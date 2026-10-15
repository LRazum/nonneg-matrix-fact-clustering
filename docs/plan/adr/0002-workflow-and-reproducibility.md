# ADR-0002: Small reviewed changes, shared understanding and traceable experiments

**Date:** 2026-10-15 · **Status:** accepted (Lovro, 2026-10-15)

## Context

Mislav, Sara and Lovro are preparing an NMF seminar for Matrične i tenzorske metode u analizi
podataka. The deliverables are a written seminar, presentation, Python code and experimental
results. All three must understand the full project. The application, dataset and implementation
details remain open and will be agreed later.

Lovro requested adapting the existing PelosiPlus workflow on 2026-10-15. Its useful practices
are small changes, human review, decision records, documentation propagation, findings and a
daily audit. Its product architecture and ownership boundaries do not describe this seminar.
This record documents Lovro's requested setup, not Mislav's or Sara's approval.

## Decision

1. Use one task per branch and a small PR. Human branches use `mislav/<topic>`, `sara/<topic>`
   and `lovro/<topic>`; AI-created branches use `codex/<topic>`. Never commit directly to `main`, force-push or
   rewrite another person's branch.
2. Every PR to `main` needs approval by at least one other human member of the three. AI
   review supplements that review. Rotate work and walkthroughs so all three can explain the
   mathematics, implementation, experiments and conclusions; record only real participation.
3. Keep root `AGENTS.md` as the single source of repository rules and `CLAUDE.md` as
   `@AGENTS.md`. Record material decisions in ADRs and update the affected plans, commands
   and deliverables in the same change.
4. Keep unresolved scientific choices visibly open. Prepare alternatives and rationale for
   team discussion before dependent implementation; do routine authorized corrections
   without adding a new approval step.
5. AI tools need explicit user authorization in the session before committing, pushing,
   opening PRs or publishing issues, comments, reviews, submissions or public artifacts.
   Authorization already given remains valid within its stated scope.
6. Run documentation/tool checks in CI and through the shared completion script. Verify
   actual hook installation before claiming tool integration. Add numerical CI and locked
   dependencies when the implementation is chosen.
7. Keep identified experiment configurations, data identity, code/environment provenance,
   stopping information and outputs for every reported run. Corrections create new run IDs;
   cited results are not silently overwritten. Missing evidence stays visibly missing.
8. Use shared findings and a daily GitHub audit for CI state, PR conflicts/staleness,
   approvals and commits reaching `main` without PRs. Audit enforcement starts at the captured
   setup baseline, 2026-10-15 21:19:49 UTC; pre-workflow initialization is not audited
   retroactively. Remote activation and identity configuration must be verified separately.

## Why

Small changes are easier for another student to understand and check. Human review and rotated
explanations support the learning goal without dividing knowledge into isolated roles.
Documentation propagation prevents a correct local change from leaving a misleading project
description. Decision records distinguish a deliberate scientific choice from an incidental
implementation detail.

NMF is nonunique and sensitive to methodological choices. Reproducible configurations and
provenance make results interpretable after code, data or environment changes. Numerical tests,
scientific review and traceable experiments provide different evidence; none replaces the
others. A scheduled audit catches some workflow violations but cannot prove understanding or
scientific correctness.

## What was rejected

- **Separate permanent owners for mathematics, code and experiments:** incompatible with
  the requirement that every member understands the full project.
- **Copying the earlier project's product stack and restrictions:** this project has no
  agreed API, database, hosted product or deployment requirement.
- **Choosing the solver and dataset during workflow setup:** Lovro explicitly left those
  implementation and application decisions for later discussion.
- **Treating AI approval or a green CI run as sufficient:** neither supplies another human
  member's review or establishes the scientific claims.
- **Keeping result screenshots without reproducible inputs:** a figure alone cannot explain
  which choices produced it.
- **A separate AI memory repository now:** durable decisions, tasks, source notes and findings
  already have shared homes here; extra infrastructure is not needed for this setup.
- **Assuming remote protections, labels or hooks are active:** local files do not establish
  the state of GitHub or each member's machine.

## Consequences

- `docs/CHANGE_PROTOCOL.md` defines the task procedure, propagation checklist and handover.
- `docs/plan/PIPELINE.md` distinguishes current checks from planned numerical work and states
  the minimum provenance for results.
- `docs/plan/AI_REVIEW.md` defines findings, review and the audit's limits.
- `.github/pull_request_template.md`, `.github/workflows/ci.yml` and
  `.github/workflows/daily-check.yml` implement the local workflow setup.
- `tools/check_docs.py`, `tools/check_before_stop.py` and `tools/daily_check.py`, with tests,
  provide the automated checks. `.claude/settings.json` and `.codex/hooks.json` configure the
  same completion checker. Hook activation is verified independently of script presence.
- GitHub identities, branch protection availability, remote audit activation, application,
  dataset, solver and numerical environment remain explicit follow-up work.

## Addendum 2026-10-15: explicitly authorized initial workflow merge

After reviewing the prepared setup, Lovro explicitly requested commit, push, PR and merge in
the current session. This authorizes publishing and merging initial workflow PR #1 from
`codex/seminar-workflow` without waiting for another member's review. It does not record or
imply an approval from Mislav or Sara, and it does not change the review rule for later PRs.

The daily audit recognizes only that exact PR number and branch as a review exception. CI
must still pass; direct commits and other unreviewed merges remain findings. Creating the
finding labels required by the published daily workflow is part of its activation. No
unrelated issues, messages or repository access changes are authorized by this instruction.
