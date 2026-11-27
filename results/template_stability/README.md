# B6: stabilnost predložaka naučenih s maskom

Predlošci naučeni s maskom na 12 snimki (po jedna za svaki par gitarista i načina), u 6
foldova i iz 3 sjemena, za KL i Frobenius, `tol` $10^{-4}$. Do spajanja C3 uči ih zamjenska
funkcija `learn_masked`. Datoteke su napravljene naredbama:

```bash
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 uv run python -m experiments.template_stability
uv run python -m experiments.template_stability --publish results/runs/20261127T144648Z-template_stability-7a9d17
```

Pokretanje `20261127T144648Z-template_stability-7a9d17` (commit `c32cd53`, čisto radno stablo).

- `results/template_stability/summary.json`: zapis pokretanja bez lokalnih putanja, sa sličnostima po tonu kroz sjemena i
  kroz foldove. Naučeni predlošci (datoteka templates.npz) ostaju u lokalnoj mapi pokretanja.
- `results/template_stability/template_stability.png`: srednja kosinusna sličnost predloška istog tona kroz sjemena
  (medijan po foldovima) i kroz foldove (prvo sjeme), po MIDI visini.

Uzorak uključuje sve gitariste, jer svaki fold izostavlja drugog; ništa iz njega ne služi za
odabir parametara. Tumačenje je u [planu B6](../../docs/plan/podjela/b-lovro.md).
