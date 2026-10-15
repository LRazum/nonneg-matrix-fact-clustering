# Decision records

An architecture decision record (ADR) captures one material project decision, the evidence and
why alternatives were rejected. Here that includes scientific methodology as well as repository
workflow. `docs/INDEX.md` lists the records; `docs/CHANGE_PROTOCOL.md` explains when one is needed.

## File name and format

Use the next free four-digit number, followed by a short lowercase title with hyphens. Numbers
are never reused. For example:

```text
docs/plan/adr/0003-choose-application-and-dataset.md
```

Use this structure, in this order:

```markdown
# ADR-NNNN: A title that states the decision

**Date:** YYYY-MM-DD · **Status:** proposed

## Context
Facts, requirements, evidence and open questions.

## Decision
The concrete choice and its scope. State what remains open.

## Why
Reasons and evidence, with source locations where relevant.

## What was rejected
Considered alternatives and the actual reason for rejecting each.

## Consequences
Affected rules, plan, code, tests, experiments and deliverables.
```

Use `###` for subdivisions. The documentation check validates the record structure; people
review whether the reasoning and evidence are sound.

## Status and decision authority

- `proposed`: prepared for discussion; dependent implementation waits if the choice is required.
- `accepted (<who>, YYYY-MM-DD)`: name only the people who actually decided and the date.
- `superseded by ADR-NNNN`: a replacement record explains the new decision and links back.

An accepted workflow requested by Lovro does not mean Mislav or Sara have approved it.
Scientific choices still open in `docs/plan/PROJECT.md` stay open until genuinely discussed
and recorded. Write unknown facts as open questions; never invent dataset access, a solver
choice, an experiment result or a person's approval to complete the template.

## Later changes

Preserve decision history. Add a compatible clarification at the end:

```markdown
## Addendum YYYY-MM-DD: what changed
```

For a replacement, create a new ADR, mark the old one superseded and state the replacement in
its Context. Do not delete the old record or rewrite its rejected alternatives as if the new
decision had always applied. Update all affected documents in the same change.
