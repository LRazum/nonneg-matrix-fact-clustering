# Tasks and milestones

Status is evidence-based: a plan is not an implementation, passing tools checks are not
numerical results, and an AI summary is not a human approval. No individual task assignments
have been agreed. All tasks are shared; a temporary lead/reviewer can be recorded later.

## Overview

| Task | Purpose | Depends on | State |
|---|---|---|---|
| T0 | Establish project context and the adapted repository workflow | User's scope decisions | Implemented; publication authorized in initial PR, host trust remains per machine |
| T1 | Develop the common mathematical understanding from Gillis and supporting papers | T0 context | Ready to start |
| T2 | Choose a concrete problem and dataset with a justified NMF representation | T0 context | Open; may proceed alongside T1 |
| T3 | Agree the objective, algorithm and experiment design | T1, T2 | Open |
| T4 | Implement and verify the agreed NMF method in Python | T3 | Deferred until the team agrees implementation |
| T5 | Run reproducible experiments and interpret results | T4, data preparation | Open |
| T6 | Assemble the written seminar and presentation | T1 onward; final evidence from T5 | Open |
| T7 | Reproduce the final evidence and rehearse the complete explanation together | T5, T6 | Open |

The agreed project deadline is unknown. This is a dependency order, not a dated schedule or
an assignment of different subject areas to different people.

## T0: workflow setup

Deliver rules, a literature map, the methodology plan, decision records, a documentation
propagation checklist, PR template, CI, finish checker and a daily-audit definition. Validate
locally. Distinguish prepared configuration from trusted/running hooks and remotely enabled
workflows. Do not commit, push or publish GitHub content without authorization.

Local verification on 2026-10-15: documentation check reported 0 warnings and all 43 workflow
tool tests passed. Both configured hook commands were invoked manually from the repository
root and a subdirectory: valid JSON, with numerical checks explicitly NOT RUN. Workflow YAML
and text formatting were checked. This does not establish host trust or an automatic invocation.

The pre-publication GitHub snapshot had a default branch named main containing an initial
README, no published CI definition and no finding labels. Lovro then explicitly authorized
commit, push, PR and merge. Initial workflow PR #1 uses the documented bootstrap review
exception; no other member's approval is claimed. The PR and Actions runs record publication
and remote validation. Publish/activation prerequisites are in [PIPELINE](PIPELINE.md);
host-specific hook trust remains to be verified separately.

## T1: mathematical understanding

Work through the coverage in [METHODOLOGY](METHODOLOGY.md), using source sections from
[LITERATURE](../research/LITERATURE.md). Produce readable derivations with stated assumptions
and a small worked example. Distinguish a proved statement from an intuition or empirical
observation. Walk through the notation, objective and update mechanism together.

Complete when the notes are reviewed, gaps are recorded, and all three members can explain
the mathematical argument. Do not mark this complete merely because notes were generated.

## T2: problem and dataset

Compare a small number of concrete candidates on the question they answer, nonnegative
matrix construction, availability/license, manageable size, interpretation and evaluation.
Explain how the concrete problem/data differs from cases in the supplied papers. The team
chooses a candidate and records the decision. No dataset has been selected yet.

Complete with an agreed research question, a source/data description, preprocessing plan,
intended meanings of the factors and a feasible evaluation.

## T3: method and experiment design

Tie the objective and algorithm to the chosen representation and question. Agree rank values,
initializations/seeds, stopping rules, safeguards, baseline, metrics and the compute budget.
Write hypotheses/questions before inspecting the final results. Avoid adding solvers only to
fill a comparison table. Record consequential choices and rejected alternatives in an ADR.

## T4: Python implementation

Implementation details are intentionally postponed. When work starts, add the environment
definition/lock, reusable numerical code and meaningful tests together with the project check
runner and CI commands. Compare behavior with independent small examples and, when useful,
a library implementation using matched settings. Explain differences in objectives/scaling.

## T5: experiments and interpretation

Implement repeatable entry points and preserve provenance. Report reconstruction behavior,
the domain question, stability across the agreed runs and failures/limitations. Trace every
reported table/figure to its generating run. A favorable example alone is insufficient.

## T6: seminar and presentation

Draft sections as understanding develops, then replace placeholders with verified evidence.
Keep notation, algorithm, settings, figures and conclusions aligned with code. Choose source
formats and build commands before claiming either artifact is buildable. Include citations
and distinguish external figures from figures produced by this project.

## T7: final reproduction and walkthrough

Use a fresh environment to reproduce the reported evidence. Check the submission against
the eventual course requirements. Each member practices explaining the full chain from
problem and mathematics to code, results and limitations. Record real verification, remaining
gaps and final artifact locations; do not invent approvals or readiness.
