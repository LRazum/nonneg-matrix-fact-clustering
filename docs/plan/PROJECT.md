# Seminar scope and deliverables

## Agreed purpose

Course: **Matrične i tenzorske metode u analizi podataka**.
Team: **Mislav, Sara and Lovro**. Every member must understand the entire project.

Study NMF using Nicolas Gillis, *The Why and How of Nonnegative Matrix Factorization*, as the
main required source. Develop the mathematics beyond an introductory definition, understand
the chosen numerical method, implement it in Python and use it on a new concrete problem and
dataset. A familiar domain with a different concrete problem/data is acceptable. A new domain
is possible too; algorithmic research novelty is not required.

These requirements were given by Lovro on 2026-10-15. See
[ADR-0001](adr/0001-seminar-scope-and-shared-understanding.md). Do not infer that the other
members have approved a specific dataset, solver or workflow review.

## Deliverables and current state

| Deliverable | Required content | Current state |
|---|---|---|
| Written seminar | Motivation, detailed mathematics, algorithm, data/methodology, experiments, interpretation, limitations and references | Planned; format/language/length open |
| Presentation | A coherent explanation of the same model, method, evidence and conclusions | Planned; format/duration open |
| Python code | The agreed NMF method, meaningful checks and a documented reproducible run | Planned; objective/solver/dependencies open |
| Results | Traceable numerical and domain evidence, figures/tables and honest limitations | Planned; no experiments performed |

## Whole-project understanding

Tasks can have a temporary lead and a different reviewer. They must not create a mathematics
specialist who alone understands the derivation or a coding specialist who alone can run the
project. Individual assignments and the exact rotation will be decided later.

At milestones, use a walkthrough across mathematics, algorithm, data, code and interpretation.
Any member should be able to explain:

1. What the rows/columns of the input matrix mean and why its representation is nonnegative.
2. What the rank and factors mean, and what is ambiguous or not identifiable.
3. What the objective optimizes and how the implemented updates follow from it.
4. Which claims about optimality/convergence are justified and under what assumptions.
5. How to reproduce a run, interpret the reported metrics and explain a limitation/failure.

Record actual questions and remaining gaps in the task or handover. A checklist is a prompt
for a real discussion, not evidence that the discussion happened. Each person confirms their
own understanding; an AI tool cannot certify it.

## Decisions still open

- Concrete application, research question, dataset, access and redistribution conditions.
- Objective, solver, initialization, numerical safeguards, stopping rule and rank selection.
- Scientific Python dependencies, supported version, environment and library reference.
- Appropriate baseline, domain metrics and experiment budget.
- Seminar and presentation format, language, length/duration, rubric and deadline.
- Individual task allocation; Mislav's and Sara's GitHub handles and access.
- GitHub branch-protection availability and host-specific hook trust/activation.

Prepare evidence and a proposal for substantive choices, then record an agreed choice in an
ADR and update the affected documents. The setup task does not settle these choices.

## Scope boundaries

NMF is the central method. Document clustering, topic modeling and rank-2 hierarchical NMF
are possible applications/extensions from the literature, not mandatory implementations.
Tensor methods are part of the course name, not an additional project requirement supplied
by the user. No web product, deployment pipeline or production service is currently needed.
