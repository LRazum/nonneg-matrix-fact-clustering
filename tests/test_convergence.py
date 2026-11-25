import json
import tempfile
import unittest
from pathlib import Path

import numpy as np
from numpy.testing import assert_array_equal

from experiments.convergence import (
    FIGURES, SHIFTED_TRACKS, masked_start, max_relative_increase, publish, run_setting,
    stopping_iteration, training_sample,
)
from gitara.data import Track
from gitara.nmf import fit


class HistoryTests(unittest.TestCase):
    def test_max_relative_increase(self) -> None:
        self.assertEqual(max_relative_increase([10, 8, 9, 9]), 0.125)
        self.assertEqual(max_relative_increase([3, 2, 1]), 0.0)
        self.assertEqual(max_relative_increase([5]), 0.0)
        self.assertEqual(max_relative_increase([0, 0]), 0.0)

    def test_one_tol_zero_history_predicts_where_fit_stops(self) -> None:
        rng = np.random.default_rng(5)
        A, W0, H0 = rng.random((6, 5)), rng.uniform(0.5, 1.5, (6, 2)), rng.uniform(0.5, 1.5, (2, 5))
        for objective in ("kl", "frobenius"):
            full = fit([A], W0, [H0], objective=objective, tol=0, max_iter=300)
            for tol in (1e-2, 1e-3, 1e-4, 1e-12):
                stopped = fit([A], W0, [H0], objective=objective, tol=tol, max_iter=300)
                t = stopping_iteration(full.objective, tol)
                if t is None:
                    self.assertEqual(stopped.stop_reason, "max_iter")
                else:
                    self.assertEqual(stopped.n_iter, t)
                    self.assertEqual(stopped.objective, full.objective[: t + 1])


class SetupTests(unittest.TestCase):
    def test_masked_start_marks_unlabelled_pitches_inactive(self) -> None:
        rolls = [
            np.array([[1, 0], [0, 0], [0, 1]], dtype=bool),
            np.array([[0, 1, 1], [0, 0, 0], [0, 0, 0]], dtype=bool),
        ]
        W0, H0s = masked_start(rolls, 4, np.random.default_rng(0))
        self.assertEqual(W0.shape, (4, 4))
        assert_array_equal(W0[:, 1], 0)
        self.assertTrue(np.all((W0[:, [0, 2, 3]] >= 0.5) & (W0[:, [0, 2, 3]] <= 1.5)))
        assert_array_equal(H0s[0], [[1, 0], [0, 0], [0, 1], [1, 1]])
        assert_array_equal(H0s[1][3], [1, 1, 1])

        blocks = [np.random.default_rng(1).random((4, H.shape[1])) for H in H0s]
        result = fit(blocks, W0, H0s, max_iter=20)
        self.assertEqual(result.inactive, (1,))
        for H, H0 in zip(result.Hs, H0s):
            assert_array_equal(H[H0 == 0], 0)
            self.assertTrue(np.all(H[3] > 0))

    def test_training_sample_skips_held_out_player_and_shifted_tracks(self) -> None:
        tracks = []
        for player in range(6):
            for mode in ("comp", "solo"):
                ids = [f"0{player}_Rock{i}-100-A_{mode}" for i in range(1, 4)]
                if (player, mode) == (4, "comp"):
                    ids = [*SHIFTED_TRACKS, ids[0]]
                tracks += [Track(i, player, mode, Path(i), Path(i)) for i in ids]
        for seed in range(5):
            sample = training_sample(tracks, 5, 1, np.random.default_rng(seed))
            self.assertEqual(sorted((t.player, t.mode) for t in sample),
                             [(p, m) for p in range(5) for m in ("comp", "solo")])
            self.assertIn("04_Rock1-100-A_comp", [t.track_id for t in sample])


class RunSettingTests(unittest.TestCase):
    def test_numerical_failure_is_returned(self) -> None:
        summary = run_setting([[[1.0]]], [[0.0]], [[[1.0]]], objective="kl", eps=0, max_iter=5)
        self.assertEqual(summary["status"], "failed")
        self.assertIn("KL reconstruction is zero", summary["error"])

    def test_summary_of_a_full_run(self) -> None:
        rng = np.random.default_rng(2)
        A, W0, H0 = rng.random((5, 4)), rng.uniform(0.5, 1.5, (5, 2)), rng.uniform(0.5, 1.5, (2, 4))
        summary = run_setting([A], W0, [H0], objective="kl", eps=1e-12, max_iter=50)
        self.assertEqual((summary["status"], summary["n_iter"]), ("ok", 50))
        self.assertEqual(len(summary["history"]), 51)
        self.assertEqual(summary["final"], summary["history"][-1])
        for tol, t in summary["stop_at"].items():
            self.assertEqual(t, stopping_iteration(summary["history"], float(tol)))
            if t is not None:
                self.assertGreaterEqual(summary["gap_at_stop"][tol], 0)


class PublishTests(unittest.TestCase):
    def test_published_record_has_no_local_paths_and_dirty_runs_are_refused(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            run_dir, out_dir = Path(directory, "run"), Path(directory, "out")
            run_dir.mkdir()
            for name in FIGURES:
                (run_dir / name).write_bytes(b"png")
            record = {
                "id": "x", "dir": str(run_dir), "status": "ok", "git": {"dirty": False},
                "command": ["/home/someone/.venv/bin/python", "-m", "experiments.convergence"],
            }
            (run_dir / "run.json").write_text(json.dumps(record), encoding="utf-8")
            publish(run_dir, out_dir)
            summary = json.loads((out_dir / "summary.json").read_text(encoding="utf-8"))
            self.assertNotIn("dir", summary)
            self.assertEqual(summary["command"], ["python", "-m", "experiments.convergence"])
            self.assertNotIn("someone", (out_dir / "summary.json").read_text(encoding="utf-8"))
            self.assertEqual(sorted(p.name for p in out_dir.iterdir()), sorted([*FIGURES, "summary.json"]))

            record["git"]["dirty"] = True
            (run_dir / "run.json").write_text(json.dumps(record), encoding="utf-8")
            with self.assertRaises(ValueError):
                publish(run_dir, Path(directory, "other"))


if __name__ == "__main__":
    unittest.main()
