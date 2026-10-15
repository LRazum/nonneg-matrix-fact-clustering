# ADR-0001: Study and implement NMF with whole-project understanding for all three members

**Date:** 2026-10-15 · **Status:** accepted (scope specified by Lovro, 2026-10-15)

## Context

The course is Matrične i tenzorske metode u analizi podataka. Mislav, Sara and Lovro work on a
seminar together. Six research papers were supplied; Lovro identified Gillis's
main_NNMF-general.pdf as the main required source and NMF as the central method.

## Decision

1. Learn the theory with detailed mathematical reasoning, understand a numerical method,
   implement it in Python and apply it to a new concrete problem and dataset.
2. A new concrete case in a domain already mentioned by the papers is sufficient; another
   domain is also possible. A new NMF algorithm is not required.
3. Deliver a written seminar, presentation, code and experimental results.
4. Every member learns the mathematics, algorithm, data, implementation and interpretation.
   Do not divide long-term knowledge ownership by subject. Task allocation is decided later.
5. Application, dataset, objective/solver, dependencies, document formats and deadline remain
   open. The workflow setup does not select or implement the scientific method.

## Why

The learning objective is to understand a method deeply enough to implement, explain and
evaluate it. Mathematical derivations and reproducible evidence support that understanding.
All three members need to explain the same complete project.

## What was rejected

- A mathematical treatment limited to the NMF definition: Lovro explicitly requested more depth.
- Permanent mathematics/code/experiment ownership by different members: Lovro explicitly
  requires everyone to know the entire project.
- Treating document clustering or rank-2 hierarchy as already required: NMF is the main
  method and the application is still open.
- Selecting implementation details during workflow setup: the team will agree these later.

## Consequences

The scope is reflected in `AGENTS.md`, `docs/plan/PROJECT.md`, `docs/plan/TASKS.md`,
`docs/plan/METHODOLOGY.md` and `docs/research/LITERATURE.md`. Future decisions need to preserve
whole-project learning and connect mathematics, code and experimental interpretation.
