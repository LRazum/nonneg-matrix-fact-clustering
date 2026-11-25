# Podaci: GuitarSet 1.1.0

Projekt koristi **GuitarSet 1.1.0**, skup snimki akustične gitare s notama označenim pomoću
heksafonskog pickupa (zaseban signal za svaku žicu).

- Izvor: Zenodo, zapis 3371780, DOI [10.5281/zenodo.3371780](https://doi.org/10.5281/zenodo.3371780)
- Citat: Q. Xi, R. Bittner, J. Pauwels, X. Ye, J. P. Bello, *GuitarSet: A Dataset for Guitar
  Transcription*, 19th International Society for Music Information Retrieval Conference
  (ISMIR), Pariz, 2018.
- Licencija: [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). Smijemo koristiti i
  objavljivati izvedene rezultate uz navođenje izvora. Sirove datoteke ipak ne stavljamo u Git
  zbog veličine i pravila repozitorija.
- Datum pristupa i provjere zapisa na Zenodu: 2026-11-14.

## Što koristimo

Od pet arhiva na Zenodu trebaju nam dvije:

| Arhiva | Veličina (B) | MD5 | Sadržaj |
|---|---:|---|---|
| `annotation.zip` | 39 132 574 | `b39b78e63d3446f2e54ddb7a54df9b10` | 360 × .jams (JSON): note, akordi, ritam, tonalitet |
| `audio_mono-mic.zip` | 656 927 981 | `275966d6610ac34999b58426beb119c3` | 360 × `_mic.wav`: snimka mikrofona, mono, 16 bita, 44 100 Hz |

Koristimo snimku mikrofona, a ne pickupa, jer ona odgovara stvarnoj primjeni.

## Preuzimanje i provjera

Iz korijena repozitorija:

```bash
uv run python -m gitara.data download
```

Naredba preuzima arhive u mapu data/raw/ (izvan Gita), provjerava veličinu i MD5, raspakirava ih i provjerava
da postoji 360 uparenih snimki (6 gitarista × 2 načina × 30). Zatim uspoređuje svaku datoteku
s manifestom `data/manifest.csv`. Arhiva koja je već preuzeta i ispravna ne preuzima se ponovno.
Zenodo ne podržava nastavak prekinutog preuzimanja, pa se datoteka uvijek preuzima cijela.

Manifest sadrži putanju, veličinu i MD5 svih 720 datoteka. Napravljen je naredbom
`uv run python -m gitara.data manifest` na podacima provjerenim prema gornjim MD5
vrijednostima. Zapis pokretanja (`gitara.provenance`) bilježi MD5 manifesta.

## Struktura i što je u Gitu

```text
data/
  README.md          u Gitu: ovaj opis
  manifest.csv       u Gitu: veličina i MD5 svake datoteke
  raw/               izvan Gita (.gitignore)
    annotation.zip, audio_mono-mic.zip
    annotation/<track_id>.jams
    audio_mono-mic/<track_id>_mic.wav
```

Naziv snimke, npr. `00_BN1-129-Eb_comp`, sadrži gitarista (00–05), stil i progresiju (BN, Funk,
Jazz, Rock ili SS s 1–3), tempo, tonalitet i način (`comp` ili `solo`).

## Što smo provjerili na podacima

Provjere su pokrenute modulom `gitara.data` na grani `sara/a1-podaci` (2026-11-15 i 2026-11-23).

- Svih 360 snimki i anotacija učitava se bez pogreške. Svaka anotacija ima točno šest
  `note_midi` anotacija, po jednu za svaku žicu. Žica je zapisana u
  `annotation_metadata.data_source` kao tekst `"0"` (debela E žica) do `"5"` (tanka e žica).
- Ukupno ima **62 476 nota**, isto kao u opisu skupa. Visine su od 39,79 do 80,98 MIDI
  (necijele, izmjerene iz zvuka), a trajanja od 0,029 do 4,0 s.
- Svaka WAV datoteka je mono, 16-bitna i 44 100 Hz, a njezino trajanje jednako je trajanju u
  JAMS-u (`file_metadata.duration`).
- Nakon preuzorkovanja na 22 050 Hz najveća apsolutna vrijednost uzorka je 1,002. Barem
  jedna snimka u izvorniku vjerojatno doseže najveću vrijednost (clipping); provjerava se u A4.
- Najveće vrijednosti snimki razlikuju se oko 17 puta (oko 25 dB); najtiša je
  `00_Funk3-98-A_solo` s vrhom 0,058. To je ulaz za odluku o normalizaciji razine u A4.

## Poznate greške i postupanje

Prijedlog postupanja čeka potvrdu tima u
[issueu #7](https://github.com/LRazum/nonneg-matrix-fact-clustering/issues/7).
`gitara.data` učitava podatke onakve kakvi jesu i ništa ne ispravlja prešutno.

1. **Konstantan pomak anotacija** ([marl/GuitarSet#5](https://github.com/marl/GuitarSet/issues/5)):
   `04_BN3-154-E_comp` (+0,409 s) i `04_Jazz1-200-B_comp` (+0,309 s). Pomak je višestruko veći
   od tolerancije početka note od 50 ms. *Prijedlog:* obje snimke izostaviti iz učenja i
   vrednovanja; gitaristu 4 ostaje 58 snimki.
2. **Ista nota na dvije žice s početkom unutar 50 ms**: 160 parova, gotovo uvijek na susjednim
   žicama. Dio su stvarni unisoni u akordima, a dio vjerojatno preslušavanje pickupa, uključujući
   prijavljeni duplikat u `02_Funk2-119-G_comp` (žice 1 i 2,
   [marl/GuitarSet#4](https://github.com/marl/GuitarSet/issues/4)). Na klavirsku rolu nema
   utjecaja; odziv na razini nota ograničava za najviše 160/62 476 ≈ 0,26 %. *Prijedlog:*
   zadržati i navesti u seminaru.
3. **Preklapanje od jednog uzorka (1/44 100 s) na istoj žici**: 7 parova, zaokruživanje alata za
   anotaciju. *Prijedlog:* ne mijenjati; provjere preklapanja koriste toleranciju od 1 ms.
