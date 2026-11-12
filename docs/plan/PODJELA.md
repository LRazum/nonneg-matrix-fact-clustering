# Podjela rada: tri niti

Raspored niti prihvaćen je u [ADR-0004](adr/0004-divide-work-into-end-to-end-threads.md),
a tema u [ADR-0003](adr/0003-choose-guitar-transcription-with-kl-nmf.md). Ova stranica je
zajednički plan. Detaljni koraci za svaku osobu nalaze se u osobnim planovima. Prema Lovrinoj
primopredaji, Sara i Mislav usmeno su potvrdili svoje uloge na Z0. Materijale za predaju i
raspored tim vodi zasebno.

## Tko je tko

| Osoba | Član | GitHub | Nit | Pregledava nit | Osobni plan |
|---|---|---|---|---|---|
| A | Sara | `@saragrguric` | A: od snimke do matrice i od nota do $F_1$ | B | [plan A](podjela/a-sara.md) |
| B | Lovro | `@LRazum` | B: od matrice do faktora | C | [plan B](podjela/b-lovro.md) |
| C | Mislav | `@phantom5470` | C: od faktora do nota | A | [plan C](podjela/c-mislav.md) |

Svaka nit ima nositelja, a ne vlasnika. Svatko radi matematiku, piše kod i testove, provodi
eksperimente te piše svoj dio seminara i prezentacije. Na kraju svatko mora moći objasniti
cijeli projekt, a ne samo svoju nit.

## Što koja nit radi

| | A: Sara | B: Lovro | C: Mislav |
|---|---|---|---|
| **Matematika** | Ton i harmonici; DFT, prozor i spektrogram; približna aditivnost spektara. KL divergencija: definicija, nenegativnost, homogenost, Poissonova izglednost, usporedba s Frobeniusovom normom. Definicija $F_1$ preko sparivanja | Gradijenti; uvjeti optimalnosti (KKT) na nenegativnom ortantu. Izvod multiplikativnih pravila iz skaliranog gradijentnog koraka; dokaz nerasta pomoćnom funkcijom (L3, teorem 2). Praktični detalji: ε, zaustavljanje, složenost | Model $A\approx WH$ i usporedba sa SVD-om; nejedinstvenost i normalizacija; nekonveksnost punog problema i konveksnost po $H$. Što je, a što nije dokazano o konvergenciji. Maskirani NMF; pravila za note iz aktivacija |
| **Kod** | `gitara.data`, `gitara.spectrogram`, `gitara.evaluate`, `gitara.peaks` | Okruženje i CI, `gitara.nmf`, `gitara.provenance` | `gitara.transcribe`, `gitara.templates`, pokretač unakrsne provjere |
| **Eksperimenti** | Provjera pretprocesiranja; osjetljivost na parametre STFT-a; metoda spektralnih vrhova | Ponašanje algoritma na stvarnim podacima; konvergencija KL i Frobeniusa; stabilnost kroz sjemena | Glavni eksperiment sa šest podjela; usporedba metoda; analiza pogrešaka |
| **Seminar** | Problem, od zvuka do matrice, funkcija cilja, podaci, mjere uspjeha | Uvjeti optimalnosti, multiplikativna pravila, dokaz nerasta, praktični detalji | Model i struktura, jamstva, primjena, rezultati i rasprava |
| **Prezentacija** | Slajdovi za svoja poglavlja | Slajdovi za svoja poglavlja | Slajdovi za svoja poglavlja |
| **Pitanja za obranu iz skripte** | 1, 2, 3, 4, 6, 7, 21 | 10–15 | 5, 8, 9, 16–20, 22 |

## Pregled u krug

**A pregledava B, B pregledava C, C pregledava A.** Recenzent niti:

1. pregledava njezine PR-ove: kod, testove i usklađenost dokumentacije;
2. neovisno na papiru izvodi njezine dokaze i o nejasnoćama razgovara s nositeljem niti;
3. objašnjava tu nit na zajedničkim prolazima, a nositelj ga dopunjuje;
4. reproducira njezine eksperimente u čistom okruženju (Z4).

`.github/CODEOWNERS` automatski traži pregled od recenzenta niti. Za spajanje vrijedi odobrenje
bilo kojeg drugog člana tima. Datoteke koje ne pripadaju nijednoj niti traže pregled od svih.

## Zajednička sučelja

Početni ugovor prema [ADR-0006](adr/0006-start-with-python-312-and-simple-interfaces.md).
Promjene uskladite s pogođenim pozivateljima i testovima.

```text
src/gitara/
  data.py              A  popis snimki, učitavanje zvuka i anotacija
  spectrogram.py       A  STFT, frekvencije i vremena okvira, tonovi, klavirska rola
  evaluate.py          A  P, R i F1 na razini nota
  peaks.py             A  salijencija tonova iz spektralnih vrhova
  nmf.py               B  funkcije cilja i multiplikativna pravila (KL, Frobenius)
  provenance.py        B  zapis podrijetla pokretanja
  transcribe.py        C  aktivacije uz fiksni W i note iz aktivacija
  templates.py         C  učenje predložaka (maskirani NMF, prosjek spektara)
tests/                 test_<modul>.py uz svaki modul
experiments/
  data_checks.py       A  provjera pretprocesiranja
  stft_sensitivity.py  A  osjetljivost na parametre STFT-a
  convergence.py       B  konvergencija i stabilnost
  cv.py                C  unakrsna provjera po gitaristu za sve metode
  errors.py            C  analiza pogrešaka
data/                  README i manifest kontrolnih zbrojeva; sirovi podaci izvan Gita
results/               odabrane tablice i slike; results/runs/ izvan Gita
```

Dogovori o podacima:

- **Spektrogram** je `float64` polje `A` oblika `(m, n)`: $m$ frekvencijskih binova i $n$
  okvira. `stft_magnitude` vraća i `freqs` (oblik `(m,)`, Hz) te `times` (oblik `(n,)`, s).
  Prozor se centrira uz dopunu nulama, pa je `times[t] = t * hop / sr`. Početak note je vrijeme
  prvog aktivnog okvira, a kraj vrijeme prvog idućeg neaktivnog okvira. Ako je zadnji okvir
  aktivan, kraj je njegovo vrijeme uvećano za `hop / sr`.
- **Pretprocesiranje** radi po snimci. STFT računa amplitudu. Ako A4 uvede normalizaciju
  razine, primjenjuje se zasebno i bilježi uz pokretanje. Predmemoriju uvodimo kad zatreba.
- **Tonovi** su cijeli MIDI brojevi u konstanti `PITCHES` (prijedlog: 40–88, tj. E2–E6,
  $K=49$; potvrditi iz anotacija u A4). Retci od $H$ i stupci od $W$ slijede redoslijed iz
  `PITCHES`. Nedostupan predložak ima nul-stupac u $W$ i nul-redak u $H$. Jezgra prihvaća
  neaktivne komponente, a transkripcija zadržava isti raspored tonova. Ako u eksperimentu
  koristimo pozadinsku komponentu, ide na kraj i preskače se pri izdvajanju nota.
- **Note** su par `(intervals, pitches)`: `intervals` je oblika `(N, 2)` (početak i kraj u
  sekundama), a `pitches` oblika `(N,)` (MIDI, `float`). Učitač anotacija `load_notes` uz taj
  par vraća i `strings`, polje oblika `(N,)` za analizu pogrešaka po žici. Vrednovanje i
  klavirska rola koriste samo intervale i visine.
- **Klavirska rola** je `bool` matrica oblika `(K, n)`.
- **Gitarist** je cijeli broj 0–5 iz prefiksa naziva snimke, a **način** je `comp` ili `solo`.
- **Nevaljan ulaz** (NaN, negativne vrijednosti, krivi oblici) izaziva `ValueError` s jasnom
  porukom. Ništa se prešutno ne popravlja.
- **Slučajnost** dolazi samo iz `numpy.random.default_rng(seed)`, a sjeme je uvijek parametar.
- **Svako pokretanje eksperimenta** zapisuje podrijetlo preko `gitara.provenance`.
  Na početku `start_run(name, config, seeds=..., manifest=...)` stvara novu mapu unutar
  results/runs/ i vraća zapis. Artefakti pokretanja spremaju se u mapu `record["dir"]`.
  Na kraju `finish_run(record, "ok", results)` ili
  `finish_run(record, "failed", errors=[...])` zapisuje ishod.

## Faze, milestonei i zadaci

Repozitorijski zadaci imaju GitHub issue s oznakom niti i milestoneom faze. Brojevi
repozitorijskih issuea navedeni su u zagradama. Tim vodi pisanje, pregled tekstova i
pripremu obrane zasebno.

| Faza (milestone) | Završava | Zadaci |
|---|---|---|
| **Faza 0: dogovor** | Potvrđena podjela i sučelja; radi okruženje | Z0 (#5), B1 (#6) |
| **Faza 1: temelji i prva faktorizacija** | Prolazom 1: prva faktorizacija jedne stvarne snimke | A1 (#7), A2 (#8), B2 (#10), B3 (#11), C2 (#14), Z1 (#15) |
| **Faza 2: cijeli lanac na jednoj podjeli** | Zapisanim planom eksperimenata i prolazom 2 | A4 (#16), A5 (#17), B5 (#19), C3 (#21), C4 (#22), Z2 (#24), Z3 (#25) |
| **Faza 3: rezultati** | Svim planiranim rezultatima | A6 (#26), B6 (#28), C5 (#30), C6 (#31) |
| **Faza 4: reprodukcija** | Reproduciranim rezultatima | Z4 (#36) |

Ovisnosti među zadacima navedene su u svakom issueu i osobnom planu. Najvažnije su:

- okruženje B1 prethodi spajanju svakog koda;
- prolaz Z1 traži spektrogram (A2), jezgru NMF-a (B2) i note iz aktivacija (C2);
- pokretač C4 traži predloške (C3), vrednovanje (A5) i zapis podrijetla (B3);
- glavni eksperiment C5 pokreće se tek nakon zapisanog plana eksperimenata (Z2).

Mislav najviše ovisi o drugima. Zato u fazi 1 ima najviše matematike i kod koji se može
provjeriti na umjetnim podacima.

## Zajednički zadaci

### Z0: dogovor (#5)

Lovro je prenio da su Sara i Mislav na sastanku usmeno potvrdili uloge. Tim je dogovorio
Python 3.12 i postupno dodavanje ovisnosti. Lovro je prepustio pojednostavljenje tehničkih
sučelja, koja su zapisana iznad. B1 je prvi implementacijski zadatak.

Pri početku rada svatko provjerava klon i pokreće `python3 tools/check_before_stop.py`
(vidi [tijek rada](PIPELINE.md)). Priprema za matematiku je Dio I
[skripte](../research/skripta-gitara/skripta-gitara.pdf) i L1, odjeljci 1–2.

### Z1: prolaz 1, prva faktorizacija jedne stvarne snimke (#15)

Sara pokazuje spektrogram i klavirsku rolu jedne snimke. Lovro na njoj pokreće KL-NMF bez
nadzora i pokazuje aktivacije i krivulju funkcije cilja. Mislav pokazuje izdvajanje nota na
malom $H$ s poznatim tonovima. Transkripcija stvarne snimke koristi označene predloške iz C3.

Nit objašnjava njezin recenzent: Sara objašnjava B, Lovro C, a Mislav A. Pitanja, nejasnoće i
tko je stvarno sudjelovao zapisujemo u issue.

### Z2: plan eksperimenata prije završnih pokretanja (#24)

Nositelj je Mislav, a sudjeluju svi. To je zadatak T3 iz [popisa zadataka](TASKS.md).

- Hipoteze se zapisuju prije završnih rezultata, npr.:
  - KL ima veći $F_1$ od Frobeniusa kod većine gitarista;
  - NMF je bolji od spektralnih vrhova;
  - comp je teži od solo.
- Odabrati način učenja predložaka, mrežu hiperparametara, sjemena, broj iteracija, mjere i
  računalni proračun. Važne izbore zabilježiti u ADR-u i [metodologiji](METHODOLOGY.md).

### Z3: prolaz 2, cijeli lanac na jednoj podjeli (#25)

Jedan vanjski fold od podataka do $F_1$. Nit ponovno objašnjava njezin recenzent. Svatko
pokrene cijeli lanac na svom računalu.

### Z4: reprodukcija u čistom okruženju (#36)

Svatko reproducira nit koju pregledava:

- Sara reproducira eksperimente niti B;
- Lovro reproducira eksperimente niti C;
- Mislav reproducira eksperimente niti A.

Koraci su čist klon, instalacija zaključanih ovisnosti prema uputama iz B1, ponovno pokretanje i
usporedba brojeva. Razlike i neuspjehe zapisujemo; ne skrivamo ih.

### Z5: uvod, zaključak i usklađivanje oznaka

Tim zasebno usklađuje tekst. Za provjeru oznaka, parametara i brojeva koristi kod i
identifikatore pokretanja.

### Z6: prolaz 3, probna obrana

Pitanja iz dodatka skripte dijelimo nasumično, tako da svatko dobije i pitanja iz tuđih niti.
Svatko izlaže i dio koji nije njegov. Praznine zapisujemo i zatim ih ponovno obrađujemo.

## Kako se radi na zadatku

1. Dodijeli si issue (ako već nije) i u komentaru napiši da počinješ.
2. Napravi granu iz svježeg `main`:

   ```bash
   git switch main && git pull && git switch -c sara/a1-podaci
   ```

   Prefiks je ime člana, a ne slovo niti.
3. Radi u malim commitovima s porukama na hrvatskom, npr. `podaci: učitaj anotacije iz JAMS-a`.
4. Prije PR-a lokalno pokreni `python3 tools/check_before_stop.py`.
5. Otvori PR prema predlošku. U opisu napiši `Closes #N`. GitHub automatski traži pregled od
   recenzenta niti, CI se pokreće sam, a spajanje je moguće tek nakon odobrenja drugog člana i
   uspješnog CI-ja.
6. Nakon odobrenja autor spaja PR, a issue se zatvara sam. Kvačice u issueu ažuriraj usput.
7. Pitanja i blokade piši u komentare issuea, uz `@spominjanje` osobe. Provjeren problem
   prijavi predloškom „Nalaz” (vidi [pregled i nalaze](AI_REVIEW.md)).

## Što je automatizirano na GitHubu

- **CI** na svakom PR-u i pushu na `main`: provjera dokumentacije i testovi alata. Numeričke
  provjere dodaje B1.
- **Dnevna provjera** prijavljuje pad CI-ja, konflikte, zastarjele PR-ove i spajanja bez pregleda.
- **Zaštita grane `main`**: samo preko PR-a, uz odobrenje drugog člana i uspješan CI.
- **`.github/CODEOWNERS`** automatski traži pregled od recenzenta niti.
- **Predlošci issuea** „Zadatak” i „Nalaz” te predložak PR-a.
- **Oznake i milestonei.** Milestone pokazuje napredak faze, a `Closes #N` zatvara issue pri
  spajanju.

Ploča GitHub Projects nije napravljena jer trenutačni pristupni token nema dopuštenje
`project`. Može se dodati ručno u sučelju GitHuba. Ni jedna automatizacija ne može potvrditi
da netko razumije gradivo; to provjeravamo na prolazima.
