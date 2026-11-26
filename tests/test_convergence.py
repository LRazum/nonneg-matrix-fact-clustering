import json
import tempfile
import unittest
from pathlib import Path

import numpy as np
from numpy.testing import assert_array_equal

from experiments.convergence import (
    EPS_VALUES, FIGURES, SHIFTED_TRACKS, eps_histories_identical, masked_start,
    max_relative_increase, publish, run_setting, stopping_iteration, subnormal_entries, time_iteration,
    time_objective,
    training_sample, transcription_start,
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
    def test_transcription_keeps_templates_and_inactive_rows(self) -> None:
        rng = np.random.default_rng(3)
        W = rng.uniform(0.5, 1.5, (5, 3))
        W[:, 1] = 0
        W0, (H0,) = transcription_start(W, 4)
        assert_array_equal(H0, [[1] * 4, [0] * 4, [1] * 4])
        summary = run_setting([rng.random((5, 4))], W0, [H0], objective="kl", eps=1e-12,
                              max_iter=30, update_W=False)
        assert_array_equal(summary["W"], W)
        self.assertEqual(summary["inactive"], [1])
        self.assertEqual(summary["max_relative_increase"], 0.0)

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
        self.assertGreater(summary["objective_seconds"], 0)
        self.assertAlmostEqual(summary["objective_share"],
                               summary["objective_seconds"] / summary["iteration_seconds"])
        self.assertEqual(summary["subnormal_entries"], {"W": 0, "H": 0})

    def test_time_objective_is_positive_for_both_objectives_and_blocks(self) -> None:
        rng = np.random.default_rng(4)
        blocks = [rng.random((5, 4)), rng.random((5, 3))]
        W, Hs = rng.uniform(0.5, 1.5, (5, 2)), [rng.uniform(0.5, 1.5, (2, 4)), rng.uniform(0.5, 1.5, (2, 3))]
        for objective in ("kl", "frobenius"):
            seconds = time_objective(blocks, W, Hs, objective, repeats=3)
            self.assertTrue(np.isfinite(seconds) and seconds > 0)

    def test_time_iteration_does_not_change_the_factors(self) -> None:
        rng = np.random.default_rng(5)
        blocks = [rng.random((5, 4))]
        W, Hs = rng.uniform(0.5, 1.5, (5, 2)), [rng.uniform(0.5, 1.5, (2, 4))]
        before = W.copy(), Hs[0].copy()
        for update_W in (True, False):
            seconds = time_iteration(blocks, W, Hs, objective="kl", eps=1e-12, update_W=update_W, repeats=3)
            self.assertTrue(np.isfinite(seconds) and seconds > 0)
        assert_array_equal(W, before[0])
        assert_array_equal(Hs[0], before[1])

    def test_subnormal_entries(self) -> None:
        tiny = np.finfo(np.float64).tiny
        X = np.array([[0.0, tiny, tiny / 2], [-tiny / 4, 5e-324, 1.0]])
        self.assertEqual(subnormal_entries(X), 3)

    def test_eps_histories_identical(self) -> None:
        def run(objective, seed, eps, history, status="ok"):
            return {"objective": objective, "seed": seed, "eps": eps, "status": status, "history": history}

        same = [run("kl", 0, eps, [3.0, 2.0, 1.5]) for eps in EPS_VALUES]
        # The largest eps changes the last value by one unit in the last place.
        last = {eps: 1.5 for eps in EPS_VALUES} | {max(EPS_VALUES): float(np.nextafter(1.5, 2.0))}
        differ = [run("kl", 1, eps, [3.0, 2.0, last[eps]]) for eps in EPS_VALUES]
        failed = [run("frobenius", 0, eps, [2.0, 1.0]) for eps in EPS_VALUES[:-1]]
        failed.append(run("frobenius", 0, EPS_VALUES[-1], None, status="failed"))
        self.assertEqual(eps_histories_identical(same + differ + failed),
                         {"kl seed=0": True, "kl seed=1": False, "frobenius seed=0": False})


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
