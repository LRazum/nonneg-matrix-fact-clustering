import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from gitara import provenance
from gitara.provenance import finish_run, start_run


def git(cwd: Path, *args: str) -> str:
    return subprocess.run(
        ["git", "-c", "user.name=Test", "-c", "user.email=test@example.com",
         "-c", "commit.gpgsign=false", *args],
        cwd=cwd, check=True, capture_output=True, text=True,
    ).stdout


class ProvenanceTests(unittest.TestCase):
    def setUp(self) -> None:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.repo = Path(temporary.name, "repo")
        (self.repo / "src").mkdir(parents=True)
        (self.repo / ".gitignore").write_text("/results/runs/\n")
        (self.repo / "src" / "model.py").write_text("RANK = 2\n")
        git(self.repo, "init", "-q")
        git(self.repo, "add", ".")
        git(self.repo, "commit", "-q", "--no-verify", "-m", "start")
        self.commit = git(self.repo, "rev-parse", "HEAD").strip()

    def read_record(self, record: dict) -> dict:
        return json.loads(Path(record["dir"], "run.json").read_text(encoding="utf-8"))

    def test_clean_run_from_subdirectory(self) -> None:
        config = {"objective": "kl", "max_iter": 200, "tol": 1e-4}
        record = start_run("fit", config, seeds=[0, 7], root=self.repo / "src")

        run_dir = Path(record["dir"])
        self.assertEqual(run_dir.parent, self.repo.resolve() / "results" / "runs")
        self.assertRegex(record["id"], r"^\d{8}T\d{6}Z-fit-[0-9a-f]{6}$")
        self.assertEqual(run_dir.name, record["id"])
        self.assertEqual(self.read_record(record), record)
        self.assertEqual(record["status"], "running")
        self.assertEqual(record["config"], config)
        self.assertEqual(record["seeds"], [0, 7])
        self.assertIsNone(record["data_manifest"])
        self.assertEqual(record["git"], {"commit": self.commit, "dirty": False, "diff": None})
        self.assertFalse((run_dir / "uncommitted.diff").exists())
        environment = record["environment"]
        self.assertEqual(
            set(environment["threads"]),
            {"OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS", "MKL_NUM_THREADS"},
        )
        self.assertIn("numpy", {name.lower() for name in environment["packages"]})

    def test_uncommitted_changes_are_saved_as_an_applicable_patch(self) -> None:
        (self.repo / "src" / "model.py").write_text("RANK = 3\n")
        (self.repo / "src" / "new.py").write_text("SEED = 5\n")
        (self.repo / "src" / "empty.py").write_text("")

        record = start_run("fit", {}, seeds=[], root=self.repo)

        self.assertEqual(record["git"], {
            "commit": self.commit, "dirty": True, "diff": "uncommitted.diff",
        })
        clone = self.repo.parent / "clone"
        git(self.repo.parent, "clone", "-q", str(self.repo), str(clone))
        git(clone, "checkout", "-q", record["git"]["commit"])
        git(clone, "apply", str(Path(record["dir"], "uncommitted.diff")))
        for name in ("model.py", "new.py", "empty.py"):
            with self.subTest(name=name):
                self.assertEqual(
                    (clone / "src" / name).read_bytes(), (self.repo / "src" / name).read_bytes(),
                )

    def test_existing_run_directory_is_never_overwritten(self) -> None:
        with mock.patch.object(provenance, "_run_id", return_value="same-id"):
            first = start_run("fit", {"rank": 1}, seeds=[0], root=self.repo)
            with self.assertRaises(FileExistsError):
                start_run("fit", {"rank": 2}, seeds=[1], root=self.repo)
        self.assertEqual(self.read_record(first)["config"], {"rank": 1})

    def test_finished_run_is_never_rewritten(self) -> None:
        record = start_run("fit", {}, seeds=[0], root=self.repo)
        run_dir = finish_run(record, "ok", {"f1": 0.5})

        self.assertEqual(run_dir, Path(record["dir"]))
        final = self.read_record(record)
        self.assertEqual((final["status"], final["results"], final["errors"]), ("ok", {"f1": 0.5}, []))
        with self.assertRaises(FileExistsError):
            finish_run(record, "failed", errors=["late"])
        self.assertEqual(self.read_record(record), final)

    def test_failed_run_is_recorded_with_its_error(self) -> None:
        record = start_run("fit", {}, seeds=[0], root=self.repo)
        with self.assertRaises(ValueError):
            finish_run(record, "failed")

        finish_run(record, "failed", errors=["ValueError('NaN in A')"])
        final = self.read_record(record)
        self.assertEqual(final["status"], "failed")
        self.assertEqual(final["errors"], ["ValueError('NaN in A')"])
        self.assertIsNone(final["results"])
        self.assertIn("finished", final)

    def test_manifest_md5(self) -> None:
        manifest = self.repo / "manifest.csv"
        manifest.write_bytes(b"abc")
        record = start_run("fit", {}, seeds=[], manifest=manifest, root=self.repo)
        # MD5 test vector from RFC 1321.
        self.assertEqual(record["data_manifest"]["md5"], "900150983cd24fb0d6963f7d28e17f72")
        with self.assertRaises(FileNotFoundError):
            start_run("fit", {}, seeds=[], manifest=self.repo / "missing.csv", root=self.repo)

    def test_invalid_inputs_create_no_run(self) -> None:
        cases = {
            "name with slash": lambda: start_run("a/b", {}, seeds=[], root=self.repo),
            "name with dots": lambda: start_run("..", {}, seeds=[], root=self.repo),
            "config": lambda: start_run("fit", {"x": object()}, seeds=[], root=self.repo),
            "float seed": lambda: start_run("fit", {}, seeds=[1.0], root=self.repo),
            "bool seed": lambda: start_run("fit", {}, seeds=[True], root=self.repo),
            "string seeds": lambda: start_run("fit", {}, seeds="12", root=self.repo),
        }
        for label, call in cases.items():
            with self.subTest(label), self.assertRaises(ValueError):
                call()
        self.assertFalse((self.repo / "results").exists())

        record = start_run("fit", {}, seeds=[], root=self.repo)
        for status, errors in (("done", ()), ("ok", "boom"), ("failed", [1])):
            with self.subTest(status=status, errors=errors), self.assertRaises(ValueError):
                finish_run(record, status, errors=errors)
        with self.assertRaises(ValueError):
            finish_run(record, "ok", {"x": object()})
        self.assertEqual(self.read_record(record)["status"], "running")

    def test_outside_git_work_tree_fails(self) -> None:
        outside = self.repo.parent / "plain"
        outside.mkdir()
        ceiling = {"GIT_CEILING_DIRECTORIES": str(self.repo.parent)}
        with mock.patch.dict("os.environ", ceiling), self.assertRaises(RuntimeError):
            start_run("fit", {}, seeds=[], root=outside)
        self.assertFalse((outside / "results").exists())


if __name__ == "__main__":
    unittest.main()
