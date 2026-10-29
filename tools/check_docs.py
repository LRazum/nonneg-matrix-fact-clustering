#!/usr/bin/env python3
"""Check repository documentation with Python 3.10+ and the standard library.

Run with ``python3 tools/check_docs.py``. All checks include untracked files and
work before the first commit; Git-ignored data and outputs are not scanned.
"""
from __future__ import annotations

import os
import re
import subprocess
import sys
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from urllib.parse import unquote

REPO_ROOT = Path(__file__).resolve().parent.parent
# Inline-code branch names (team members and historical PRs) are not repository paths.
BRANCH_PREFIXES = ("codex/", "mislav/", "sara/", "lovro/")

# Remove an entry when its path is created; the checker reports stale entries.
PLANNED = frozenset({
    "src/", "tests/", "experiments/", "data/", "results/", "seminar/",
    "presentation/", "pyproject.toml", "uv.lock", "tools/check_project.py",
})
SKIP_DIRS = {".git", ".venv", "__pycache__", ".pytest_cache", ".mypy_cache"}
FILE_EXTENSIONS = {
    "bib", "cfg", "csv", "example", "html", "ini", "ipynb", "json", "lock",
    "md", "npy", "npz", "pdf", "png", "py", "sh", "svg", "tex", "toml",
    "tsv", "txt", "yaml", "yml",
}
ADR_DIR = "docs/plan/adr"
ADR_SECTIONS = ("Kontekst", "Odluka", "Obrazloženje", "Odbačene mogućnosti", "Posljedice")
LINK_RE = re.compile(r'!?\[[^\]\n]*\]\(\s*(<[^>\n]+>|[^\s)]+)(?:\s+"[^"\n]*")?\s*\)')
INLINE_RE = re.compile(r"`([^`\n]+)`")
SCHEME_RE = re.compile(r"^[A-Za-z][A-Za-z0-9+.-]*:")
ADR_NAME_RE = re.compile(r"^(\d{4})-[a-z0-9]+(?:-[a-z0-9]+)*\.md$")
ADDENDUM_RE = re.compile(r"^## Dodatak (\d{4}-\d{2}-\d{2}): \S")
SECRET_RE = re.compile(r"(^|/)\.env(?:\.[A-Za-z0-9_-]+)?$")


@dataclass(frozen=True)
class Config:
    planned: frozenset[str] = PLANNED


@dataclass(frozen=True, order=True)
class Problem:
    path: str
    line: int
    check: int
    message: str

    def __str__(self) -> str:
        where = f"{self.path}:{self.line}" if self.line else self.path
        return f"{where}: [check {self.check}] {self.message}"


@dataclass(frozen=True)
class Mention:
    source: str
    line: int
    raw: str
    path: str | None


class Repo:
    def __init__(self, root: Path) -> None:
        self.root = root.resolve()
        self.git_ok = self.git(["rev-parse", "--git-dir"]).returncode == 0
        if self.git_ok:
            result = self.git(["ls-files", "-z", "--cached", "--others", "--exclude-standard"])
            names = result.stdout.split("\0")
        else:
            names = []
            for folder, dirs, files in os.walk(self.root):
                dirs[:] = [name for name in dirs if name not in SKIP_DIRS]
                names.extend((Path(folder) / name).relative_to(self.root).as_posix() for name in files)
        self.files = sorted({name for name in names if name and (self.root / name).is_file()})

    def git(self, args: list[str], stdin: str | None = None) -> subprocess.CompletedProcess[str]:
        try:
            return subprocess.run(
                ["git", "-C", str(self.root), *args], input=stdin,
                capture_output=True, text=True, encoding="utf-8", check=False,
            )
        except FileNotFoundError:
            return subprocess.CompletedProcess(args, 127, "", "git not found")

    def ignored(self, paths: set[str]) -> set[str]:
        if not paths or not self.git_ok:
            return set()
        result = self.git(["check-ignore", "-z", "--stdin"], "\0".join(sorted(paths)) + "\0")
        return set(result.stdout.split("\0")) - {""}

    def text(self, path: str) -> str:
        return (self.root / path).read_text(encoding="utf-8", errors="replace")

    def exists(self, path: str) -> bool:
        return (self.root / path).exists()


def normalize_rel(path: str) -> str | None:
    """Return a repository-relative path, or None if it escapes the repository."""
    if path.startswith("/"):
        return None
    parts: list[str] = []
    for part in path.split("/"):
        if part in ("", "."):
            continue
        if part == "..":
            if not parts:
                return None
            parts.pop()
        else:
            parts.append(part)
    return "/".join(parts)


def markdown_lines(text: str) -> list[tuple[int, str]]:
    """Exclude fenced examples from path checks."""
    result = []
    fence: tuple[str, int] | None = None
    for number, line in enumerate(text.splitlines(), 1):
        match = re.match(r"^\s*(`{3,}|~{3,})(.*)$", line)
        if match:
            marker, rest = match.groups()
            if fence is None:
                fence = (marker[0], len(marker))
            elif marker[0] == fence[0] and len(marker) >= fence[1] and not rest.strip():
                fence = None
            continue
        if fence is None:
            result.append((number, line))
    return result


def extract_mentions(repo: Repo, path: str) -> list[Mention]:
    mentions = []
    for number, line in markdown_lines(repo.text(path)):
        for match in LINK_RE.finditer(line):
            raw = match.group(1).strip("<>")
            target = unquote(raw.split("#", 1)[0])
            if not target or SCHEME_RE.match(target) or target.startswith("//"):
                continue
            joined = (Path(path).parent / target).as_posix()
            mentions.append(Mention(path, number, raw, normalize_rel(joined)))
        for match in INLINE_RE.finditer(LINK_RE.sub("", line)):
            token = re.sub(r":\d+(?:-\d+)?$", "", match.group(1))
            if not re.fullmatch(r"[A-Za-z0-9_./-]+", token) or set(token) <= {".", "/"}:
                continue
            if token.startswith(BRANCH_PREFIXES):
                continue
            name = token.rsplit("/", 1)[-1]
            hidden_file = len(name) > 1 and name.startswith(".") and name[1].isalpha()
            file_extension = "." in name and name.rsplit(".", 1)[-1] in FILE_EXTENSIONS
            if "/" in token or hidden_file or file_extension:
                mentions.append(Mention(path, number, token, normalize_rel(token)))
    return mentions


def check_paths(repo: Repo, mentions: list[Mention], config: Config) -> list[Problem]:
    problems = []
    planned = {path.rstrip("/") for path in config.planned}
    ignored = repo.ignored({m.path for m in mentions if m.path is not None})
    for mention in mentions:
        if mention.path is None:
            message = f"`{mention.raw}` points outside the repository"
        elif repo.exists(mention.path) or mention.path in planned or mention.path in ignored:
            continue
        else:
            message = f"`{mention.raw}` does not exist and is not in PLANNED (tools/check_docs.py)"
        problems.append(Problem(mention.source, mention.line, 1, message))
    for entry in sorted(config.planned):
        if repo.exists(entry):
            problems.append(Problem("tools/check_docs.py", 0, 1, f"PLANNED entry `{entry}` exists now; remove it"))
    return problems


def check_agents_pointers(repo: Repo) -> list[Problem]:
    problems = []
    names = set(repo.files)
    for path in repo.files:
        name = Path(path).name
        if name == "AGENTS.md":
            pointer = str(Path(path).with_name("CLAUDE.md"))
            if pointer not in names:
                problems.append(Problem(path, 0, 2, f"missing `{pointer}` with `@AGENTS.md`"))
        elif name == "CLAUDE.md":
            if str(Path(path).with_name("AGENTS.md")) not in names:
                problems.append(Problem(path, 0, 2, "CLAUDE.md without AGENTS.md next to it"))
            if repo.text(path).strip() != "@AGENTS.md":
                problems.append(Problem(path, 1, 2, "CLAUDE.md must contain only `@AGENTS.md`"))
    return problems


def valid_date(value: str) -> bool:
    try:
        date.fromisoformat(value)
        return True
    except ValueError:
        return False


def check_adrs(repo: Repo) -> list[Problem]:
    problems = []
    numbers: dict[str, str] = {}
    records = []
    for path in repo.files:
        if Path(path).parent.as_posix() != ADR_DIR or not path.endswith(".md") or Path(path).name == "README.md":
            continue
        match = ADR_NAME_RE.fullmatch(Path(path).name)
        if not match:
            problems.append(Problem(path, 0, 3, "ADR file name must be NNNN-short-title.md"))
            continue
        number = match.group(1)
        if number in numbers:
            problems.append(Problem(path, 0, 3, f"ADR number {number} is also used by {numbers[number]}"))
        numbers.setdefault(number, path)
        records.append((path, number, repo.text(path).splitlines()))
    for path, number, lines in records:
        first = next(((i, line) for i, line in enumerate(lines, 1) if line.strip()), (1, ""))
        if not re.match(rf"^# ADR-{number}: \S", first[1]):
            problems.append(Problem(path, first[0], 3, f"first line must be `# ADR-{number}: <decision>`"))
        header = next(((i, line) for i, line in enumerate(lines[:8], 1) if line.startswith("**Datum:**")), (0, ""))
        match = re.fullmatch(r"\*\*Datum:\*\* (\d{4}-\d{2}-\d{2}) · \*\*Status:\*\* (.+)", header[1])
        if not match or not valid_date(match.group(1)):
            problems.append(Problem(path, header[0], 3, "missing or invalid `**Datum:** YYYY-MM-DD · **Status:** ...` line"))
        else:
            status = match.group(2)
            accepted = re.fullmatch(r"prihvaćeno \([^,()]+, (\d{4}-\d{2}-\d{2})\)", status)
            superseded = re.fullmatch(r"zamijenjeno zapisom ADR-(\d{4})", status)
            if status != "predloženo" and not (accepted and valid_date(accepted.group(1))) and not superseded:
                problems.append(Problem(path, header[0], 3, "status must be predloženo, prihvaćeno (<tko>, YYYY-MM-DD), or zamijenjeno zapisom ADR-NNNN"))
            if superseded and superseded.group(1) not in numbers:
                problems.append(Problem(path, header[0], 3, f"superseded by unknown ADR-{superseded.group(1)}"))
        sections = []
        addendum_started = False
        for line_number, line in enumerate(lines, 1):
            if not line.startswith("## "):
                continue
            if line.startswith("## Dodatak"):
                addendum_started = True
                addendum = ADDENDUM_RE.match(line)
                if not addendum or not valid_date(addendum.group(1)):
                    problems.append(Problem(path, line_number, 3, "addendum heading must be `## Dodatak YYYY-MM-DD: <što>`"))
            else:
                sections.append(line[3:].strip())
                if addendum_started:
                    problems.append(Problem(path, line_number, 3, "main sections must precede addenda"))
        if sections != list(ADR_SECTIONS):
            problems.append(Problem(path, 0, 3, "sections must be, in order: " + ", ".join(ADR_SECTIONS)))
    return problems


def check_secrets(repo: Repo, mentions: list[Mention]) -> list[Problem]:
    secrets = {path for path in repo.files if SECRET_RE.search(path) and not path.endswith(".example")}
    secrets.update(m.path for m in mentions if m.path and SECRET_RE.search(m.path) and not m.path.endswith(".example"))
    problems = [Problem(path, 0, 4, "secret file must be Git-ignored") for path in sorted(secrets - repo.ignored(secrets))]
    for path in repo.files:
        if not Path(path).name.endswith(".env.example"):
            continue
        for number, raw in enumerate(repo.text(path).splitlines(), 1):
            line = raw.strip()
            if line and not line.startswith("#") and not re.fullmatch(r"[A-Z][A-Z0-9_]*=", line):
                problems.append(Problem(path, number, 4, "must be `NAME=` with no value"))
    return problems


def check_index(repo: Repo) -> list[Problem]:
    documents = {path for path in repo.files if path.startswith("docs/") and path != "docs/INDEX.md"}
    if not documents:
        return []
    if "docs/INDEX.md" not in repo.files:
        return [Problem("docs/INDEX.md", 0, 5, "missing; it must list every file under docs/")]
    listed = {mention.path for mention in extract_mentions(repo, "docs/INDEX.md")}
    return [Problem("docs/INDEX.md", 0, 5, f"does not mention `{path}`") for path in sorted(documents - listed)]


def run_checks(root: Path, config: Config | None = None) -> list[Problem]:
    repo = Repo(root)
    config = config or Config()
    mentions = [mention for path in repo.files if path.endswith(".md") for mention in extract_mentions(repo, path)]
    return sorted(set(
        check_paths(repo, mentions, config)
        + check_agents_pointers(repo)
        + check_adrs(repo)
        + check_secrets(repo, mentions)
        + check_index(repo)
    ))


def main() -> int:
    problems = run_checks(REPO_ROOT)
    for problem in problems:
        print(problem)
    if problems:
        print(f"{len(problems)} warning(s).")
        return 1
    print("Documentation is consistent. (0 warnings.)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
