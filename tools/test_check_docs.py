"""Run with: python3 -m unittest discover -s tools -p 'test_*.py'."""
from __future__ import annotations

import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import check_docs

ADR = """# ADR-0001: Koristiti jedan repozitorij

**Datum:** 2026-10-15 · **Status:** prihvaćeno (Projektni tim, 2026-10-15)

## Kontekst
Jedan seminar.
## Odluka
Jedan repozitorij.
## Obrazloženje
Zajednički rad.
## Odbačene mogućnosti
Odvojeni repozitoriji.
## Posljedice
Zajednički pregled.
"""


class DocsCheckTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.config = check_docs.Config(planned=frozenset())

    def write(self, path: str, text: str) -> None:
        target = self.root / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text, encoding="utf-8")

    def checks(self, config: check_docs.Config | None = None) -> list[check_docs.Problem]:
        return check_docs.run_checks(self.root, config or self.config)

    def test_empty_directory_passes(self) -> None:
        self.assertEqual(self.checks(), [])

    def test_local_links_inline_paths_and_planned_paths(self) -> None:
        self.write("README.md", "[note](notes/a%20b.md#section) `notes/a b.md` `later/file.md`\n")
        self.write("notes/a b.md", "[root](../README.md)\n")
        config = check_docs.Config(planned=frozenset({"later/file.md"}))
        self.assertEqual(self.checks(config), [])

    def test_broken_link_and_inline_path_report_source_lines(self) -> None:
        self.write("README.md", "line one\n[missing](missing.md)\n`notes/missing.txt:3`\n")
        found = self.checks()
        self.assertEqual([(p.path, p.line, p.check) for p in found], [("README.md", 2, 1), ("README.md", 3, 1)])

    def test_paths_outside_repository_and_stale_planned_entry_fail(self) -> None:
        self.write("README.md", "[outside](../outside.md)\n")
        config = check_docs.Config(planned=frozenset({"README.md"}))
        self.assertEqual({p.check for p in self.checks(config)}, {1})
        self.assertEqual(len(self.checks(config)), 2)

    def test_fenced_examples_external_links_and_branch_names_are_skipped(self) -> None:
        self.write("README.md", "[site](https://example.com/a) `codex/topic`\n````md\n```\n[missing](missing.md)\n````\n")
        self.assertEqual(self.checks(), [])

    def test_agents_requires_exact_claude_pointer(self) -> None:
        self.write("AGENTS.md", "rules\n")
        self.assertEqual([p.check for p in self.checks()], [2])
        self.write("CLAUDE.md", "@AGENTS.md\n")
        self.assertEqual(self.checks(), [])
        self.write("CLAUDE.md", "other rules\n")
        self.assertIn("must contain only", self.checks()[0].message)

    def test_orphan_claude_pointer_fails(self) -> None:
        self.write("CLAUDE.md", "@AGENTS.md\n")
        self.assertIn("without AGENTS.md", self.checks()[0].message)

    def test_valid_adr_and_complete_index_pass(self) -> None:
        self.write("docs/plan/adr/0001-one-repo.md", ADR)
        self.write("docs/INDEX.md", "[decision](plan/adr/0001-one-repo.md)\n")
        self.assertEqual(self.checks(), [])

    def test_duplicate_adr_number_and_bad_structure_fail(self) -> None:
        self.write("docs/plan/adr/0001-one-repo.md", ADR)
        self.write("docs/plan/adr/0001-other.md", ADR.replace("## Obrazloženje", "## Razlog"))
        problems = [p for p in self.checks() if p.check == 3]
        self.assertTrue(any("also used" in p.message for p in problems))
        self.assertTrue(any("sections must be" in p.message for p in problems))

    def test_adr_status_dates_and_superseded_reference_are_validated(self) -> None:
        self.write("docs/plan/adr/0001-one-repo.md", ADR.replace("prihvaćeno (Projektni tim, 2026-10-15)", "prihvaćeno (Projektni tim, 2026-02-30)"))
        self.assertTrue(any("status must be" in p.message for p in self.checks()))
        self.write("docs/plan/adr/0001-one-repo.md", ADR.replace("prihvaćeno (Projektni tim, 2026-10-15)", "zamijenjeno zapisom ADR-0009"))
        self.assertTrue(any("unknown ADR-0009" in p.message for p in self.checks()))

    def test_croatian_adr_statuses_and_dated_addendum(self) -> None:
        self.write("docs/INDEX.md", "[opseg](plan/adr/0001-one-repo.md)\n[jezik](plan/adr/0002-language.md)\n")
        for status in ("predloženo", "prihvaćeno (Član tima, 2026-10-15)", "zamijenjeno zapisom ADR-0002"):
            with self.subTest(status=status):
                self.write("docs/plan/adr/0001-one-repo.md", ADR.replace(
                    "prihvaćeno (Projektni tim, 2026-10-15)", status,
                ) + "\n## Dodatak 2026-10-15: jezično usklađivanje\nČuvamo povijest odluka.\n")
                self.write("docs/plan/adr/0002-language.md", ADR.replace("# ADR-0001:", "# ADR-0002:"))
                self.assertEqual(self.checks(), [])

        self.write("docs/plan/adr/0001-one-repo.md", ADR + "\n## Dodatak 2026-02-30: nevaljan datum\n")
        self.assertTrue(any("addendum heading must be" in p.message for p in self.checks()))
        self.write("docs/plan/adr/0001-one-repo.md", ADR.replace("## Obrazloženje", "## Obrazlozenje"))
        self.assertTrue(any("sections must be" in p.message for p in self.checks()))

    def test_index_must_list_every_document(self) -> None:
        self.write("docs/plan/PROJECT.md", "Project\n")
        self.write("docs/INDEX.md", "Index\n")
        self.assertEqual([(p.path, p.check) for p in self.checks()], [("docs/INDEX.md", 5)])
        self.write("docs/INDEX.md", "[project](plan/PROJECT.md)\n")
        self.assertEqual(self.checks(), [])

    def test_env_examples_cannot_contain_values(self) -> None:
        self.write(".env.example", "# template\nTOKEN=\nOTHER=secret\n")
        self.assertEqual([(p.path, p.line, p.check) for p in self.checks()], [(".env.example", 3, 4)])

    @unittest.skipUnless(shutil.which("git"), "Git is not installed")
    def test_git_checks_untracked_files_before_first_commit_and_skips_ignored_files(self) -> None:
        subprocess.run(["git", "init", "-q", str(self.root)], check=True)
        self.write(".gitignore", ".env\nresults/\n")
        self.write(".env", "TOKEN=secret\n")
        self.write("results/notes.md", "[missing](missing.md)\n")
        self.write("README.md", "Use `.env`. [missing](missing.md)\n")
        problems = self.checks()
        self.assertEqual([(p.path, p.check) for p in problems], [("README.md", 1)])
        self.write("README.md", "Use `.env`.\n")
        self.assertEqual(self.checks(), [])

    @unittest.skipUnless(shutil.which("git"), "Git is not installed")
    def test_unignored_env_is_reported_without_exposing_content(self) -> None:
        subprocess.run(["git", "init", "-q", str(self.root)], check=True)
        self.write(".env", "TOKEN=secret-value\n")
        problems = self.checks()
        self.assertEqual([p.check for p in problems], [4])
        self.assertNotIn("secret-value", str(problems))

    def test_cli_exit_status(self) -> None:
        with patch.object(check_docs, "REPO_ROOT", self.root), patch("builtins.print") as output:
            self.assertEqual(check_docs.main(), 0)
            output.assert_called_with("Documentation is consistent. (0 warnings.)")
            self.write("README.md", "[missing](missing.md)\n")
            self.assertEqual(check_docs.main(), 1)


if __name__ == "__main__":
    unittest.main()
