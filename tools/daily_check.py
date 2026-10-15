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

ISSUE_TITLE = "Dnevna provjera: main ili otvoreni PR-ovi zahtijevaju pozornost"
DEFAULT_REPOSITORY = "LRazum/nonneg-matrix-fact-clustering"
CI_WORKFLOW = "ci.yml"
STALE_AFTER_DAYS = 3
# Captured setup baseline; the pre-workflow initialization is not audited retroactively.
APPROVAL_REQUIRED_FROM = datetime(2026, 10, 15, 21, 19, 49, tzinfo=timezone.utc)
# Longer than a day, so a delayed or skipped scheduled run does not lose a merge.
LOOKBACK_HOURS = 48
SEVERITY_LABELS = ("severity:high", "severity:medium", "severity:low")
BASE_LABELS = ("finding", "source:daily-check")
# Explicit per-PR merge instructions recorded in ADR-0002; these are not human approvals.
AUTHORIZED_REVIEW_EXCEPTIONS = frozenset({
    (1, "codex/seminar-workflow"),
    (2, "codex/croatian-project-docs"),
})


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
                "nema",
                f".github/workflows/{CI_WORKFLOW}",
                "Tijek CI provjera nije pronađen na grani `main`.",
                f"Naredba `gh run list --workflow {CI_WORKFLOW} --branch main` nije uspjela.",
                "Provjeri postoji li konfiguracija CI provjera na grani `main` i je li uključena.",
            )
        ]
    if not runs:
        return [
            Problem(
                "high",
                "nema",
                f".github/workflows/{CI_WORKFLOW}",
                "Na grani `main` nema dovršenog izvođenja CI provjera.",
                f"Naredba `gh run list --workflow {CI_WORKFLOW} --branch main --status completed` nema rezultata.",
                "Pokreni CI na grani `main` (push ili workflow_dispatch) i pregledaj rezultat.",
            )
        ]
    run = runs[0]
    if run.get("conclusion") == "success":
        return []
    return [
        Problem(
            "high",
            "nema",
            f".github/workflows/{CI_WORKFLOW}",
            f"Posljednje izvođenje CI provjera na grani `main` završilo je stanjem `{run.get('conclusion')}`.",
            f"{run.get('url', '?')} (commit {str(run.get('headSha', '?'))[:12]})",
            "Prije nastavka rada ispravi `main` kroz novu granu; pregledaj zapis neuspješnog posla.",
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
                    "nije primjenjivo",
                    f"PR #{pr['number']} ima konflikt pri spajanju s ciljnom granom.",
                    f"{pr.get('url', '?')} prikazuje mergeable = CONFLICTING.",
                    "Autor grane spaja ciljnu granu u svoju i rješava konflikt "
                    "(bez rebasea i prisilnog pusha).",
                )
            )
        elif pr.get("mergeable") != "MERGEABLE":
            problems.append(
                Problem(
                    "medium",
                    ref,
                    "nije primjenjivo",
                    f"Za PR #{pr['number']} mogućnost spajanja nije provjerena.",
                    f"{pr.get('url', '?')} prijavljuje mergeable = {pr.get('mergeable', 'nedostaje')}.",
                    "Ponovi GitHub provjeru nakon izračuna mogućnosti spajanja; provjeri ciljnu "
                    "granu prije spajanja. Ovaj nalaz ne potvrđuje postojanje konflikta.",
                )
            )
        updated = parse_time(pr["updatedAt"])
        age = now - updated
        if age > timedelta(days=STALE_AFTER_DAYS):
            problems.append(
                Problem(
                    "medium",
                    ref,
                    "nije primjenjivo",
                    f"Broj dana bez promjene na PR-u #{pr['number']}: {age.days}.",
                    f"{pr.get('url', '?')} posljednji je put ažuriran {updated:%Y-%m-%d %H:%M} UTC.",
                    "Pregledaj ga, dovrši ili zatvori uz obrazloženje.",
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
        # These exact exceptions waive review only; CI and direct-commit checks still apply.
        if (pr["number"], pr.get("headRefName")) in AUTHORIZED_REVIEW_EXCEPTIONS:
            continue
        author = (pr.get("author") or {}).get("login")
        if author and human_approvers(pr) - {str(author).lower()}:
            continue
        merged_by = (pr.get("mergedBy") or {}).get("login", "?")
        problems.append(
            Problem(
                "medium",
                f"#{pr['number']} ({pr.get('headRefName', '?')})",
                "nije primjenjivo",
                f"PR #{pr['number']} spojen je u `main` bez provjerljivog odobrenja "
                "druge osobe koja je pregledala promjenu.",
                f"{pr.get('url', '?')} spojen je {merged_at:%Y-%m-%d %H:%M} UTC; spojio: {merged_by}.",
                "Drugi član tima treba pregledati spojenu promjenu; ispravci idu kroz novi PR. "
                "Budući PR-ovi trebaju odobrenje prije spajanja.",
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
                "nema",
                "nije primjenjivo",
                f"Commit {commit['sha'][:12]} dospio je na `main` bez PR-a.",
                f"{commit.get('url', '?')}, vrijeme commita: {committed_at:%Y-%m-%d %H:%M} UTC.",
                "Drugi član tima treba pregledati commit; daljnje promjene idu kroz PR.",
            )
        )
    return problems


def overall_severity(problems: list[Problem]) -> str:
    order = {"high": 0, "medium": 1, "low": 2}
    return "severity:" + min((p.severity for p in problems), key=order.__getitem__)


def render_body(problems: list[Problem], now: datetime) -> str:
    lines = [
        f"Otvara i ažurira `tools/daily_check.py` (posljednje izvođenje: {now:%Y-%m-%d %H:%M} UTC).",
        "Nalaz se automatski zatvara kada sve provjere prođu.",
        "Provjera odobrenja isključuje botove i autora PR-a; članstvo u timu i dalje provjeravaju ljudi.",
        "",
    ]
    for number, p in enumerate(problems, start=1):
        lines += [
            f"### {number}. {p.problem}",
            "",
            f"- **PR:** {p.pr}",
            f"- **Datoteka:** {p.file}",
            f"- **Problem:** {p.problem}",
            f"- **Kako se očituje:** {p.how_it_shows}",
            f"- **Prijedlog:** {p.proposal}",
            f"- **Ozbiljnost:** { {'high': 'visoka', 'medium': 'srednja', 'low': 'niska'}[p.severity]}",
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
    parser = argparse.ArgumentParser(description="Dnevna provjera repozitorija; održava jedan otvoren nalaz.")
    parser.add_argument("--dry-run", action="store_true", help="prikaži planirane radnje bez promjena na GitHubu")
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
        print(f"Broj pronađenih problema: {len(problems)}\n\n{body}")
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
    print("Sve provjere prolaze.")
    if issue is not None:
        act(
            "issue", "close", str(issue["number"]), "--comment",
            f"Sve provjere prolaze ({now:%Y-%m-%d %H:%M} UTC). Nalaz zatvara `tools/daily_check.py`.",
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
