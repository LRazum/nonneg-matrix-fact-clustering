# Nonnegative matrix factorization seminar

A seminar for **Matrične i tenzorske metode u analizi podataka** by **Mislav, Sara and Lovro**:
understand NMF in mathematical detail, implement it in Python and apply it to a new concrete
problem and dataset. Everyone learns the whole project.

The main source is Nicolas Gillis, *The Why and How of Nonnegative Matrix Factorization*
(main_NNMF-general.pdf). [The literature guide](docs/research/LITERATURE.md) maps all six
supplied papers to the learning goals.

## Current state

The repository contains the working rules, research plan and workflow checks adapted from
the team's reference workflow. The application, dataset, NMF objective/solver and scientific
Python environment are not selected. There is no NMF implementation or experimental result
yet. The deadline, submission formats and individual task allocation are also open.

The deliverables are a written seminar, a presentation, code and reproducible results.
The [project scope](docs/plan/PROJECT.md), [mathematical and experimental plan](docs/plan/METHODOLOGY.md)
and [task list](docs/plan/TASKS.md) connect those deliverables.

## Start here

1. Read [AGENTS.md](AGENTS.md) for the rules shared by people and AI tools.
2. Use [the documentation index](docs/INDEX.md) to locate the current decisions and research.
3. Take one small task from [TASKS](docs/plan/TASKS.md), on its own branch, with another human
   team member reviewing the change. [The change protocol](docs/CHANGE_PROTOCOL.md) explains
   what documentation each kind of change affects.
4. Run the local checks before handover:

```bash
python3 tools/check_before_stop.py
```

Only Python 3.11 or later and Git are needed for the workflow tools; no scientific packages
are needed yet. The checker runs documentation checks and the tools' unit tests, and explicitly
reports the numerical suite as NOT RUN until the implementation environment is agreed.

For the separate commands, CI and host-specific hook setup, see
[PIPELINE](docs/plan/PIPELINE.md). For findings and the read-only daily-audit preview, see
[AI_REVIEW](docs/plan/AI_REVIEW.md). No GitHub settings, labels, publications or branch
protection are created merely by adding these files.
