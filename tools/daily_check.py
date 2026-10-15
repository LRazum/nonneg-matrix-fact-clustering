#!/usr/bin/env python3
"""Daily repository check, without AI. Keeps at most one open GitHub issue about it.

It looks at the last completed CI run on `main`, at every open pull request, and at what
reached `main` in the last 48 hours without an approval or without a pull request. When
something is wrong it opens one issue, or updates the one that is already open; when
everything passes it closes that issue. Runs from .github/workflows/daily-check.yml and
needs the `gh` CLI with a token. See docs/plan/AI_REVIEW.md.

Usage:
    python3 tools/daily_check.py              act on GitHub
    python3 tools/daily_check.py --dry-run    only print what it would do

Dry-run still needs read access to GitHub. GH_REPO overrides the repository default.
Non-bot, non-author reviews are checked; membership in the three-person team is not.
An approval without a submission timestamp is not proof of a pre-merge approval.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path

ISSUE_TITLE = "Daily check: main or open pull requests need attention"
DEFAULT_REPOSITORY = "LRazum/nonneg-matrix-fact-clustering"
CI_WORKFLOW = "ci.yml"
STALE_AFTER_DAYS = 3
# Captured setup baseline; the pre-workflow initialization is not audited retroactively.
APPROVAL_REQUIRED_FROM = datetime(2026, 10, 15, 21, 19, 49, tzinfo=timezone.utc)
# Longer than a day, so a delayed or skipped scheduled run does not lose a merge.
LOOKBACK_HOURS = 48
SEVERITY_LABELS = ("severity:high", "severity:medium", "severity:low")
BASE_LABELS = ("finding", "source:daily-check")


@dataclass(frozen=True)
class Problem:
    severity: str  # "high", "medium" or "low"
    pr: str
    file: str
    problem: str
    how_it_shows: str
    proposal: str


def parse_time(text: str) -> datetime:
    return datetime.fromisoformat(text.replace("Z", "+00:00"))


def ci_problems(runs: list[dict] | None) -> list[Problem]:
    """`runs` is the last completed CI run on main, or None when the workflow is missing."""
    if runs is None:
        return [
            Problem(
                "high",
                "none",
                f".github/workflows/{CI_WORKFLOW}",
                "The CI workflow was not found on `main`.",
                f"`gh run list --workflow {CI_WORKFLOW} --branch main` fails.",
                "Check that the workflow file exists on `main` and is enabled.",
            )
        ]
    if not runs:
        return [
            Problem(
                "high",
                "none",
                f".github/workflows/{CI_WORKFLOW}",
                "There is no completed CI run on `main`.",
                f"`gh run list --workflow {CI_WORKFLOW} --branch main --status completed` is empty.",
                "Run CI on `main` (push or workflow_dispatch) and look at the result.",
            )
        ]
    run = runs[0]
    if run.get("conclusion") == "success":
        return []
    return [
        Problem(
            "high",
            "none",
            f".github/workflows/{CI_WORKFLOW}",
            f"The last CI run on `main` ended with `{run.get('conclusion')}`.",
            f"{run.get('url', '?')} (commit {str(run.get('headSha', '?'))[:12]})",
            "Fix `main` in a new branch before other work; see the failing job log.",
        )
    ]


def pr_problems(prs: list[dict], now: datetime) -> list[Problem]:
    problems = []
    for pr in sorted(prs, key=lambda p: p["number"]):
        ref = f"#{pr['number']} ({pr.get('headRefName', '?')})"
        if pr.get("mergeable") == "CONFLICTING":
            problems.append(
                Problem(
                    "medium",
                    ref,
                    "n/a",
                    f"Pull request #{pr['number']} has a merge conflict with its base.",
                    f"{pr.get('url', '?')} shows mergeable = CONFLICTING.",
                    "The owner of the branch merges the base into it and resolves the conflict "
                    "(no rebase, no force push).",
                )
            )
        elif pr.get("mergeable") != "MERGEABLE":
            problems.append(
                Problem(
                    "medium",
                    ref,
                    "n/a",
                    f"Pull request #{pr['number']} has unverified mergeability.",
                    f"{pr.get('url', '?')} reports mergeable = {pr.get('mergeable', 'missing')}.",
                    "Retry the GitHub check after mergeability has been computed; verify the "
                    "base before merging. This result does not establish a merge conflict.",
                )
            )
        updated = parse_time(pr["updatedAt"])
        age = now - updated
        if age > timedelta(days=STALE_AFTER_DAYS):
            problems.append(
                Problem(
                    "medium",
                    ref,
                    "n/a",
                    f"Pull request #{pr['number']} has not changed for {age.days} days.",
                    f"{pr.get('url', '?')} was last updated {updated:%Y-%m-%d %H:%M} UTC.",
                    "Review it, finish it, or close it with a reason.",
                )
            )
    return problems


def window_start(now: datetime) -> datetime:
    return max(now - timedelta(hours=LOOKBACK_HOURS), APPROVAL_REQUIRED_FROM)


def unapproved_merge_problems(prs: list[dict], now: datetime) -> list[Problem]:
    """`prs` are PRs merged into main, with their author, merge time and reviews."""
    since = window_start(now)
    problems = []
    for pr in sorted(prs, key=lambda p: p["number"]):
        merged_at = parse_time(pr["mergedAt"])
        if merged_at < since:
            continue
        # Lovro explicitly authorized this setup's commit/push/PR/merge on 2026-10-15.
        # This one-off exception waives review only; it does not assert a human approval.
        if (pr["number"], pr.get("headRefName")) == (1, "codex/seminar-workflow"):
            continue
        author = (pr.get("author") or {}).get("login")
        if author and human_approvers(pr) - {str(author).lower()}:
            continue
        merged_by = (pr.get("mergedBy") or {}).get("login", "?")
        problems.append(
            Problem(
                "medium",
                f"#{pr['number']} ({pr.get('headRefName', '?')})",
                "n/a",
                f"Pull request #{pr['number']} was merged into `main` without a verifiable approving "
                "review by another human reviewer.",
                f"{pr.get('url', '?')} was merged {merged_at:%Y-%m-%d %H:%M} UTC by {merged_by}.",
                "A different team member reviews the merged change now; anything wrong goes "
                "into a new PR. Future PRs need approval before merging.",
            )
        )
    return problems


def human_approvers(pr: dict) -> set[str]:
    """Verifiable effective non-bot approvals; team membership is checked by participants."""
    states = {}
    undated = set()
    merged_at = parse_time(pr["mergedAt"])
    for review in pr.get("reviews", []):
        author = review.get("author") or {}
        login = str(author.get("login", "")).lower()
        if (
            not login or login.endswith("[bot]") or author.get("is_bot")
            or author.get("type") == "Bot"
        ):
            continue
        state = review.get("state")
        if state not in {"APPROVED", "CHANGES_REQUESTED", "DISMISSED"}:
            continue
        if not review.get("submittedAt"):
            undated.add(login)
            continue
        submitted_at = parse_time(review["submittedAt"])
        if submitted_at > merged_at:
            continue
        if login not in states or submitted_at >= states[login][0]:
            states[login] = (submitted_at, state)
    return {login for login, (_, state) in states.items() if state == "APPROVED"} - undated


def direct_push_problems(commits: list[dict], now: datetime) -> list[Problem]:
    """`commits` are commits on main: sha, date, url and the numbers of their PRs."""
    since = window_start(now)
    problems = []
    for commit in commits:
        committed_at = parse_time(commit["date"])
        if committed_at < since or commit["prs"]:
            continue
        problems.append(
            Problem(
                "medium",
                "none",
                "n/a",
                f"Commit {commit['sha'][:12]} reached `main` without a pull request.",
                f"{commit.get('url', '?')}, committed {committed_at:%Y-%m-%d %H:%M} UTC.",
                "A different team member reviews the commit; later changes go through a PR.",
            )
        )
    return problems


def overall_severity(problems: list[Problem]) -> str:
    order = {"high": 0, "medium": 1, "low": 2}
    return "severity:" + min((p.severity for p in problems), key=order.__getitem__)


def render_body(problems: list[Problem], now: datetime) -> str:
    lines = [
        f"Opened and updated by `tools/daily_check.py` (last run {now:%Y-%m-%d %H:%M} UTC).",
        "It closes this issue by itself when every check passes.",
        "Review checks exclude bots and the PR author; team membership still needs human verification.",
        "",
    ]
    for number, p in enumerate(problems, start=1):
        lines += [
            f"### {number}. {p.problem}",
            "",
            f"- **PR:** {p.pr}",
            f"- **File:** {p.file}",
            f"- **Problem:** {p.problem}",
            f"- **How it shows:** {p.how_it_shows}",
            f"- **Proposal:** {p.proposal}",
            f"- **Severity:** {p.severity}",
            "",
        ]
    return "\n".join(lines)


def gh(*args: str) -> str:
    env = os.environ.copy()
    env.setdefault("GH_REPO", DEFAULT_REPOSITORY)
    return subprocess.run(
        ["gh", *args], check=True, capture_output=True, text=True, env=env
    ).stdout


def fetch_ci_runs() -> list[dict] | None:
    try:
        out = gh(
            "run", "list", "--workflow", CI_WORKFLOW, "--branch", "main", "--status",
            "completed", "--limit", "1", "--json", "conclusion,url,headSha,createdAt",
        )
    except subprocess.CalledProcessError as error:
        stderr = (error.stderr or "").lower()
        if "could not find" in stderr or "http 404" in stderr:
            return None
        raise
    return json.loads(out)


def fetch_prs() -> list[dict]:
    out = gh(
        "pr", "list", "--state", "open", "--limit", "200", "--json",
        "number,url,mergeable,updatedAt,headRefName",
    )
    return json.loads(out)


def fetch_merged_prs(since: datetime) -> list[dict]:
    out = gh(
        "pr", "list", "--state", "merged", "--base", "main", "--search",
        f"merged:>={since:%Y-%m-%d}", "--limit", "200", "--json",
        "number,url,author,mergedAt,mergedBy,reviews,headRefName",
    )
    return json.loads(out)


def fetch_main_commits(since: datetime) -> list[dict]:
    out = gh(
        "api", f"repos/{{owner}}/{{repo}}/commits?sha=main&per_page=100"
        f"&since={since:%Y-%m-%dT%H:%M:%SZ}",
    )
    commits = []
    for item in json.loads(out):
        pulls = json.loads(gh("api", f"repos/{{owner}}/{{repo}}/commits/{item['sha']}/pulls"))
        commits.append(
            {
                "sha": item["sha"],
                "date": item["commit"]["committer"]["date"],
                "url": item.get("html_url", "?"),
                "prs": [pull["number"] for pull in pulls
                        if pull.get("merged_at") and pull.get("base", {}).get("ref") == "main"],
            }
        )
    return commits


def fetch_open_issue() -> dict | None:
    out = gh(
        "issue", "list", "--state", "open", "--limit", "100", "--search", f'"{ISSUE_TITLE}" in:title',
        "--json", "number,title,labels",
    )
    matches = [i for i in json.loads(out) if i["title"] == ISSUE_TITLE]
    return min(matches, key=lambda i: i["number"]) if matches else None


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--dry-run", action="store_true", help="print actions, change nothing")
    args = parser.parse_args(argv)

    now = datetime.now(timezone.utc)
    problems = ci_problems(fetch_ci_runs()) + pr_problems(fetch_prs(), now)
    since = window_start(now)
    if since < now:
        problems += unapproved_merge_problems(fetch_merged_prs(since), now)
        problems += direct_push_problems(fetch_main_commits(since), now)
    issue = fetch_open_issue()

    def act(*command: str, body: str | None = None) -> None:
        preview = (*command, "--body-file", "<temporary-body.md>") if body is not None else command
        print("gh " + " ".join(preview))
        if args.dry_run:
            return
        if body is None:
            gh(*command)
        else:
            with tempfile.TemporaryDirectory(prefix="nmf-daily-check-") as temporary:
                path = Path(temporary) / "body.md"
                path.write_text(body, encoding="utf-8")
                gh(*command, "--body-file", str(path))

    if problems:
        body = render_body(problems, now)
        severity = overall_severity(problems)
        print(f"{len(problems)} problem(s) found:\n\n{body}")
        if issue is None:
            labels = [x for label in (*BASE_LABELS, severity) for x in ("--label", label)]
            act("issue", "create", "--title", ISSUE_TITLE, *labels, body=body)
        else:
            current = {label["name"] for label in issue.get("labels", [])}
            stale = [x for label in SEVERITY_LABELS if label in current and label != severity
                     for x in ("--remove-label", label)]
            labels = [x for label in (*BASE_LABELS, severity) for x in ("--add-label", label)]
            act("issue", "edit", str(issue["number"]), *labels, *stale, body=body)
        return 0
    print("All checks pass.")
    if issue is not None:
        act(
            "issue", "close", str(issue["number"]), "--comment",
            f"All checks pass ({now:%Y-%m-%d %H:%M} UTC). Closed by `tools/daily_check.py`.",
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
