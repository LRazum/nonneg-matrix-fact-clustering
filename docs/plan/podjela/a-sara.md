# Plan osobe A: Sara, nit „od snimke do matrice i od nota do $F_1$”

Zajednička pravila, sučelja i faze opisani su u [podjeli rada](../PODJELA.md). Ovaj plan
je prijedlog; promijeni ga u PR-u ili issueu ako nešto ne odgovara. Brojevi u zagradama
označavaju GitHub issuee.

## Ukratko

Tvoja nit pretvara snimku u nenegativnu matricu $A$ i mjeri koliko su procijenjene note dobre.
Bez nje ostale niti nemaju ni ulaz ni mjeru uspjeha.

- **Matematika:** ton i harmonici; DFT, prozor i spektrogram; zašto je spektar akorda
  približno zbroj spektara tonova. Generalizirana KL divergencija: definicija, nenegativnost,
  homogenost, Poissonova izglednost i usporedba s Frobeniusovom normom. $F_1$ na razini nota.
- **Kod:** `gitara.data`, `gitara.spectrogram`, `gitara.evaluate` i `gitara.peaks`, svaki s
  testovima.
- **Eksperimenti:** provjera pretprocesiranja podataka, osjetljivost na parametre STFT-a i
  referentna metoda spektralnih vrhova.
- **Seminar i prezentacija:** poglavlja i slajdovi o problemu, spektrogramu, funkciji cilja,
  podacima i mjerama uspjeha.
- **Pregled:**
  - pregledavaš Lovrinu nit B: PR-ove, neovisan izvod dokaza (A9) i reprodukciju (Z4);
  - na prolazima objašnjavaš nit B;
  - tvoju nit pregledava Mislav.

**Pitanja za obranu iz skripte koja su „tvoja”:** 1, 2, 3, 4, 6, 7 i 21. Na probnoj obrani
dobit ćeš i pitanja iz tuđih niti.

## Redoslijed

| Faza | Zadatak | Ovisi o | Tko čeka tebe |
|---|---|---|---|
| 0 | Z0 dogovor (#5) | — | svi |
| 1 | A1 podaci (#7) | Z0; za spajanje B1 | A2, A4 |
| 1 | A2 STFT i klavirska rola (#8) | A1, B1 | Z1, B5, C3 |
| 1 | A3 matematika: zvuk, spektrogram i KL (#9) | Z0 | C9, A7 |
| 2 | A4 provjera pretprocesiranja (#16) | A2, B3 | Z2 |
| 2 | A5 vrednovanje na razini nota (#17) | B1 | C4 |
| 2 | A9 neovisna provjera dokaza niti B (#18) | B4 | Z3 |
| 3 | A6 spektralni vrhovi i osjetljivost STFT-a (#26) | A2, C4 | C5 |
| 3 | A7 seminar: poglavlja niti A (#27) | A3–A6 | Z5 |
| 4 | A8 slajdovi niti A (#33) | A7 | Z6 |

Ako te nešto blokira, počni sljedeći zadatak koji ne ovisi o blokadi. A3 i A5 možeš početi
odmah nakon Z0, a A5 se dobro testira bez stvarnih podataka.

## Faza 0: priprema

Uz zajednički sastanak Z0:

1. Kloniraj repozitorij i pokreni `python3 tools/check_before_stop.py`.
2. Pročitaj Dio I [skripte](../../research/skripta-gitara/skripta-gitara.pdf) i L1, odjeljke 1–2.
3. Pročitaj opis skupa: Q. Xi i sur., *GuitarSet: A Dataset for Guitar Transcription*,
   ISMIR 2018, i stranicu Zenodo zapisa 3371780. Zapiši kako su anotacije nastale: iz
   heksafonskog pickupa, a ne iz mikrofona. To je važno za A4.

## A1: preuzimanje GuitarSeta i učitavanje (#7)

**Cilj:** ponovljivo preuzimanje podataka s provjerom kontrolnih zbrojeva i modul `gitara.data`.

1. Preko Zenodo API-ja (`https://zenodo.org/api/records/3371780`) pročitaj popis datoteka,
   veličine i MD5. Trebaju samo `annotation.zip` i `audio_mono-mic.zip`. Lovrina lokalna
   proba zabilježila je 2026-11-04 sljedeće vrijednosti, koje treba ponovno provjeriti:

   | Datoteka | Veličina (B) | MD5 |
   |---|---:|---|
   | `annotation.zip` | 39 132 574 | `b39b78e63d3446f2e54ddb7a54df9b10` |
   | `audio_mono-mic.zip` | 656 927 981 | `275966d6610ac34999b58426beb119c3` |

   Zenodo ne podržava nastavak prekinutog preuzimanja, pa se datoteka preuzima cijela.
2. Napiši naredbu za preuzimanje, npr. `python -m gitara.data download`. Ona sprema arhive
   u mapu data/raw/ (izvan Gita), provjerava MD5, raspakirava ih i zapisuje manifest s MD5
   vrijednošću svake snimke i anotacije. Manifest je malen, pa ga verzioniramo u mapi `data/`.
3. U `gitara.data` napiši:
   - `Track` (dataclass): `track_id` (npr. `00_BN1-129-Eb_comp`), `player` (0–5, iz prefiksa),
     `mode` (`comp` ili `solo`, iz sufiksa), putanju zvuka i putanju anotacije;
   - `list_tracks(root)`: sortiran popis. Provjeri da ima 360 snimki, po 60 za svakog
     gitarista, od kojih je 30 comp i 30 solo;
   - `load_audio(track, sr=22050)`: čita WAV (`scipy.io.wavfile`), pretvara u `float64` u
     $[-1,1]$, provjerava da je mono i preuzorkuje 44 100 → 22 050 Hz pomoću
     `scipy.signal.resample_poly`. **Ne normalizira razinu**; to je zasebna, izričita odluka
     u A4;
   - `load_notes(track)`: parsira JAMS, koji je običan JSON, pa paket `jams` nije potreban.
     Uzmi anotacije s imenskim prostorom `note_midi`; ima ih šest, po jedna za svaku žicu.
     Vraća `intervals` `(N, 2)`, `pitches` `(N,)` (MIDI, `float`, izvorna necijela vrijednost)
     i `strings` `(N,)` (0–5), sortirano po početku. Provjeri u podacima koje polje određuje
     žicu i to zapiši u docstring.
4. Provjera ulaza:
   - nedostaje datoteka → `FileNotFoundError`;
   - neočekivan broj kanala, nekonačne vrijednosti ili nota trajanja $\leq 0$ → `ValueError`
     s nazivom snimke.
5. Testovi (modul `test_data`):
   - ručno napisana mala JAMS datoteka s dvije žice i tri note u privremenoj mapi daje točne
     intervale, visine i žice;
   - parsiranje `track_id` za comp i solo;
   - WAV s poznatim sinusom, zapisan u privremenu mapu, nakon preuzorkovanja ima vrh spektra
     na istoj frekvenciji;
   - pogrešna MD5 vrijednost izaziva pogrešku.

   Stvarne datoteke GuitarSeta ne stavljamo u testove.
6. U `data/` napiši README: izvor i citat, licencu CC BY 4.0, datum pristupa, MD5, naredbu za
   preuzimanje, strukturu mapa te što je u Gitu, a što nije.

**Gotovo kada:** svih 360 snimki i anotacija učitava se bez pogreške; broj nota odgovara opisu
skupa (prijedlog tema navodi 62 476); testovi prolaze u CI-ju; Mislav je pregledao PR.

## A2: STFT i klavirska rola (#8)

**Cilj:** modul `gitara.spectrogram` koji iz zvuka daje $A$, frekvencije, vremena okvira i
klavirsku rolu.

1. Prijedlog početnih parametara (konačno ih biraš u A6):
   - frekvencija uzorkovanja 22 050 Hz;
   - Hannov prozor $N=2048$ (92,9 ms) i korak 512 (23,2 ms);
   - rezolucija $\Delta f = 22\,050/2048 \approx 10{,}77$ Hz;
   - gornja granica frekvencije $f_{\max}$, primjerice 5,5 kHz. Odluku obrazloži: koliko
     harmonika najvišeg i najnižeg tona ostaje ispod granice?
2. `stft_magnitude(y, sr, n_win, hop, f_max)` vraća `(A, freqs, times)`. Implementiraj STFT
   sam pomoću `numpy.fft.rfft` i usporedi ga sa `scipy.signal.stft` u testu. Tako ćeš znati
   objasniti svaki korak. Odluči o centriranju okvira i dopuni na rubovima i zapiši odluku.
   `times` su središta prozora.
3. Pretvorbe: `midi_to_hz(p)` $=440\cdot 2^{(p-69)/12}$ i `hz_to_midi(f)`.
4. Konstanta `PITCHES`: cijeli MIDI brojevi 40–88. Potvrdi raspon iz anotacija u A4.
5. `piano_roll(intervals, pitches, times, PITCHES)` vraća `bool` matricu $(K,n)$:
   $R_{kt}=1$ ako postoji nota s $\mathrm{round}(p)=\texttt{PITCHES}[k]$ i
   $\text{početak}\le t<\text{kraj}$. Note izvan raspona broji i prijavljuje, a ne odbacuje
   ih prešutno.
6. Predmemorija: spektrograme spremaj u mapu data/processed/ (izvan Gita) kao NumPy datoteke, uz zapis
   parametara. Ako se parametri promijene, predmemorija se ne smije prešutno koristiti.
7. Testovi (modul `test_spectrogram`):
   - sinus točno na frekvenciji nekog bina daje najveću vrijednost u tom binu, s amplitudom
     koju izračunaš iz zbroja vrijednosti prozora;
   - zbroj dvaju sinusa udaljenih frekvencija daje spektrogram približno jednak zbroju
     spektrograma. To je numerička ilustracija propozicije o zbrajanju modula;
   - broj i vrijednosti `times`;
   - nenegativnost i konačnost;
   - NaN na ulazu izaziva `ValueError`;
   - klavirska rola na ručno zadanim notama.

**Gotovo kada:** spektrogrami svih snimki postoje lokalno; testovi prolaze; Lovro može
pokrenuti NMF na jednoj snimki za Z1.

## A3: matematika od zvuka do matrice i KL divergencija (#9)

**Cilj:** nacrt tvojih poglavlja seminara s potpunim izvodima. Sve izvode prođi sama na
papiru, pa ih tek onda zapiši. Skripta je polazište, a ne gotov tekst. Uz svaku tvrdnju
označi je li citirana, vlastiti izvod ili empirijsko opažanje.

1. **Ton i harmonici.**
   - Harmonici su na $f_n=n f_0$, a MIDI broj je $p=69+12\log_2(f/440)$.
   - Zašto se oktave lako zamijene: harmonici tona $p+12$ podskup su harmonika tona $p$.
   - Izvor: skripta, odjeljak „Ton, frekvencija i harmonici”.
2. **DFT i STFT.**
   - Definicija DFT-a i frekvencija bina $k\,f_s/N$; Nyquistova frekvencija.
   - Prozor, korak i definicija spektrograma $a_{kt}=|X(k,t)|$; propozicija o sinusoidi kroz
     prozor.
   - Kompromis vremenske i frekvencijske razlučivosti, s brojevima za odabrane parametre.
     Kod E2 polutonovi su udaljeni oko 4,9 Hz, a bin je širok oko 10,8 Hz. Objasni
     posljedice za niske tonove.
   - Izvor: skripta, odjeljak „Signal, DFT i spektrogram” u Dijelu II, i udžbenik obrade
     signala koji odabereš i citiraš.
3. **Približna aditivnost.**
   - STFT je linearan, pa je $X_{x+y}=X_x+X_y$.
   - Za modul vrijedi $|X_x+X_y|\le|X_x|+|X_y|$, uz jednakost kad su faze poravnate ili
     kad su nosači razdvojeni.
   - Kada je spektar akorda točno, a kada samo približno zbroj?
   - Izvor: propozicija o zbrajanju modula u skripti.
4. **Zašto amplitudni spektrogram**, a ne snaga ili logaritam: nenegativnost i (približna)
   aditivnost.
5. **Generalizirana KL divergencija.**
   - Definicija $D(A\|V)=\sum_{ij}\bigl(a_{ij}\log\frac{a_{ij}}{v_{ij}}-a_{ij}+v_{ij}\bigr)$,
     uz $0\log 0=0$, i domena.
   - Dokaz da je $D\ge0$, uz jednakost točno za $A=V$ (npr. preko $\log x\le x-1$).
   - $D$ nije simetrična.
   - Izvori: L3, odjeljak 3; skripta, propozicija o nenegativnosti KL divergencije.
6. **Homogenost.**
   - $D(cA\|cV)=c\,D(A\|V)$, a $\|cA-cV\|_F^2=c^2\|A-V\|_F^2$.
   - Posljedica: glasnije snimke inače dobivaju veću težinu u učenju (veza s A4), a relativni
     kriterij zaustavljanja za KL ne ovisi o glasnoći.
   - Izvor: propozicija o ljestvici u skripti.
7. **Statistička interpretacija.**
   - Ako su $a_{ij}$ nezavisne Poissonove varijable s očekivanjem $(WH)_{ij}$, onda je
     $-\log L = D(A\|WH)+\text{konst}$, pa minimizacija KL divergencije maksimizira izglednost.
   - Frobeniusova norma odgovara Gaussovu šumu.
   - Amplitudni spektrogram nije brojčani podatak, pa je ovo motivacija, a ne opis podataka.
   - Izvori: L2, jednadžba (2); propozicija o Poissonovu modelu u skripti.
8. **Zašto KL za zvuk.** Frobeniusova norma pogreške u jakim binovima kažnjava oko $a^2$, a KL
   oko $a$. Tihi viši harmonici, koji razlikuju tonove, zato više vrijede. Ovo je intuicija,
   pa je tako i označi. Izvori: skripta, odjeljak „Kako mjeriti koliko je $WH$ blizu $A$”, i
   Févotte i sur. (L1, ref. [42]); pročitaj prije citiranja.
9. **Mali primjer.** Ručno izračunaj $D$ i Frobeniusovu udaljenost za dvije matrice $2\times2$.
   Isti primjer stavi u test u A5 ili A2.
10. Uskladi oznake s [metodologijom](../METHODOLOGY.md): $A$ je $m\times n$, s frekvencijama u
    retcima i okvirima u stupcima.

**Gotovo kada:** nacrt je u dogovorenom formatu u mapi `seminar/`; Mislav je neovisno prošao
izvode (C9) i nejasnoće su zapisane u issueu.

## A4: provjera pretprocesiranja podataka (#16)

**Cilj:** prije modela znati kakvi su podaci. Lovrina lokalna proba upozorila je na nekoliko
zamki; svaku provjeri sama i ne preuzimaj njezine brojeve.

1. **Razina zvuka po gitaristu.**
   - Za svaku snimku izračunaj vršnu razinu i RMS u dBFS, medijan po gitaristu i broj
     odrezanih uzoraka.
   - Proba je pokazala da su neki gitaristi snimljeni znatno tiše.
   - Predloži normalizaciju (npr. dijeljenje svakog spektrograma njegovom srednjom
     vrijednošću) i obrazloži je homogenošću iz A3.
   - Odluku zapiši u [metodologiju](../METHODOLOGY.md), odjeljak 4.
2. **Poravnanje anotacija s mikrofonom.**
   - Anotacije potječu iz pickupa, a mi koristimo mikrofon.
   - Usporedi anotirane početke s vrhovima spektralnog toka (kratki prozor) na snimci
     mikrofona. Prijavi srednji pomak i raspršenje.
   - Pomak ispravljaj samo ako je usporediv s tolerancijom od 50 ms.
3. **Comp i solo.** Broj nota u sekundi, prosječan broj istodobnih nota i raspon tonova, po
   načinu sviranja i gitaristu.
4. **Raspon tonova i savijanje žica.**
   - Najniži i najviši MIDI broj; udio nota koje od polutona odstupaju više od 25 centi.
   - Referentni ton je zaokružen MIDI broj, uz toleranciju od 50 centi.
   - Potvrdi ili promijeni `PITCHES`.
5. **Repertoar.** Iz naziva datoteka provjeri sviraju li svi gitaristi iste isječke. Ako je
   tako, unakrsna provjera mjeri prijenos na novog svirača, a ne na novu glazbu. Javi to
   Mislavu za ograničenja u C6.
6. Sve izvodi kao `python -m experiments.data_checks`, sa zapisom podrijetla (`gitara.provenance`,
   B3). Rezultat je JSON i nekoliko slika u `results/`.

**Gotovo kada:** odluke o normalizaciji i rasponu tonova zapisane su u metodologiji; rezultati
su povezani s pokretanjem; tim je o nalazima obaviješten prije Z2.

## A5: vrednovanje na razini nota (#17)

**Cilj:** vlastita, provjerena implementacija preciznosti, odziva i $F_1$ u `gitara.evaluate`.

1. **Matematika** (ide u tvoje poglavlje „Mjere uspjeha”):
   - Par (procijenjena, stvarna nota) je dopušten ako se visine razlikuju najviše za 50 centi,
     a početci najviše za $\Delta=50$ ms.
   - $\mathrm{TP}$ je veličina **najvećeg sparivanja** u bipartitnom grafu dopuštenih parova.
   - $P=\mathrm{TP}/|\mathcal E|$, $R=\mathrm{TP}/|\mathcal R|$ i $F_1=2PR/(P+R)$.
   - Objasni zašto pohlepno sparivanje nije dovoljno i što radimo kad je
     $\mathcal E=\emptyset$: $P$ nije definiran, prijavljujemo to i dogovaramo $F_1=0$.
   - Izvori: skripta, definicija mjera na razini nota; Raffel i sur., *mir_eval*, ISMIR 2014.
2. **Kod:**
   - `note_scores(ref_intervals, ref_pitches, est_intervals, est_pitches, onset_tol=0.05,
     pitch_tol_cents=50)` vraća `P`, `R`, `F1` i `TP`;
   - sparivanje pomoću `scipy.sparse.csgraph.maximum_bipartite_matching` ili vlastitog
     Hopcroft–Karpova algoritma;
   - neobavezno: inačica s kriterijem kraja note (`offset_ratio` 0,2) kao sporedna mjera.
3. **Testovi** (modul `test_evaluate`), na primjerima izračunatima ručno:
   - jednake liste daju $F_1=1$;
   - pomak početka 49 ms se broji, a 51 ms ne;
   - oktavna pogreška nije pogodak;
   - jedna procjena ne smije se upariti s dvije stvarne note;
   - na protuprimjeru pohlepno sparivanje daje manji $\mathrm{TP}$ od najvećeg;
   - prazne liste;
   - na nasumičnim primjerima rezultat se slaže s
     `mir_eval.transcription.precision_recall_f1_overlap` uz `offset_ratio=None`.
     `mir_eval` prima visine u Hz.

**Gotovo kada:** testovi prolaze; Mislav je pregledao kod; C4 može koristiti modul.

## A6: spektralni vrhovi i osjetljivost STFT-a (#26)

**Cilj:** referentna metoda bez učenja i obrazložen izbor parametara STFT-a.

1. **Spektralni vrhovi** (`gitara.peaks.pitch_salience(A, freqs, PITCHES)`):
   - salijencija tona $k$ u okviru $t$ najveća je amplituda u binovima unutar $\pm\tfrac12$
     polutona oko $f_0(k)$; ako takvog bina nema, uzima se najbliži bin;
   - rezultat je matrica oblika $(K,n)$ koja dalje prolazi **isti** postupak za note (C2) i
     **isti** izbor hiperparametara (C4) kao NMF.
2. Testovi: sinus na $f_0(k)$ daje najveću salijenciju za ton $k$. Pokaži i dokumentiraj da
   kod niskih tonova susjedni polutoni padaju u isti bin. To je očekivano ograničenje, a ne
   pogreška.
3. **Osjetljivost STFT-a:**
   - samo na **jednom unutarnjem foldu**, dakle na gitaristima za učenje, nikad na testnom;
   - usporedi npr. $N\in\{2048, 4096\}$ i korak $\in\{256, 512\}$ s KL postupkom;
   - procijeni trošak prije pokretanja, jer učenje predložaka za KL može trajati desetke
     minuta po foldu;
   - zabilježi sva pokretanja, uključujući neuspjela;
   - izbor zapiši u metodologiju, a ako se mijenjaju početni parametri, i u ADR.

**Gotovo kada:** parametri su odabrani bez testnih gitarista; metoda vrhova radi kroz Mislavov
pokretač; rezultati imaju zapis podrijetla.

## A7: seminar, poglavlja niti A (#27)

Nacrt iz A3 dopuni podacima i rezultatima:

1. **Problem:** pitanje, transkripcija, klavirska rola i zašto je zadatak težak (oktave,
   akordi, ista nota na više žica).
2. **Od zvuka do matrice:** DFT, STFT, parametri i aditivnost, uz sliku spektrograma s
   ucrtanim anotacijama i sliku harmoničkog češlja.
3. **Funkcija cilja:** KL divergencija, nenegativnost, homogenost, Poisson, usporedba s
   Frobeniusom.
4. **Podaci:** GuitarSet, licenca, predobrada i nalazi iz A4, uz sliku razine po gitaristu.
5. **Mjere uspjeha:** definicija $F_1$ i sparivanje, rezultati metode vrhova.

Svaka slika i broj imaju identifikator pokretanja. Preuzete slike odvoji od naših i citiraj.

## A8: slajdovi niti A (#33)

Oko 4–6 slajdova: zvuk → spektrogram → matrica $A$; zašto je zbroj približan; KL prema
Frobeniusu na jednoj slici; kako mjerimo $F_1$. Iste oznake i brojevi kao u seminaru.
Pripremi kratko objašnjenje bez slajdova za probnu obranu (Z6).

## A9: neovisna provjera dokaza niti B (#18)

Ti si recenzentica Lovrine niti. Kad B4 bude u PR-u, bez gledanja u njegov tekst na papiru
izvedi:

1. gradijente $\nabla_H D=W^T(\mathbf 1-A\oslash WH)$ i $\nabla_W D=(\mathbf 1-A\oslash WH)H^T$;
2. uvjete optimalnosti na nenegativnom ortantu i primjer stacionarne točke koja nije minimum;
3. multiplikativno pravilo iz gradijentnog koraka s korakom $h_{kj}/(W^T\mathbf 1)_{kj}$;
4. lemu o pomoćnoj funkciji, majorantu preko Jensenove nejednakosti i teorem o nerastu
   (L3, odjeljak 6, teorem 2).

Usporedi svoj izvod s Lovrinim i sa L3. Svaku razliku ili nejasnoću zapiši u issue ili kao
komentar u PR-u. Na prolazima Z1 i Z3 ti objašnjavaš nit B, a u Z4 reproduciraš Lovrine
eksperimente.

## Što trebaš znati iz tuđih niti

- **Iz niti B:** što radi `gitara.nmf.fit` i zašto funkcija cilja ne raste. To je tvoj
  recenzentski posao, pa ćeš ga znati najbolje.
- **Iz niti C:** zašto je problem uz fiksni $W$ konveksan, kako maskirani NMF uči predloške i
  kako se biraju hiperparametri bez testnog gitarista. Pročitaj Mislavov nacrt C1 kad bude
  spreman.
