# Plan osobe C: Mislav, nit „od faktora do nota”

Zajednička pravila, sučelja i faze opisani su u [podjeli rada](../PODJELA.md). Ovaj plan je
prijedlog; mijenja se u PR-u ili issueu. Brojevi u zagradama označavaju GitHub issuee.

## Ukratko

Tvoja nit pretvara faktorizaciju u odgovor na istraživačko pitanje: kako iz označenih snimki
naučiti predloške, kako iz aktivacija dobiti note i koliko dobro to radi na novom gitaristu.

- **Matematika:**
  - model $A\approx WH$ i usporedba sa SVD-om;
  - nejedinstvenost i normalizacija; NP-težina;
  - nekonveksnost punog problema i konveksnost po $H$ uz fiksni $W$;
  - što jest, a što nije dokazano o konvergenciji multiplikativnih pravila;
  - propozicija o maskiranom NMF-u i formalizacija postupka za note.
- **Kod:** `gitara.transcribe`, `gitara.templates` i pokretač unakrsne provjere po gitaristu.
- **Eksperimenti:** glavni eksperiment sa šest podjela i tri metode te analiza pogrešaka.
- **Seminar i prezentacija:** model i struktura problema, jamstva, primjena, rezultati,
  rasprava i ograničenja.
- **Pregled:**
  - pregledavaš Sarinu nit A: PR-ove, neovisan izvod dokaza (C9) i reprodukciju (Z4);
  - na prolazima objašnjavaš nit A;
  - tvoju nit pregledava Lovro.

**Pitanja za obranu iz skripte koja su „tvoja”:** 5, 8, 9, 16–20 i 22. Na probnoj obrani dobit
ćeš i pitanja iz tuđih niti.

## Redoslijed

| Faza | Zadatak | Ovisi o | Tko čeka tebe |
|---|---|---|---|
| 0 | Z0 dogovor (#5) | — | svi |
| 1 | C1 matematika: model, struktura i jamstva | Z0 | B9, C7 |
| 1 | C2 note iz aktivacija (#14) | B1 | Z1, C4 |
| 2 | C3 učenje predložaka (#21) | A2, B2 | C4, B6, Z2 |
| 2 | C4 pokretač unakrsne provjere (#22) | C2, C3, A5, B3 | A6, C5, Z3 |
| 2 | C9 neovisna provjera dokaza niti A | A3 | Z3 |
| 2 | Z2 plan eksperimenata, ti si nositelj (#24) | Z1, A4, B5, C3 | C5 |
| 3 | C5 glavni eksperiment (#30) | C4, A6, Z2 | C6, Z4 |
| 3 | C6 analiza pogrešaka (#31) | C5 | C7 |
| 3 | C7 seminar: poglavlja niti C | C1, C5, C6 | Z5 |
| 4 | C8 slajdovi niti C | C7 | Z6 |

Najviše ovisiš o drugima. Zato u fazi 1 radi matematiku (C1) i C2, koji se potpuno provjerava na
umjetnom $H$. C3 možeš početi na umjetnim podacima i prije nego što A2 bude spojen.

## C1: matematika: model, struktura problema i jamstva

**Cilj:** nacrt tvojih poglavlja seminara s potpunim izvodima. Skripta je polazište, a ne gotov
tekst. Uz svaku tvrdnju označi je li citirana, vlastiti izvod ili empirijsko opažanje.

1. **Model.**
   - Stupci od $W$ su spektralni predlošci tonova, a retci od $H$ aktivacije kroz vrijeme.
   - Zašto nenegativnost: aditivne kombinacije bez poništavanja.
   - Rang $r=K$ (broj tonova), uz moguću pozadinsku komponentu.
   - Razlika između NMF-a bez nadzora i učenja s maskom.
   - Izvori: skripta, odjeljak „Model $A\approx WH$”; L1, odjeljci 1–2; L2.
2. **Usporedba sa skraćenim SVD-om.** SVD je optimalan u Frobeniusovoj normi
   (Eckart–Young), ali faktori imaju negativne elemente, pa nisu „dijelovi”. Izvor: L1,
   odjeljak 1.
3. **Nejedinstvenost i normalizacija.**
   - $(WD)(D^{-1}H)=WH$ za pozitivnu dijagonalnu $D$, i permutacije.
   - Normalizacija stupaca od $W$ na $\ell_1$-normu 1 uz preskaliranje redaka od $H$ čuva
     $WH$, pa $h_{kj}$ dobiva značenje mase tona $k$ u okviru $j$.
   - Maska fiksira permutaciju.
   - Izvori: L1, odjeljak 3 (uvod); propozicije o nejedinstvenosti i normalizaciji u skripti.
4. **Složenost.** NMF je općenito NP-težak (Vavasis 2009, prema L1, odjeljak 3). To citiraš,
   ne dokazuješ.
5. **Nekonveksnost i konveksnost.**
   - Primjer: $f(w,h)=\tfrac12(1-wh)^2$ nije konveksna. Pokaži to preko Hessijana u
     $(0,0)$ ili preko polovišta.
   - Uz fiksni $W$ funkcija $D(A\|WH)$ rastavlja se po stupcima. Svaki pribrojnik je konveksan
     u $h_j$, jer je $-\log$ afine funkcije konveksan, pa je svaki lokalni minimum globalan.
     Isto vrijedi za Frobeniusov potproblem (nenegativni najmanji kvadrati).
   - Izvori: L3, odjeljak 3; L1, odjeljak 3.1; skripta, propozicija o konveksnim potproblemima
     i napomena o potproblemu uz fiksni $W$.
6. **Što je, a što nije dokazano o konvergenciji.** Ovo je jedno od najvažnijih mjesta za
   obranu.
   - **Dokazano:** funkcija cilja ne raste. Odozdo je ograničena, pa niz vrijednosti
     konvergira.
   - **Nije dokazano:**
     - da iterati konvergiraju;
     - da je granica stacionarna točka;
     - da je granica lokalni minimum.
   - L3 nakon leme 1 tvrdi konvergenciju prema lokalnom minimumu, a L4 (odjeljak 3.1) pokazuje
     da dokaz daje samo nerast.
   - Granična točka s pozitivnim elementima je stacionarna; za točku na rubu to ne slijedi.
     Navedi primjer nepomične točke koja nije stacionarna (primjer zapinjanja u skripti).
   - L4, odjeljak 3.4, tvrdi da je točka koja zadovoljava uvjete optimalnosti barem lokalni
     minimum. To ne vrijedi, a protuprimjer je $(0,0)$.
   - Spomeni Linovu izmjenu (2007, prema L1) koja daje jaču tvrdnju. Pročitaj je prije
     citiranja.
7. **Maskirani NMF** (propozicija o maskiranom učenju u skripti, vlastiti izvod):
   - ako $H_0$ ima nule točno tamo gdje je maska nula, pravila čuvaju masku;
   - početna KL vrijednost je konačna kad je $(WH)_{ij}>0$ svugdje gdje je $a_{ij}>0$.
     Pozitivno inicijalizirani predlošci pokrivaju nenulte okvire koje maska pridružuje
     barem jednoj komponenti;
   - za dokaz nerasta obradi aktivne komponente i pretpostavke iz B4;
   - ton koji se ne pojavljuje u skupu za učenje ne može se naučiti.
8. **Transkripcija i odabir hiperparametara.**
   - Formalno zapiši prag, spajanje okvira u note i najkraće trajanje.
   - Objasni zašto se hiperparametri biraju samo na gitaristima za učenje (ugniježđena
     unakrsna provjera; AGENTS.md, pravilo 7). U suprotnom bi rezultat bio optimistično
     pristran.

**Gotovo kada:** Lovro je neovisno prošao nacrt (B9) i raspravio nejasnoće s Mislavom.

## C2: note iz aktivacija (#14)

**Cilj:** `gitara.transcribe`, potpuno testiran na umjetnim podacima.

1. `activations(A, W, objective, max_iter, tol)` poziva Lovrin `gitara.nmf.fit` uz
   `update_W=False`. Početni $H$ ima jedinice za dostupne predloške i nul-retke za nul-stupce
   u $W$. `fit` prijavljuje neizvedivu KL rekonstrukciju. Dok B2 nije spojen, testiraj
   izlučivanje nota izravno na umjetnom $H$.
2. `extract_notes(H, times, PITCHES, frame_step, threshold, min_duration, retrigger=None)`:
   1. uzima prvih $K$ redaka (tonove) i dijeli ih njihovom najvećom aktivacijom po snimci.
      Ako je ona nula, vraća prazna polja intervala i visina;
   2. okvir je aktivan ako je $\hat h_{kt}\ge\theta$, uz $0<\theta\le1$;
   3. svaki najdulji niz uzastopnih aktivnih okvira u retku $k$ postaje nota. Početak je
      `times` prvog aktivnog okvira, a kraj `times` prvog sljedećeg neaktivnog okvira.
      Niz do zadnjeg okvira završava u `times[-1] + frame_step`, uz `frame_step = hop / sr`;
   4. ako je zadan `retrigger` $\delta$, niz se dijeli na lokalnim maksimumima porasta
      $\hat h_{kt}-\hat h_{k,t-1}>\delta$, jer ponovljeni udarac iste note inače postaje
      jedna duga nota;
   5. odbacuje note kraće od $d_{\min}$.
3. Testovi (modul `test_transcribe`):
   - umjetni $H$ s poznatim blokovima daje točno očekivane note;
   - rubni slučajevi praga;
   - kratka nota se odbacuje;
   - ponovljeni udarac se dijeli;
   - nul-matrica daje prazna polja, a nul-redak ne proizvodi note;
   - pretvorba okvira u sekunde uključuje ulaz s jednim okvirom.

**Gotovo kada:** testovi prolaze; Lovro je pregledao PR; postupak je spreman za Z1.

## C3: učenje predložaka (#21)

**Cilj:** `gitara.templates` s dvije mogućnosti iz skripte. Izbor između njih ide u Z2.

1. `mask_from_roll(R, background=True)` vraća masku $M$ oblika $(K,n)$ ili $(K+1,n)$. Redak
   pozadine je svugdje 1.
2. `learn_templates(blocks, objective, max_iter, tol, seed, background)`:
   - `blocks` je popis parova (spektrogram, klavirska rola);
   - za dostupne tonove $W_0$ se uzima iz `default_rng(seed).uniform(0.5, 1.5)`, a $H_0=M$ po
     bloku. Ton bez označenog okvira dobiva nul-stupac već u $W_0$;
   - poziva `fit` s više blokova;
   - vraća predloške u redoslijedu `PITCHES`, s nul-stupcima za nedostupne tonove. Za KL
     provjeri pokriva li maska nenulte okvire. Ako ne pokriva, prijavi ih i zapiši način
     obrade prije pokretanja (npr. pozadinska komponenta ili izričit odabir okvira za učenje).
3. `average_templates(blocks)`: predložak tona je prosjek normaliziranih spektara okvira u
   kojima svira samo taj ton. Ako takvih okvira nema, ton je neaktivan.
4. Testovi (modul `test_templates`):
   - umjetni podaci: $W_*$ kao harmonički češljevi, $H_*$ s maskom i $A=W_*H_*$. Naučeni
     predlošci imaju kosinusnu sličnost s $W_*$ blizu 1, jer maska fiksira permutaciju;
   - maska je očuvana;
   - neaktivni ton je prepoznat;
   - pozadinski redak je uvijek aktivan;
   - funkcija cilja ne raste.
5. Na jednom unutarnjem foldu usporedi maskirani NMF i prosjek spektara. Rezultat donesi na Z2.

**Gotovo kada:** testovi prolaze; prvi predlošci naučeni na stvarnim podacima pokazuju
harmoničku strukturu (slika); Lovro je pregledao PR.

## C4: pokretač unakrsne provjere po gitaristu (#22)

**Cilj:** `python -m experiments.cv`, jedan pokretač za KL, Frobenius i spektralne vrhove.
Testni gitarist nikad ne sudjeluje u izboru hiperparametara.

1. **Vanjski foldovi** $g=0,\dots,5$: predlošci $W_{\setminus g}$ uče se na ostalih pet
   gitarista, a testira se na gitaristu $g$.
2. **Unutarnji foldovi** za hiperparametre $(\theta,\delta,d_{\min})$:
   - za svaki $j\ne g$ uči se $W_{\setminus\{g,j\}}$ na četiri gitarista i prepisuje se
     gitarist $j$;
   - bira se kombinacija s najvećim srednjim $F_1$ po snimci;
   - $W_{\setminus\{g,j\}}=W_{\setminus\{j,g\}}$, pa je to 15 parova i 6 vanjskih, ukupno
     21 učenje po metodi.
3. **Mreža hiperparametara** zadaje se u konfiguraciji. Ako je izabrana vrijednost na rubu
   mreže, mreža se proširuje i unutarnji izbor ponavlja. To pravilo zapiši u Z2 prije
   završnih pokretanja.
4. Spektralni vrhovi nemaju učenje, ali prolaze isti izbor hiperparametara na unutarnjim
   foldovima.
5. **Predmemorija i nastavak:**
   - aktivacije i predlošci spremaju se unutar results/runs/;
   - zapisivanje je atomsko, a ponovno pokretanje preskače gotovo;
   - svako pokretanje ima zapis podrijetla (`gitara.provenance`).
6. **Proračun.** KL učenje na velikom foldu može trajati desetke minuta. Na računalu s 8 GB
   RAM-a pokreni najviše jedan paralelni bazen procesa i postavi varijable dretvi iz B1.
   Procjenu vremena zapiši prije pokretanja.
7. **Izlaz:** P, R i $F_1$ po snimci, gitaristu i načinu (comp ili solo) u JSON-u. Tu je i
   zapis izabranih hiperparametara po foldu.
8. **Test:** cijeli lanac na malom umjetnom skupu (2–3 „gitarista”). Provjerava se da testni
   gitarist ne sudjeluje u izboru i da isto sjeme daje iste rezultate.

**Gotovo kada:** jedan vanjski fold radi od početka do kraja (za Z3); Lovro je pregledao PR.

## C5: glavni eksperiment (#30)

Pokreće se **tek kad je plan iz Z2 zapisan**.

1. Pokreni svih šest vanjskih foldova za KL, Frobenius i spektralne vrhove.
2. Napravi tablicu po gitaristu te srednju vrijednost i standardnu devijaciju; posebno za comp
   i solo.
3. Izračunaj uparene razlike $F_1$ (KL − Frobenius, KL − vrhovi) po snimci i po gitaristu.
   - Test predznaka preko šest gitarista: kad svih šest razlika ima isti predznak, dvostrana
     p-vrijednost je $2\cdot2^{-6}\approx0{,}031$ i to je najmanja moguća.
   - Bootstrap po snimkama ne modelira ovisnost snimki istog gitarista. Tumači ga kao opis
     raspršenja, a ne kao dokaz generalizacije.
4. Prikaži sva pokretanja, uključujući neuspjela, te sva sjemena i foldove.

## C6: analiza pogrešaka (#31)

1. Razvrstaj lažno pozitivne note:
   - oktava;
   - susjedni poluton;
   - ponovljeni ton bez novog početka;
   - nota bez ijedne stvarne note u blizini.
2. Lažno negativne razvrstaj prema broju istodobnih nota (akordi), žici (Sara daje žicu u A1)
   i visini tona.
3. Usporedi comp i solo.
4. Napravi sliku naučenih predložaka. Imaju li harmoničku strukturu i jesu li najniži tonovi
   slabi na temeljnoj frekvenciji?
5. Ograničenja:
   - predlošci su nadzirani;
   - provjeri sa Sarom (A4) sviraju li svi gitaristi isti repertoar;
   - generalizacija na drugu gitaru ili prostoriju nije provjerena.

## C7: seminar, poglavlja niti C

1. **Model i struktura:** model, SVD, nejedinstvenost, normalizacija, NP-težina,
   nekonveksnost i konveksnost.
2. **Jamstva:** što je dokazano, a što nije; primjer zapinjanja; kritika L3 i L4.
3. **Primjena:** maskirani NMF, transkripcija i ugniježđena unakrsna provjera.
4. **Rezultati i rasprava:** tablice iz C5, analiza iz C6, ograničenja i odgovor na
   istraživačko pitanje.

Svaki broj i slika imaju identifikator pokretanja. Skroman ili negativan rezultat legitiman
je ako je pošteno izmjeren.

## C8: slajdovi niti C

Oko 5–7 slajdova:

- nejedinstvenost na jednoj slici;
- zašto je transkripcija uz fiksni $W$ laka;
- shema ugniježđene unakrsne provjere;
- glavna tablica i primjer prepisane snimke uz stvarne note;
- ograničenja.

## C9: neovisna provjera dokaza niti A

Ti si recenzent Sarine niti. Kad nacrt A3 bude spreman, na papiru neovisno izvedi:

1. propoziciju o zbrajanju modula: kada je spektar zbroja jednak zbroju spektara;
2. nenegativnost KL divergencije i kada je jednaka nuli;
3. homogenost KL divergencije i Frobeniusove norme te posljedicu za normalizaciju snimki;
4. ekvivalenciju minimizacije KL divergencije i Poissonove izglednosti;
5. zašto $F_1$ traži najveće sparivanje, a ne pohlepno.

Razlike i nejasnoće prođi sa Sarom. Na prolazima Z1 i Z3 objašnjavaš nit A, a u Z4
reproduciraš Sarine eksperimente.

## Što trebaš znati iz tuđih niti

- **Iz niti A:** ovo je tvoj recenzentski posao, pa ćeš ga znati najbolje: spektrogram, KL
  divergencija i $F_1$.
- **Iz niti B:** izvod multiplikativnog pravila i dokaz nerasta. To je temelj tvoje tvrdnje o
  maskiranom NMF-u. Pročitaj Lovrin nacrt B4 kad bude spreman.
