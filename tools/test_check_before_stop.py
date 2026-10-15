"""The shared check runner must never present an unconfigured project suite as a pass."""
from __future__ import annotations

import contextlib
import io
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import check_before_stop as checks


class CheckBeforeStopTests(unittest.TestCase):
    def run_checks(self, root: Path, *, stdout: str = "", stderr: str = "", code: int = 0, hook: bool = True) -> tuple[int, str, str]:
        output, errors = io.StringIO(), io.StringIO()
        completed = subprocess.CompletedProcess(["check"], code, stdout, stderr)
        with (
            patch.object(checks, "ROOT", root),
            patch.object(checks, "steps", return_value=[("fixture check", ["check"], root)]),
            patch.object(checks.subprocess, "run", return_value=completed),
            contextlib.redirect_stdout(output), contextlib.redirect_stderr(errors),
        ):
            status = checks.main(["--hook"] if hook else [])
        return status, output.getvalue(), errors.getvalue()

    def test_undecided_stack_is_explicitly_not_run_in_cli_and_hook(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            status, output, errors = self.run_checks(root)
            self.assertEqual((status, errors), (0, ""))
            self.assertIn("project checks NOT RUN: no pyproject.toml", json.loads(output)["systemMessage"])
            status, output, errors = self.run_checks(root, hook=False)
            self.assertEqual((status, errors), (0, ""))
            self.assertIn("PASS: fixture check", output)
            self.assertIn("project checks NOT RUN", output)

    def test_adding_pyproject_requires_an_explicit_project_runner(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "pyproject.toml").write_text("", encoding="utf-8")
            status, output, errors = self.run_checks(root)
            self.assertEqual((status, output), (2, ""))
            self.assertIn("tools/check_project.py is missing", errors)

    def test_project_checks_only_join_the_steps_when_both_files_exist(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "tools").mkdir()
            (root / "tools/check_project.py").write_text("", encoding="utf-8")
            with patch.object(checks, "ROOT", root):
                self.assertEqual(len(checks.steps()), 2)
                (root / "pyproject.toml").write_text("", encoding="utf-8")
                project = checks.steps()[2]
            self.assertEqual(project, ("project checks", [sys.executable, "tools/check_project.py"], root))

    def test_hook_success_is_json_even_when_there_are_no_not_run_messages(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "tools").mkdir()
            (root / "pyproject.toml").touch()
            (root / "tools/check_project.py").touch()
            self.assertEqual(self.run_checks(root, stdout="tests passed"), (0, "{}\n", ""))

    def test_a_failure_blocks_finishing_and_keeps_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            status, output, errors = self.run_checks(Path(temporary), stdout="real failure", code=1)
            self.assertEqual((status, output), (2, ""))
            self.assertIn("fixture check failed (exit 1)", errors)
            self.assertIn("real failure", errors)
            self.assertIn("project checks NOT RUN", errors)

    def test_only_structured_pytest_skip_reasons_are_reported(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            captured = "NOT RUN: captured example\nSKIPPED [1] test.py:3: intentionally omitted\n"
            self.assertNotIn("captured example", self.run_checks(root, stdout=captured)[1])
            reports = "SKIPPED [2] test.py:3: NOT RUN: data missing\nSKIPPED [1] other.py:4: NOT RUN: data missing\n"
            output = self.run_checks(root, stderr=reports)[1]
            self.assertEqual(json.loads(output)["systemMessage"].count("data missing"), 1)

    def test_missing_process_and_timeout_are_failures(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            for error in (FileNotFoundError("missing Python"), subprocess.TimeoutExpired("check", 1)):
                with (
                    patch.object(checks, "ROOT", Path(temporary)),
                    patch.object(checks, "steps", return_value=[("fixture check", ["check"], Path(temporary))]),
                    patch.object(checks.subprocess, "run", side_effect=error),
                    contextlib.redirect_stderr(io.StringIO()) as errors,
                ):
                    self.assertEqual(checks.main(["--hook"]), 2)
                    self.assertIn("could not complete", errors.getvalue())

    def test_tail_limits_failure_output(self) -> None:
        rendered = checks.tail("\n".join(str(i) for i in range(205)))
        self.assertTrue(rendered.startswith("... (5 earlier lines cut)\n5\n"))
        self.assertTrue(rendered.endswith("204"))

    def test_hook_protocol_across_a_real_subprocess_from_another_directory(self) -> None:
        script = (
            "import pathlib, sys;"
            f"sys.path.insert(0, {str(checks.ROOT / 'tools')!r});"
            "import check_before_stop as checks;"
            "checks.ROOT = pathlib.Path.cwd();"
            "checks.steps = lambda: [('fixture', [sys.executable, '-c', "
            "\"print('SKIPPED [1] test.py:2: NOT RUN: fixture unavailable')\"], checks.ROOT)];"
            "raise SystemExit(checks.main(['--hook']))"
        )
        with tempfile.TemporaryDirectory() as temporary:
            result = subprocess.run(
                [sys.executable, "-c", script], cwd=temporary, input="{}",
                capture_output=True, text=True, timeout=30,
            )
        self.assertEqual((result.returncode, result.stderr), (0, ""))
        self.assertIn("fixture unavailable", json.loads(result.stdout)["systemMessage"])


if __name__ == "__main__":
    unittest.main()
