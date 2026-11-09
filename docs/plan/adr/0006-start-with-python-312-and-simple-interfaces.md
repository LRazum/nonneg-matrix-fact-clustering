# ADR-0006: Uvesti Python 3.12 i jednostavna sučelja među nitima

**Datum:** 2026-11-09 · **Status:** prihvaćeno (Lovro, 2026-11-09)

## Kontekst

Lovro je prenio ishod sastanka Z0. Sara i Mislav usmeno su potvrdili svoje uloge. Dogovoren je
Python 3.12 uz postupno dodavanje ovisnosti. Lovro je zatražio da se sučelja pojednostave.
Organizaciju pisanja tim je riješio zasebno.

## Odluka

1. B1 postavlja osnovu za Python 3.12 i provjere u CI-ju. Ovisnost se dodaje i zaključava uz
   kod koji je prvi koristi. Početna provjera može koristiti postojeći `unittest`.
2. Za svaku snimku koristimo spektrogram `(A, freqs, times)`, klavirsku rolu i isti redoslijed
   tonova `PITCHES`. Neaktivan ton ima nul-stupac u $W$ i nul-redak u $H$. Faktorima se može
   pristupiti po istom indeksu u svakoj podjeli. Cjeloviti ugovor je u
   [zajedničkim sučeljima](../PODJELA.md#zajednička-sučelja).
3. GitHub prati kod, podatke, provjere i rezultate pokretanja. Tim zasebno vodi pisanje i
   pregled materijala za predaju prema [ADR-0005](0005-write-seminar-and-slides-on-overleaf.md).

## Obrazloženje

Fiksni redoslijed tonova omogućuje izravnu usporedbu predložaka između podjela i jednostavno
pretvaranje aktivacija u note. Obrada po snimci ograničava veličinu privremenih matrica.
Postupno dodavanje ovisnosti veže svaku novu ovisnost uz konkretnu potrebu u kodu.

## Odbačene mogućnosti

- Unaprijed instalirati cijeli popis iz prijedloga za Z0. Dio paketa može ostati neiskorišten.
- Uklanjati pa ponovno umetati neaktivne tonove oko svakog poziva jezgre. To bi tražilo
  usklađivanje indeksa na više mjesta.
- Odmah propisati poseban format predmemorije i različite tipove podataka na disku i u izračunu.
  Za prvi prolaz dovoljan je izračun po snimci.

## Posljedice

B1 priprema okruženje, a A1, A2, B2, C2 i C3 koriste ugovore iz podjele rada. B2 testira
nulte komponente i prijavljuje nevaljanu rekonstrukciju. C2 testira vremenske rubove i nulte
aktivacije. Odabir metode učenja predložaka, parametara STFT-a i hiperparametara ostaje u
pripadajućim zadacima.

## Dodatak 2026-11-09: početno okruženje B1

Za postavljanje Python projekta i zaključavanje ovisnosti koristimo `uv`. Paket se gradi
pomoću `uv_build` i na početku nema radnih ovisnosti. `unittest` služi za testove, a
`compileall` za provjeru sintakse. Naredbe su u [tijeku rada](../PIPELINE.md).
