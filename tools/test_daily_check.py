"""Daily-check regression tests use fixtures only; they never contact GitHub."""
from __future__ import annotations

import contextlib
import io
import json
import subprocess
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch

import daily_check as daily

NOW = datetime(2026, 10, 18, 7, 0, tzinfo=timezone.utc)


def pr(number: int, updated: str, mergeable: str = "MERGEABLE") -> dict:
    return {
        "number": number, "url": f"https://example.invalid/pull/{number}",
        "mergeable": mergeable, "updatedAt": updated, "headRefName": f"codex/topic-{number}",
    }


def review(login: str, state: str = "APPROVED", at: str = "2026-10-17T10:00:00Z") -> dict:
    return {"author": {"login": login}, "state": state, "submittedAt": at}


def merged(number: int, reviews: list[dict], at: str = "2026-10-17T12:00:00Z") -> dict:
    return {
        "number": number, "url": f"https://example.invalid/pull/{number}",
        "headRefName": f"codex/topic-{number}", "author": {"login": "author"},
        "mergedAt": at, "mergedBy": {"login": "author"}, "reviews": reviews,
    }


class FindingsTests(unittest.TestCase):
    def test_ci_success_failure_and_missing_runs(self) -> None:
        self.assertEqual(daily.ci_problems([{"conclusion": "success"}]), [])
        for runs in ([{"conclusion": "failure", "url": "u", "headSha": "abc"}], [], None):
            self.assertEqual([p.severity for p in daily.ci_problems(runs)], ["high"])

    def test_conflicting_and_stale_prs(self) -> None:
        prs = [
            pr(1, "2026-10-17T10:00:00Z"),
            pr(2, "2026-10-17T10:00:00Z", "CONFLICTING"),
            pr(3, "2026-10-14T06:00:00Z"),
            pr(4, "2026-10-15T08:00:00Z", "UNKNOWN"),
        ]
        self.assertEqual([p.pr.split()[0] for p in daily.pr_problems(prs, NOW)], ["#2", "#3", "#4"])

    def test_unknown_or_missing_mergeability_requires_recheck_without_claiming_conflict(self) -> None:
        for value in ("UNKNOWN", None):
            item = pr(4, "2026-10-17T10:00:00Z", value)
            if value is None:
                del item["mergeable"]
            problems = daily.pr_problems([item], NOW)
            self.assertEqual(len(problems), 1)
            self.assertEqual(problems[0].severity, "medium")
            self.assertIn("mogućnost spajanja nije provjerena", problems[0].problem)
            self.assertNotIn("konflikt", problems[0].problem)
            self.assertIn("Ponovi", problems[0].proposal)

    def test_48_hour_window_does_not_precede_workflow_adoption(self) -> None:
        self.assertEqual(daily.window_start(NOW), datetime(2026, 10, 16, 7, tzinfo=timezone.utc))
        self.assertEqual(
            daily.window_start(datetime(2026, 10, 15, 12, tzinfo=timezone.utc)),
            daily.APPROVAL_REQUIRED_FROM,
        )

    def test_merge_requires_another_human_approval_before_merging(self) -> None:
        bot = review("service-account")
        bot["author"]["is_bot"] = True
        prs = [
            merged(1, [review("sara")]),
            merged(2, [review("AUTHOR")]),
            merged(3, [review("github-actions[bot]"), bot]),
            merged(4, [review("sara", at="2026-10-17T13:00:00Z")]),
            merged(5, [], at="2026-10-16T06:59:00Z"),
        ]
        problems = daily.unapproved_merge_problems(prs, NOW)
        self.assertEqual([p.pr.split()[0] for p in problems], ["#2", "#3", "#4"])

    def test_authorized_review_exceptions_require_exact_pr_and_branch(self) -> None:
        for number, branch in (
            (1, "codex/seminar-workflow"), (2, "codex/croatian-project-docs"), (4, "lovro/ai-authorship"),
        ):
            with self.subTest(number=number, branch=branch):
                authorized = merged(number, [])
                authorized["headRefName"] = branch
                self.assertEqual(daily.unapproved_merge_problems([authorized], NOW), [])
                self.assertEqual(daily.human_approvers(authorized), set())
        for number, branch in (
            (2, "codex/seminar-workflow"), (1, "codex/another-task"),
            (3, "codex/croatian-project-docs"), (2, "codex/another-task"),
            (5, "lovro/ai-authorship"), (4, "lovro/another-task"),
        ):
            with self.subTest(number=number, branch=branch):
                other = merged(number, [])
                other["headRefName"] = branch
                self.assertEqual(len(daily.unapproved_merge_problems([other], NOW)), 1)

    def test_dismissed_or_replaced_approvals_do_not_count_but_comments_do_not_revoke(self) -> None:
        approved = review("sara")
        self.assertEqual(daily.human_approvers(merged(1, [approved, review("sara", "COMMENTED")])), {"sara"})
        for state in ("CHANGES_REQUESTED", "DISMISSED"):
            self.assertEqual(daily.human_approvers(merged(1, [approved, review("sara", state)])), set())
        self.assertEqual(
            daily.human_approvers(merged(1, [review("sara", "DISMISSED"), review("mislav")])),
            {"mislav"},
        )

    def test_latest_decisive_review_is_chosen_by_time_not_response_order(self) -> None:
        older = review("sara", "CHANGES_REQUESTED", at="2026-10-17T09:00:00Z")
        newer = review("SARA", at="2026-10-17T10:00:00Z")
        self.assertEqual(daily.human_approvers(merged(1, [newer, older])), {"sara"})

    def test_missing_review_time_or_pr_author_cannot_prove_another_premerge_approval(self) -> None:
        undated = review("sara")
        del undated["submittedAt"]
        self.assertEqual(daily.human_approvers(merged(1, [undated])), set())
        undated["state"] = "DISMISSED"
        self.assertEqual(daily.human_approvers(merged(1, [review("sara"), undated])), set())
        item = merged(1, [review("sara")])
        del item["author"]
        self.assertEqual(len(daily.unapproved_merge_problems([item], NOW)), 1)

    def test_only_commits_in_window_without_pr_are_reported(self) -> None:
        commits = [
            {"sha": "a" * 40, "date": "2026-10-17T10:00:00Z", "url": "u", "prs": []},
            {"sha": "b" * 40, "date": "2026-10-17T11:00:00Z", "url": "u", "prs": [7]},
            {"sha": "c" * 40, "date": "2026-10-16T06:59:00Z", "url": "u", "prs": []},
        ]
        problems = daily.direct_push_problems(commits, NOW)
        self.assertEqual(len(problems), 1)
        self.assertIn("a" * 12, problems[0].problem)

    def test_pre_workflow_bootstrap_is_outside_the_direct_commit_rule(self) -> None:
        baseline = daily.APPROVAL_REQUIRED_FROM
        after_setup = baseline + timedelta(seconds=1)
        commits = [
            {
                "sha": "4769154e39353c437bfc42073e6ca595a7e3f3c0",
                "date": "2026-10-15T20:50:00Z", "url": "u", "prs": [],
            },
            {"sha": "d" * 40, "date": after_setup.isoformat(), "url": "u", "prs": []},
        ]
        problems = daily.direct_push_problems(commits, after_setup)
        self.assertEqual(len(problems), 1)
        self.assertIn("d" * 12, problems[0].problem)

    def test_report_contains_the_evidence_and_highest_severity(self) -> None:
        problems = daily.ci_problems([]) + daily.pr_problems([pr(3, "2026-10-17T10:00:00Z", "CONFLICTING")], NOW)
        body = daily.render_body(problems, NOW)
        for field in ("**PR:**", "**Datoteka:**", "**Problem:**", "**Kako se očituje:**", "**Prijedlog:**"):
            self.assertEqual(body.count(field), 2)
        self.assertEqual(daily.overall_severity(problems), "severity:high")
        self.assertEqual(daily.overall_severity(problems[1:]), "severity:medium")


class GitHubBoundaryTests(unittest.TestCase):
    def test_default_repository_and_explicit_override(self) -> None:
        result = subprocess.CompletedProcess(["gh"], 0, "[]", "")
        for env, expected in (({}, daily.DEFAULT_REPOSITORY), ({"GH_REPO": "owner/other"}, "owner/other")):
            with patch.dict(daily.os.environ, env, clear=True), patch.object(daily.subprocess, "run", return_value=result) as run:
                self.assertEqual(daily.gh("issue", "list"), "[]")
                self.assertEqual(run.call_args.kwargs["env"]["GH_REPO"], expected)

    def test_issue_lookup_uses_exact_title_and_reuses_oldest_match(self) -> None:
        issues = [
            {"number": 1, "title": daily.ISSUE_TITLE + " extra"},
            {"number": 3, "title": daily.ISSUE_TITLE},
            {"number": 2, "title": daily.ISSUE_TITLE},
        ]
        with patch.object(daily, "gh", return_value=json.dumps(issues)):
            self.assertEqual(daily.fetch_open_issue()["number"], 2)

    def test_only_merged_prs_targeting_main_account_for_a_commit(self) -> None:
        commit = {"sha": "abc", "commit": {"committer": {"date": "2026-10-17T10:00:00Z"}}}
        pulls = [
            {"number": 1, "merged_at": None, "base": {"ref": "main"}},
            {"number": 2, "merged_at": "date", "base": {"ref": "other"}},
            {"number": 3, "merged_at": "date", "base": {"ref": "main"}},
        ]
        with patch.object(daily, "gh", side_effect=[json.dumps([commit]), json.dumps(pulls)]):
            self.assertEqual(daily.fetch_main_commits(NOW)[0]["prs"], [3])


class CliTests(unittest.TestCase):
    def run_cli(self, *, broken: bool, issue: dict | None, dry_run: bool = False, publish_effect=None) -> tuple[list, str]:
        output = io.StringIO()
        with (
            patch.object(daily, "fetch_ci_runs", return_value=[] if broken else [{"conclusion": "success"}]),
            patch.object(daily, "fetch_prs", return_value=[]),
            patch.object(daily, "fetch_merged_prs", return_value=[]),
            patch.object(daily, "fetch_main_commits", return_value=[]),
            patch.object(daily, "fetch_open_issue", return_value=issue),
            patch.object(daily, "gh", side_effect=publish_effect) as publish,
            contextlib.redirect_stdout(output),
        ):
            self.assertEqual(daily.main(["--dry-run"] if dry_run else []), 0)
        return publish.call_args_list, output.getvalue()

    def test_create_edit_close_and_healthy_noop_use_at_most_one_mutation(self) -> None:
        issue = {"number": 7, "labels": [{"name": "severity:medium"}]}
        for broken, existing, action in ((True, None, "create"), (True, issue, "edit"), (False, issue, "close")):
            calls, _ = self.run_cli(broken=broken, issue=existing)
            self.assertEqual(len(calls), 1)
            self.assertEqual(calls[0].args[:2], ("issue", action))
            if action == "edit":
                self.assertIn("finding", calls[0].args)
                self.assertIn("--remove-label", calls[0].args)
        self.assertEqual(self.run_cli(broken=False, issue=None)[0], [])

    def test_dry_run_prints_proposed_action_without_publishing(self) -> None:
        for broken, issue in ((True, None), (True, {"number": 7}), (False, {"number": 7})):
            calls, output = self.run_cli(broken=broken, issue=issue, dry_run=True)
            self.assertEqual(calls, [])
            self.assertIn("gh issue", output)

    def test_dry_run_read_auth_failure_is_an_error_and_cannot_publish(self) -> None:
        error = subprocess.CalledProcessError(1, ["gh", "run", "list"], stderr="HTTP 401: authentication required")
        with patch.object(daily, "gh", side_effect=error) as github:
            with self.assertRaises(subprocess.CalledProcessError):
                daily.main(["--dry-run"])
        self.assertEqual(github.call_count, 1)
        self.assertEqual(github.call_args.args[:2], ("run", "list"))

    def test_multiline_body_is_read_from_a_temporary_file_and_cleaned_up(self) -> None:
        bodies, paths = [], []

        def read_body(*command: str) -> str:
            self.assertNotIn("--body", command)
            path = Path(command[command.index("--body-file") + 1])
            paths.append(path)
            bodies.append(path.read_text(encoding="utf-8"))
            return ""

        for issue in (None, {"number": 7}):
            self.run_cli(broken=True, issue=issue, publish_effect=read_body)
        self.assertEqual(len(bodies), 2)
        for body in bodies:
            self.assertIn("\n### 1.", body)
            self.assertIn("\n- **Prijedlog:**", body)
        self.assertTrue(all(not path.exists() for path in paths))


if __name__ == "__main__":
    unittest.main()
