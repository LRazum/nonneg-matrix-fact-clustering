# B5: konvergencija na stvarnim spektrogramima

Datoteke u ovoj mapi potječu iz pokretanja `20261126T081632Z-convergence-f0a504`
(commit `df7d34b`, čisto radno stablo). Napravljene su naredbama:

```bash
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 uv run python -m experiments.convergence
uv run python -m experiments.convergence --publish results/runs/20261126T081632Z-convergence-f0a504
```

- `results/convergence/summary.json`: zapis pokretanja bez lokalnih putanja (konfiguracija, okruženje, MD5 manifesta
  podataka i sažetak svakog pokretanja). Povijesti funkcije cilja ostaju u lokalnoj mapi
  pokretanja unutar results/runs/, u datoteci curves.json.
- `results/convergence/unsupervised.png`, `results/convergence/masked.png` i
  `results/convergence/transcription.png`: funkcija cilja i relativni pad po
  iteraciji za KL i Frobenius, za tri vrijednosti ε i tri sjemena.

Postavke, tumačenje i prijedlog za Z2 opisani su u
[metodologiji](../../docs/plan/METHODOLOGY.md), odjeljak 2.3.
