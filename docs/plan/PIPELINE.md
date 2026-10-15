# Pipeline

Repository structure, automated checks and the path from a research question to reproducible
seminar results. The workflow setup is separate from the numerical work that the team will
choose later.

## Repository structure

Keep this tree aligned manually; fenced trees are not a substitute for checked links.

```text
AGENTS.md                           single source of repository rules
CLAUDE.md                           @AGENTS.md
README.md                           purpose, team, current state and commands
.gitignore
docs/
  INDEX.md                          documentation index
  CHANGE_PROTOCOL.md                tasks, review and documentation propagation
  plan/
    PROJECT.md                      scope, deliverables and open decisions
    TASKS.md                        small tasks and their dependencies
    METHODOLOGY.md                  mathematical and experimental planning
    PIPELINE.md                     this file
    AI_REVIEW.md                    findings, audit and review procedure
    adr/                            decision records
  research/
    LITERATURE.md                   source identities, roles and reading notes
tools/
  check_docs.py
  test_check_docs.py
  daily_check.py
  test_daily_check.py
  check_before_stop.py               shared completion checks
  test_check_before_stop.py
  check_project.py                   planned: agreed numerical checks
.github/
  pull_request_template.md
  workflows/
    ci.yml
    daily-check.yml
.claude/
  settings.json                      Claude Stop hook configuration
  hooks/check_before_stop.py         wrapper around the shared completion check
.codex/
  hooks.json                         Codex Stop hook configuration; trust is host-local
pyproject.toml                       planned: agreed numerical environment
uv.lock                              planned: locked numerical dependencies
src/                                 planned: reusable Python implementation
tests/                               planned: numerical and data checks
experiments/                         planned: configurations and reproducible entry points
data/                                planned: documented data acquisition/preparation
results/                             planned: identified runs, figures and tables
seminar/                             planned: written seminar source
presentation/                        planned: presentation source
```

The planned directories are introduced when there is actual work for them. A folder name does
not choose a dataset, solver or document format. The proposed uv lockfile follows the reference
workflow; the numerical environment and package manager are still to be agreed. Verify the host
integration before saying that a Codex completion hook is active.

## Checks available at setup

`.github/workflows/ci.yml` runs on pull requests, pushes to `main` and manual dispatch. It runs
the documentation check and standard-library tests of `tools/`. These checks require no NMF
package, selected dataset or paid service. They do not yet validate a numerical implementation.

Run locally from the repository root:

```bash
python3 tools/check_docs.py
python3 -m unittest discover -s tools -p 'test_*.py'
python3 tools/check_before_stop.py
python3 tools/daily_check.py --dry-run
```

The daily dry run reads GitHub when access is available and reports the proposed audit action
without publishing it. Missing authentication or an unavailable API is reported, not recorded
as a clean audit. See `docs/plan/AI_REVIEW.md` for the exact audit scope.

Actions are pinned to full commit SHAs with their versions in comments. CI receives only the
permissions it needs; checkout does not retain credentials. The daily workflow needs issue-write
permission to maintain its audit issue. Adding that workflow locally does not enable scheduled
runs until it reaches the repository's default branch and GitHub Actions permits execution.

## Numerical environment: later team decision

Python is agreed; the solver, dependency versions, numerical commands and application are
open. The implementation task will add the environment specification and lock file together,
then document one supported setup command, test command and experiment entry point. Add a CI
job that installs locked dependencies and runs small deterministic checks. Keep full data
downloads and long experiment sweeps outside the default PR job unless explicitly justified.

The completion script, CI, root command list and this page must change together. Until
`pyproject.toml` exists, the completion script reports numerical verification as NOT RUN.
Once that marker exists, it requires `tools/check_project.py`, introduced with the agreed
environment to run its numerical checks. A missing runner then fails visibly. A numerical
job must also fail on a broken environment or invalid input; absence is never a passing check.

## Completion hooks

`tools/check_before_stop.py` is the local CLI. Its `--hook` mode emits Stop-hook JSON, and the
Claude wrapper calls that shared implementation. `.codex/hooks.json` invokes the same checker
through the Git root, so clones and worktrees do not depend on Lovro's absolute path. Codex
requires both a trusted project configuration layer and review
and trust of the exact non-managed hook definition; a new or changed definition is skipped
until trusted. Verify configuration and a real invocation before reporting runtime activation.
These are product requirements documented in the [official hooks guide](https://learn.chatgpt.com/docs/hooks),
checked on 2026-10-15, separate from the repository's human PR review rule.

Configuration files for both tools are present. Running the configured command manually proves
the command works, not that either application has loaded it. Review the Codex hook using the
/hooks command in the CLI, trust the intended definition and verify a real invocation on each host.
Do not bypass trust or change personal/global trust settings as part of this repository setup.

## Remote activation

File presence alone does not create a commit, push, PR, issue, label or repository setting.
Lovro subsequently authorized commit, push, PR and merge of the initial workflow on 2026-10-15;
the one-time review exception is recorded in ADR-0002. After the files reach the
default branch, verify Actions/Issues are enabled, create the finding labels described in
`docs/plan/AI_REVIEW.md`, and inspect a CI run and a read-only audit preview before relying on
the daily issue. Configure available branch protection for the human review rule. Do not
assume the reference project's GitHub-plan restrictions apply to this repository.

## Research and experiment flow

1. **Understand:** read the main Gillis source, develop the mathematical explanation and
   record assumptions, dimensions and source locations. Compare algorithm statements with
   the original papers where needed.
2. **Decide:** agree on a new concrete problem and dataset, the interpretation of the input
   matrix, the objective, algorithm and evaluation. Record material choices in ADRs and
   `docs/plan/METHODOLOGY.md` before building dependent experiments.
3. **Implement and check:** connect the derivation to the Python implementation. Use tiny
   analytically understood cases, invariants and a justified reference comparison where
   appropriate. Tests must allow the method's mathematical nonuniqueness.
4. **Run:** execute experiments from recorded configurations and the locked environment.
   Keep failed runs distinguishable from successful ones; retain enough provenance to
   reproduce or explain every result used in a deliverable.
5. **Interpret:** evaluate reconstruction and the actual application question separately.
   Record sensitivity, limitations and unresolved observations. A small reconstruction error
   alone does not establish useful components or clusters.
6. **Write and present:** generate figures/tables from identified runs, cite those runs in
   working notes and align claims between the seminar and slides. Every team member walks
   through the full reasoning and can explain the conclusions before submission.

## Minimum provenance for a reported run

Choose the concrete manifest format during implementation. It must preserve:

- A distinct run ID, timestamp, status and the command/configuration used.
- Code commit and whether the working tree was dirty. Preserve the relevant patch or state
  when results depend on uncommitted code; a commit hash alone is then insufficient.
- Python and dependency environment, and material execution details when timing is reported.
- Data source, version or checksum, acquisition/access date, licence and preprocessing
  configuration; identify generated matrices or splits used by the run.
- Objective, rank, solver, initialization, random seed(s), tolerances, iteration limits and
  actual stopping reason. A seed alone is not a complete reproducibility record.
- Metrics, generated artifacts, warnings and failures. Preserve independent repeated runs
  when investigating initialization or other variability.

Published result identities are stable: a correction creates a new run and links the earlier
one. Do not overwrite the evidence behind an existing figure. Large or restricted artifacts may
live outside git, but the repository must retain their identities and retrieval instructions.
Never invent missing provenance.

## Data and artifacts

Check licence, privacy and redistribution terms before committing data. Keep downloaded raw
data and large derived artifacts out of git by default; record acquisition and regeneration
instead. Small redistributable fixtures and selected figures may be committed when justified
and reviewed. Do not copy papers from local personal folders into the repository merely to make
an absolute link work. The literature index records portable bibliographic identities.

No deployment, hosted service or external submission is part of this setup. Submission and
public release require the user's explicit instruction for the concrete action.
