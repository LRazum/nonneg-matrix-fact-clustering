"""Project checks require a synchronized environment and propagate failures."""
from __future__ import annotations

import contextlib
import io
import subprocess
import unittest
from unittest.mock import patch

import check_project


class CheckProjectTests(unittest.TestCase):
    def test_missing_uv_reports_how_to_set_up_environment(self) -> None:
        errors = io.StringIO()
        with (
            patch.object(check_project.subprocess, "run", side_effect=FileNotFoundError),
            contextlib.redirect_stderr(errors),
        ):
            self.assertNotEqual(check_project.main(), 0)
        self.assertIn("uv sync --locked", errors.getvalue())

    def test_unsynchronized_environment_stops_before_running_checks(self) -> None:
        errors = io.StringIO()
        with (
            patch.object(
                check_project.subprocess, "run", return_value=subprocess.CompletedProcess([], 2),
            ) as run,
            contextlib.redirect_stderr(errors),
        ):
            self.assertEqual(check_project.main(), 2)
        run.assert_called_once_with(
            ["uv", "--no-cache", "sync", "--locked", "--check"],
            cwd=check_project.ROOT,
            check=False,
        )
        self.assertIn("uv sync --locked", errors.getvalue())

    def test_syntax_failure_stops_before_running_tests(self) -> None:
        with patch.object(
            check_project.subprocess, "run",
            side_effect=[subprocess.CompletedProcess([], 0), subprocess.CompletedProcess([], 1)],
        ) as run:
            self.assertEqual(check_project.main(), 1)
        self.assertEqual(run.call_count, 2)

    def test_test_result_is_returned(self) -> None:
        for status in (0, 5):
            with (
                self.subTest(status=status),
                patch.object(
                    check_project.subprocess, "run",
                    side_effect=[subprocess.CompletedProcess([], code) for code in (0, 0, status)],
                ) as run,
            ):
                self.assertEqual(check_project.main(), status)
                self.assertEqual(run.call_count, 3)
