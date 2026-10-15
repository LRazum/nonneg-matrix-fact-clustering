# AI review, findings and the daily audit

This process keeps problems and handovers visible to Mislav, Sara and Lovro. Root `AGENTS.md`
and `docs/CHANGE_PROTOCOL.md` remain the rules; an AI tool is a collaborator, not a human
reviewer or evidence that the team understands a result.

## Findings as shared memory

Record a reproducible problem once and link later discoveries to it. Use a GitHub issue with:

- `finding`.
- One source label: `source:codex`, `source:claude-code`, `source:human-review`, `source:ci` or
  `source:daily-check`.
- One severity label: `severity:high` for an invalid central result, a broken `main` or a
  leaked secret; `severity:medium` for blocked work, misleading documentation or missing
  provenance; `severity:low` for cleanup.

The body states the PR or `none`, file and location, concrete problem, reproduction/evidence,
scientific or practical consequence, and a proposed next step. Include the relevant run ID for
experimental findings. A suspicion without evidence is an open question, not a proven defect.

At the start of work inspect `gh issue list --label finding --state open`. A fixing PR uses
`Closes #<number>` when the issue is actually resolved. Do not silently close a finding because
the code moved. Label names describe the intended scheme; their existence on GitHub must be
verified, and local configuration is not proof that they were created.

AI tools may prepare finding text locally. Publishing an issue, label, comment or review needs
explicit user authorization for that action in the session, unless it is the audit action
already authorized by an enabled repository workflow. Do not seek the same authorization again
within its approved scope.

## Daily GitHub audit

`.github/workflows/daily-check.yml` schedules `tools/daily_check.py` at 07:00 UTC and supports
manual dispatch. At the current Europe/Copenhagen offset this is 09:00; winter local time is
08:00. GitHub schedules are best effort. The workflow has to reach the default branch and
Actions must be enabled before scheduled auditing can run.

The audit checks:

1. The CI workflow exists and its latest completed run on `main` succeeded.
2. Open PRs for reported merge conflicts.
3. Open PRs with no update for more than three days.
4. PRs merged into `main` during the last 48 hours for an approving human review by someone
   other than the author, given before merge.
5. Commits visible on `main` with committer dates during the last 48 hours for an associated
   merged PR into `main`.

Historical review/direct-commit enforcement starts at the captured setup baseline,
2026-10-15 21:19:49 UTC. The pre-workflow repository initialization is not retroactively
reported as a violation of the new rules. The overlapping window reduces missed reports after a delayed run; it is not a
complete history audit. Unknown mergeability, API failures or missing required information are
visible diagnostics, not successful checks.

This is a bounded audit: it reads up to 200 open PRs, 200 merged PRs and 100 commits. It uses
committer dates rather than push timestamps, so an old commit newly pushed directly to `main`
can fall outside the window. These limits are adequate for the intended small seminar team;
the audit is not a complete history or a substitute for branch protection.

The human rule is stricter: the reviewer must be another member of Mislav, Sara and Lovro.
Until their GitHub identities are configured and verified, a non-author human approval only
checks that limited condition; the PR participants still verify team membership. Automated
reviews and bot approvals never fulfill the human-review rule. The audit cannot verify that
reviewers understood the mathematics, that all three members learned the material, or that the
results are scientifically sound.

The sole bootstrap exception is PR #1 from `codex/seminar-workflow`: Lovro explicitly requested
its commit, push, PR and merge on 2026-10-15. ADR-0002 records the instruction. The audit
recognizes that exact number/branch pair without claiming a human approval. No other PR,
CI failure or direct commit is exempted by that exception.

On problems, the audit maintains one issue titled
"Daily check: main or open pull requests need attention", with `finding`, `source:daily-check`
and the highest detected severity. It updates an existing open audit issue rather than opening
a duplicate. A clean audit resolves the existing report. It never fixes code, merges a PR,
approves work or alters research decisions. The intended labels and workflow permissions must
exist for publication to succeed; an API failure remains a failure.

Run `python3 tools/daily_check.py --dry-run` to inspect the proposed action without writes.
Installing this setup in the working tree is not a claim that a remote audit has already run.
Use GitHub branch protection as well when available; verify its actual configuration rather
than assuming a restriction from the other project's GitHub plan applies here.

### Labels and first activation

The label scheme above is configuration to create after publication is authorized, not a claim
that remote labels already exist. At minimum the daily publisher needs `finding`,
`source:daily-check`, `severity:high` and `severity:medium`. For example, run these only as part
of an authorized GitHub setup:

```bash
gh label create finding --color B60205 --description "A verified project or workflow problem"
gh label create source:daily-check --color 5319E7
gh label create severity:high --color D93F0B
gh label create severity:medium --color FBCA04
```

The remaining source labels and `severity:low` can be added when used. Verify existing labels
before creating them, the available human review protections, a successful CI run and a
read-only audit preview. Publishing the workflow allows its scheduled audit to maintain the
single report; it does not authorize unrelated messages or changes.

## Reviewing a change

Review a PR against its actual base and identify the commit inspected. Read the callers,
mathematical explanation and affected experiments, not only the diff. If the base is behind
`main`, note any integration uncertainty. Protect a person's uncommitted work: use an isolated
worktree for tests when needed and remove only the worktree you created.

Check evidence appropriate to the change:

- Mathematical claims: assumptions, dimensions, derivation, source location and the exact
  convergence or optimality claim. Decreasing objective values do not establish global
  optimality or convergence to a particular factorization.
- Numerical code: invalid inputs, finite values, nonnegativity, shapes and stopping behavior;
  small cases with known properties. Factor scaling/permutation can make raw factor equality
  an invalid test. A library comparison is useful evidence, not a proof of the same solution.
- Experiments: source data, preprocessing, configuration, rank selection, variation over runs,
  metric interpretation, artifact provenance and the link between claims and evidence.
- Documentation/workflow: propagation checklist, truthful state, executable commands and
  the distinction between installed automation and a locally prepared configuration.

Verify a suspected defect with a calculation, minimal test or source before reporting it as a
finding. Report actionable findings in severity order, with exact locations and consequences;
separate optional improvements from defects. State what was checked and what remains unrun.
When commits change, focus on the new changes and their affected dependencies. Publish a review
only within explicit authorization. Never claim an AI review fulfills the required human
approval.

## Handover and team learning

Use the handover fields in `docs/CHANGE_PROTOCOL.md` section 9. Keep accepted decisions in ADRs,
tasks in `docs/plan/TASKS.md`, source notes in `docs/research/LITERATURE.md` and verified problems
in findings. There is no separate memory repository in this setup, and no automatic pull/push
of personal AI notes. A future shared memory service needs a concrete team decision.

At milestone walkthroughs, rotate who explains the model, derivation, implementation and
experiment interpretation. Capture unresolved questions as tasks. Mark a member's attendance,
review or understanding only after actual participation or confirmation; a generated checklist
is not evidence that Mislav, Sara or Lovro completed it.
