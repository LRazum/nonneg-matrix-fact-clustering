# Seminar: nenegativna matrična faktorizacija

Seminar iz kolegija **Matrične i tenzorske metode u analizi podataka** izrađuju **Mislav, Sara i
Lovro**. Cilj je detaljno razumjeti matematiku NMF-a, implementirati metodu u Pythonu i
primijeniti je na nov konkretan problem i skup podataka. Svi članovi trebaju razumjeti cijeli
projekt.

Glavni izvor je rad Nicolasa Gillisa *The Why and How of Nonnegative Matrix Factorization*
(main_NNMF-general.pdf). [Pregled literature](docs/research/LITERATURE.md) povezuje svih šest
priloženih radova s ciljevima učenja.

## Trenutačno stanje

Repozitorij sadrži pravila rada, istraživački plan i automatizirane provjere prilagođene
referentnom projektu.

**Tema:** automatsko prepisivanje gitare u note na skupu GuitarSet. Koristimo generaliziranu
KL divergenciju i multiplikativna pravila Leeja i Seunga
([ADR-0003](docs/plan/adr/0003-choose-guitar-transcription-with-kl-nmf.md)).

**Rad je podijeljen na tri niti** ([podjela rada](docs/plan/PODJELA.md)):

- Sara: od snimke do matrice i od nota do $F_1$;
- Lovro: od matrice do faktora;
- Mislav: od faktora do nota.

Svaka nit sadrži matematiku, kod, eksperimente i dio seminara. Repozitorijski zadaci su GitHub issuei
organizirani u milestoneove Faza 0 do Faza 4.

Paket `gitara` postavljen je za Python 3.12. Modul `gitara.nmf` implementira KL i Frobeniusova
multiplikativna ažuriranja, a sintetički testovi provjeravaju ponašanje jezgre. Primjena na
GuitarSetu slijedi. Tim vodi seminar i prezentaciju izvan repozitorija.

Predajemo pisani seminar, prezentaciju, kod i ponovljive rezultate. Seminar, prezentacija i
projektna dokumentacija pišu se na hrvatskom. [Opseg projekta](docs/plan/PROJECT.md),
[matematički i eksperimentalni plan](docs/plan/METHODOLOGY.md) i
[popis zadataka](docs/plan/TASKS.md) povezuju sve dijelove predaje.

## Odakle krenuti

1. Pročitaj [AGENTS.md](AGENTS.md), zajednička pravila za ljude i AI alate.
2. U [kazalu dokumentacije](docs/INDEX.md) pronađi aktualne odluke i istraživačke materijale.
3. Otvori svoj [osobni plan](docs/plan/PODJELA.md) i sljedeći issue iz njega. Radi na zasebnoj
   grani, a PR neka zatvori issue s `Closes #N`. Promjenu pregledava drugi član tima. [Protokol promjena](docs/CHANGE_PROTOCOL.md) opisuje
   koju dokumentaciju treba uskladiti uz pojedinu vrstu promjene.
4. Instaliraj `uv`, postavi okruženje i pokreni lokalne provjere:

```bash
uv sync --locked
python3 tools/check_before_stop.py
```

Završna provjera obuhvaća dokumentaciju, testove alata i projektne provjere, uključujući
sintaksu, uvoz paketa i numeričke testove NMF-a.

Zasebne naredbe, CI i postavljanje lokalnih hookova opisani su u
[tijeku rada i provjera](docs/plan/PIPELINE.md). Postupanje s nalazima i probno pokretanje
dnevne provjere bez pisanja na GitHub opisani su u
[uputama za pregled i nalaze](docs/plan/AI_REVIEW.md). Samo dodavanje datoteka ne postavlja
GitHub postavke, labele ni zaštitu grana i ne objavljuje promjene.
