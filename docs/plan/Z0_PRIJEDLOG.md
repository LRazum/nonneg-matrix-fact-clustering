# Prijedlog odluka za sastanak Z0 (#5)

**Pripremio:** Lovro, 2026-11-05 · **Status:** prijedlog za raspravu, a ne odluka.

Ova stranica priprema sastanak Z0 iz [podjele rada](PODJELA.md). Za svako otvoreno pitanje daje
konkretan prijedlog i obrazloženje, kako AGENTS.md traži prije odluke tima. Odluke sa sastanka
zapisujemo u issue #5, a važne i u ADR. Nakon toga ova stranica postaje povijesni zapis
prijedloga.

Neki prijedlozi spominju opažanja iz Lovrine lokalne probe od 2026-11-04. Proba nije dio
repozitorija i njezini brojevi nisu rezultati projekta. Ovdje služe samo kao upozorenje na
mjesta koja treba provjeriti.

## Sažetak: što treba odlučiti

| # | Pitanje | Prijedlog | Odlučuju |
|---|---|---|---|
| 1 | Raspodjela niti i osobni planovi | Potvrditi ADR-0003, ADR-0004 i planove; izmjene unijeti u jedan PR nakon Z0 | Sara i Mislav potvrđuju |
| 2 | Zajednička sučelja | Potvrditi [sučelja](PODJELA.md) uz pet izmjena iz odjeljka 2 | svi |
| 3 | Python okruženje | Python 3.12, `numpy`, `scipy`, `matplotlib`; razvojno `pytest`, `mir_eval`, `ruff`; `uv` i `uv.lock` | svi; provodi B1 (#6) |
| 4 | Seminar i prezentacija | Overleaf, odvojeno od GitHuba (Lovrina odluka); LuaLaTeX, zajedničke oznake i literatura, Beamer; veza slika i brojeva s pokretanjima | svi |
| 5 | Rok i raspored faza | Termin dobivamo u tjednu od 2026-11-09, a rok zatim određujemo sami; faze se raspoređuju unatrag od roka | svi |
| 6 | GitHub korisnik `phantom5470` | Mislav potvrđuje da je njegov | Mislav |

## Dnevni red (oko 60 minuta)

1. Planovi i raspodjela niti, 10 min.
2. Zajednička sučelja, 15 min.
3. Okruženje i ovisnosti, 10 min.
4. Seminar i prezentacija na Overleafu, 10 min.
5. Rok, raspored faza i rezervni rezovi, 10 min.
6. Lokalno postavljanje i sljedeći koraci, 5 min.

Prije sastanka svatko pročita svoj osobni plan, ovu stranicu i odjeljak
[„Zajednička sučelja”](PODJELA.md#zajednička-sučelja).

## 1. Planovi i raspodjela niti

- Sara i Mislav potvrđuju [ADR-0003](adr/0003-choose-guitar-transcription-with-kl-nmf.md),
  [ADR-0004](adr/0004-divide-work-into-end-to-end-threads.md) i svoje planove
  ([plan A](podjela/a-sara.md), [plan C](podjela/c-mislav.md)) ili traže izmjene.
- Mislav potvrđuje GitHub korisnika `phantom5470`. O tome ovise `.github/CODEOWNERS` i
  dodjela issuea.
- **Prijedlog:** sve izmjene planova, sučelja i issuea sa sastanka unose se u jedan PR nakon
  Z0. Taj PR pregledava netko tko nije Lovro.

## 2. Zajednička sučelja: potvrditi uz pet izmjena

Sučelja iz [podjele rada](PODJELA.md) predlažem potvrditi uz izmjene ispod. Prva izmjena
rješava stvaran sukob među planovima; ostale fiksiraju dogovore o kojima ovisi više niti.

### 2.1 Neaktivni tonovi: sukob između B2, C2 i C3

**Problem.**

- B2 (plan B, korak 6): `fit` izaziva `ValueError` ako $W_0$ ima nul-stupac.
- C3 (plan C, korak 2): ton bez ijednog označenog okvira dobiva nul-stupac u $W$.
- C2 (plan C, korak 1): transkripcija poziva `fit` s tim $W$ i `update_W=False`, pa bi svaka
  transkripcija pala čim postoji neaktivan ton.
- Pri učenju je za takav ton nazivnik pravila za $W$, $\sum_b\mathbf 1H_b^T$, jednak nuli, a
  normalizacija stupca od $W$ dijelila bi nulom.

To nije rubni slučaj. U probi su zaokružene visine iz anotacija bile u rasponu MIDI 40–81, a
`PITCHES` je 40–88. Ako A4 to potvrdi, barem sedam tonova nema okvira za učenje.

**Prijedlog.**

1. `fit` ostaje strog. Izaziva `ValueError` ako $W_0$ ima nul-stupac, a uz `update_W=True` i
   ako je neka komponenta nula u svim $H_{0,b}$. Docstring navodi zašto: pravilo i teorem
   pretpostavljaju $W$ bez nul-stupca i $H$ bez nul-retka (L3, teorem 2).
2. Komponenta koja tijekom iteracija postane nula ostaje nula. `fit` je zapisuje u `inactive`,
   a normalizacija nul-stupce preskače.
3. Pozivatelji uklanjaju neaktivne komponente prije poziva i vraćaju ih nakon njega:
   - `templates.learn_templates` uči samo tonove s označenim okvirima i vraća $W$ oblika
     $(m, K)$ ili $(m, K+1)$, s nul-stupcima za neaktivne tonove i popisom `inactive`;
   - `transcribe.activations` poziva `fit` samo sa stupcima koji nisu nula i vraća $H$ oblika
     $(K, n)$, s nul-retcima za neaktivne tonove.
4. Testovi: B2 testira obje pogreške, a C2 i C3 testiraju umetanje nul-stupaca i nul-redaka.

Tako indeksi uvijek prate `PITCHES`, a nijedna funkcija ne dijeli nulom prešutno.

### 2.2 Vremenska os spektrograma

C2 iz `times` računa početke nota, A5 ih uspoređuje s anotacijama, a A4 mjeri pomak anotacija.
Konvencija mora biti ista svugdje, pa je predlažem fiksirati sada, a ne tek u A2:

- STFT dopunjuje signal nulama za $N/2$ uzoraka na oba ruba, pa je središte okvira $t$ u
  `times[t]` $= t\cdot\texttt{hop}/f_s$ i `times[0]` $=0$;
- nota počinje u `times` prvog aktivnog okvira i završava u `times` prvog neaktivnog okvira;
  za zadnji okvir dodaje se jedan korak.

Ako A4 izmjeri sustavan pomak, ispravak je zaseban, izričit i zapisan korak.

### 2.3 Normalizacija razine je zaseban korak

Odluka o normalizaciji ostaje u A4. Sučelje predlažem već sada:

- `spectrogram.stft_magnitude` nikad ne normalizira;
- normalizacija je zasebna funkcija, npr. `spectrogram.normalize_level(A) -> (A_scaled, c)`.
  Vraća i faktor $c$, a eksperimenti ga zapisuju u konfiguraciju pokretanja.

U probi su se razine pojedinih gitarista razlikovale za oko 10 dB, pa će odluka vjerojatno
biti potrebna. Treba je obrazložiti homogenošću iz A3.

### 2.4 Tip podataka i memorija

Svi spektrogrami u probi imali su oko 470 000 okvira i oko 500 binova. U `float64` to je oko
1,9 GB, a skup za učenje jednog vanjskog folda oko 1,6 GB.

- Spektrogram u predmemoriji (mapa data/processed/, izvan Gita) sprema se kao `float32`.
- Svi izračuni rade u `float64`, ali po jednom bloku.
- `fit` prima niz blokova i nikad ih ne spaja niti trajno kopira. Blok smije biti `numpy.memmap`.
- Sučelje „spektrogram je `float64` oblika `(m, n)`” vrijedi za izračun. Za predmemoriju na
  disku vrijedi gornje pravilo.

### 2.5 Note i žice

`data.load_notes` vraća `(intervals, pitches, strings)`. Svi ostali moduli primaju samo par
`(intervals, pitches)`. Žica treba samo analizi pogrešaka (C6). Treba to dopisati u odjeljak
„Dogovori o podacima”.

## 3. Python okruženje i ovisnosti

| Što | Prijedlog | Zašto |
|---|---|---|
| Python | 3.12 (datoteka .python-version i `requires-python = ">=3.12"`) | Aktualni `numpy` i `scipy` traže barem 3.12; `uv` instalira Python ako ga nema |
| Ovisnosti | `numpy`, `scipy`, `matplotlib` | Zvuk čita `scipy.io.wavfile`, preuzorkovanje `scipy.signal.resample_poly`, JAMS se parsira kao JSON, sparivanje radi `scipy.sparse.csgraph`; zato ne trebaju `librosa`, `soundfile` ni `jams` |
| Razvojne ovisnosti | `pytest`, `mir_eval`, `ruff` | `pytest` za numeričke testove; `mir_eval` samo kao neovisna provjera A5; `ruff check` kao statička provjera iz AGENTS.md, odjeljak 5 |
| Zaključavanje | `uv` i `uv.lock`; CI izvodi `uv sync --frozen` | Isti brojevi na svim računalima; potrebno za Z4 |
| Testovi alata | ostaju `unittest` u `tools/` | Rade bez okruženja, kao i dosad |

**Provjera 2026-11-05.** Lovro je naredbom `uv pip compile` za Python 3.12 razriješio ove
ovisnosti. Dobivene su verzije `numpy` 2.5.4, `scipy` 1.18.1, `matplotlib` 3.11.2,
`mir_eval` 0.8.2 i `pytest` 9.2.0. Ništa nije instalirano ni pokrenuto. `mir_eval` 0.8.2
izdan je u veljači 2025., pa B1 mora provjeriti radi li s aktualnim `numpy`. Ako ne radi,
A5 se oslanja samo na ručno izračunate primjere, a to treba zapisati.

**Na sastanku svatko navede:** operacijski sustav, RAM i ima li `uv`. O tome ovisi broj
paralelnih procesa (C4).

Varijable dretvi (`OPENBLAS_NUM_THREADS`, `OMP_NUM_THREADS`, `MKL_NUM_THREADS`) postavljaju se
na 1 kad se pokreće više procesa istodobno. B1 to zapisuje u PIPELINE.md.

## 4. Seminar i prezentacija na Overleafu

**Odluka (Lovro, 2026-11-05; [ADR-0005](adr/0005-write-seminar-and-slides-on-overleaf.md)):** seminar i prezentacija pišu se
na Overleafu, potpuno odvojeno od GitHuba. Repozitorij sadrži kod, testove, eksperimente, opis podataka i rezultate.

**Što je to promijenilo u postojećim planovima** (provedeno u istom PR-u kao ADR-0005):

- Mape seminar/ i presentation/ neće postojati. Uklonjene su iz planirane strukture u
  AGENTS.md, [tijeku rada](PIPELINE.md), popisu `PLANNED` u `tools/check_docs.py` i osobnim
  planovima.
- Neovisna provjera dokaza (A9, B9 i C9) pretpostavljala je PR. Sada recenzent komentira
  izravno u Overleafu, a sažetak nejasnoća i ishod zapisuje u issue zadatka, jer GitHub ne
  vidi Overleaf.
- Pravilo 8 iz AGENTS.md i dalje vrijedi: svaki broj i slika u seminaru povezani su s
  pokretanjem:
  - `matplotlib` sprema slike kao PDF u `results/`, s identifikatorom pokretanja u nazivu, i
    takve se učitavaju na Overleaf;
  - brojevi u tablicama prepisuju se iz JSON-a pokretanja, a u izvoru seminara uz tablicu
    stoji komentar s identifikatorom pokretanja.
- Z5 (usklađivanje oznaka) sada ručno uspoređuje Overleaf i kod.

**Prijedlog za Overleaf projekte:**

| Što | Prijedlog |
|---|---|
| Projekti | Dva projekta, seminar i prezentacija; sve troje su urednici. Provjeriti dopušta li naš Overleaf plan ili fakultetska licenca tri urednika |
| Struktura seminara | Glavna datoteka i poglavlja po nitima (`a-*.tex`, `b-*.tex`, `c-*.tex`, `z-*.tex`). Overleaf dopušta istodobno uređivanje, ali odvojene datoteke smanjuju preklapanje i olakšavaju pregled |
| Prevoditelj | LuaLaTeX (izbornik projekta), jer skripta već koristi `fontspec` i `unicode-math`; `babel` s hrvatskim jezikom |
| Oznake | Zajednička datoteka makronaredbi oznake.tex (npr. $A$, $W$, $H$, $D(\cdot\,\|\,\cdot)$). Prezentacija koristi istu datoteku, povezanu iz projekta seminara ili kopiranu; to provjeriti u Overleafu |
| Literatura | Jedna datoteka literatura.bib u projektu seminara, ista u prezentaciji |
| Prezentacija | Beamer |
| Predaja | Pri predaji izvesti PDF i izvorni kod oba projekta, jer povijest Overleafa nije u Gitu |

Ako kolegij propisuje predložak, opseg ili trajanje izlaganja, to ima prednost pred ovim
prijedlogom.

## 5. Rok, raspored i rezervni rezovi

Prema Lovri, termin dobivamo u tjednu od 2026-11-09, a rok nakon toga određujemo sami. Do
tada milestonei nemaju datume.

**Prijedlog:** kad dobijemo termin, odmah odrediti rok $D$ i rasporediti faze unatrag od njega.
Uz termin treba provjeriti propisuje li kolegij trajanje izlaganja, opseg ili predložak
seminara, način predaje koda i pravila o uporabi AI alata. Prijedlog udjela, uz pretpostavku
od oko devet tjedana:

| Faza | Trajanje | Završava |
|---|---|---|
| 0: dogovor | 1 tjedan | $D-8$ tjedana |
| 1: temelji i prva faktorizacija | 2 tjedna | $D-6$ tjedana |
| 2: cijeli lanac na jednoj podjeli | 2 tjedna | $D-4$ tjedna |
| 3: svi rezultati, seminar i slajdovi | 2–3 tjedna | $D-1,5$ tjedana |
| 4: reprodukcija i probna obrana | 1–1,5 tjedana | $D$ |

Ako je vremena manje, predlažem unaprijed dogovoriti što se reže i kojim redom, umjesto da se
reže prešutno na kraju:

1. **Prvo se reže:** sporedna mjera s krajem note; drugi način učenja predložaka (ostaje samo
   maskirani NMF ili samo prosjek spektara, prema C3); ispitivanje osjetljivosti STFT-a svodi
   se na jednu alternativu.
2. **Zatim:** stabilnost kroz sjemena u B6 svodi se na tri sjemena; analiza pogrešaka u C6
   svodi se na oktavne pogreške i polifoniju.
3. **Ne reže se:** KL metoda, obje referentne metode (Frobenius i vrhovi), svih šest vanjskih
   podjela, ugniježđen izbor hiperparametara, dokazi iz niti A, B i C te reprodukcija u Z4.

## 6. Lokalno postavljanje i sljedeći koraci

Svatko prije ili na sastanku:

- klonira repozitorij i pokrene `python3 tools/check_before_stop.py`;
- ako koristi AI alat, provjeri da mu je Stop hook pouzdan: `.claude/settings.json` za Claude
  Code ili `.codex/hooks.json` za Codex (vidi [tijek rada](PIPELINE.md));
- pročita Dio I [skripte](../research/skripta-gitara/skripta-gitara.pdf) i L1, odjeljke 1–2.

Nakon sastanka:

1. Odluke se zapisuju u issue #5 i kvačice se ažuriraju.
2. Lovro otvara PR s izmjenama podjele rada i osobnih planova te ažurira issuee #10, #14 i #21
   prema odjeljku 2.1.
3. Lovro počinje B1 (#6) na grani `lovro/b1-okruzenje`. Isti PR dodaje ADR-0006 o okruženju.
4. Kad je rok poznat, milestonei dobivaju datume.
5. Sara i Mislav mogu odmah početi A3 i C1 (matematika) te A5 i C2 (kod na umjetnim podacima).
   Kod se može spojiti tek nakon B1.
