# B6: nejedinstvenost i stacionarnost bez nadzora

NMF bez nadzora snimke `00_BN1-129-Eb_comp` ($511\times962$, $r=49$) iz 10 sjemena, za KL i
Frobenius. Datoteke su napravljene naredbama:

```bash
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 uv run python -m experiments.stability
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 uv run python -m experiments.stability --tol 0 --max-iter 2000
uv run python -m experiments.stability --publish results/runs/20261127T142405Z-stability-0153e3
uv run python -m experiments.stability --publish results/runs/20261127T143014Z-stability-bc26ec --out results/stability/control
```

- Ova mapa: pokretanje `20261127T142405Z-stability-0153e3` (commit `c32cd53`, čisto radno
  stablo), `tol` $10^{-4}$, najviše 2000 iteracija.
- `results/stability/control/`: kontrola ranog zaustavljanja, pokretanje
  `20261127T143014Z-stability-bc26ec` (isti commit), `tol=0` i točno 2000 iteracija.

U svakoj od dviju mapa:

- `results/stability/summary.json`, odnosno `results/stability/control/summary.json`: zapis pokretanja bez lokalnih putanja (konfiguracija, okruženje, MD5
  manifesta podataka, završne vrijednosti, stacionarnost i sparivanje po svim parovima).
- `results/stability/stability.png` (i u `results/stability/control/`): kosinusna sličnost stupaca od $W$ svakog sjemena s prvim sjemenom nakon
  Hungarian sparivanja, poredana po veličini; isprekidana crta je prosjek bez sparivanja.
  Prvo sjeme je proizvoljna referenca; svi parovi su u zapisu (`pairwise`).
- `results/stability/activations.png` (i u `results/stability/control/`): aktivacije prvog KL sjemena uz klavirsku rolu iste snimke (za Z1).

Tumačenje je u [planu B6](../../docs/plan/podjela/b-lovro.md).
