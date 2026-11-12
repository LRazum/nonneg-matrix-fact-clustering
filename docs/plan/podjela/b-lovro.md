# Plan osobe B: Lovro, nit „od matrice do faktora”

Zajednička pravila, sučelja i faze opisani su u [podjeli rada](../PODJELA.md). Ovaj plan je
prijedlog; mijenja se u PR-u ili issueu. Brojevi u zagradama označavaju GitHub issuee.

## Ukratko

Tvoja nit je algoritam: iz matrice $A$ dobiti nenegativne faktore i znati točno što je o tom
postupku dokazano. Uz to postavljaš okruženje i zapis podrijetla na koje se oslanjaju svi.

- **Matematika:** gradijenti; uvjeti optimalnosti na nenegativnom ortantu; izvod
  multiplikativnih pravila; dokaz nerasta pomoću pomoćne funkcije (L3, teorem 2, i ukratko
  teorem 1); praktični detalji (inicijalizacija, normalizacija, ε, zaustavljanje, složenost).
- **Kod:** numeričko okruženje i CI, `gitara.nmf` s temeljitim testovima i `gitara.provenance`.
- **Eksperimenti:** ponašanje algoritma na stvarnim spektrogramima, konvergencija KL i
  Frobeniusa te stabilnost kroz sjemena i foldove.
- **Seminar i prezentacija:** poglavlja i slajdovi o uvjetima optimalnosti, multiplikativnim
  pravilima, dokazu nerasta i praktičnim detaljima.
- **Pregled:**
  - pregledavaš Mislavovu nit C: PR-ove, neovisan izvod dokaza (B9) i reprodukciju (Z4);
  - na prolazima objašnjavaš nit C;
  - tvoju nit pregledava Sara.

**Pitanja za obranu iz skripte koja su „tvoja”:** 10–15. Na probnoj obrani dobit ćeš i pitanja
iz tuđih niti.

## Redoslijed

| Faza | Zadatak | Ovisi o | Tko čeka tebe |
|---|---|---|---|
| 0 | Z0 dogovor (#5) | — | svi |
| 0 | B1 okruženje, provjere i CI (#6) | Z0 | sav kod |
| 1 | B2 jezgra NMF-a (#10) | B1 | Z1, B5, C3 |
| 1 | B3 zapis podrijetla (#11) | B1 | A4, B5, C4 |
| 1 | B4 matematika: optimalnost, pravila i nerast | Z0 | A9, B7 |
| 2 | B5 algoritam na stvarnim spektrogramima (#19) | A2, B2, B3 | Z2, B6 |
| 2 | B9 neovisna provjera dokaza niti C | C1 | Z3 |
| 3 | B6 konvergencija i stabilnost (#28) | B5, C3 | B7, Z4 |
| 3 | B7 seminar: poglavlja niti B | B4–B6 | Z5 |
| 4 | B8 slajdovi niti B | B7 | Z6 |

B1 je usko grlo: dok ne postoji okruženje, nitko ne može spojiti kod. Napravi ga odmah nakon Z0.

## B1: numeričko okruženje, provjere i CI (#6)

**Cilj:** jedna podržana naredba za postavljanje, testove i CI. Završna provjera tada stvarno
pokreće numeričke testove.

1. Postavi Python 3.12. Koristi postojeći `unittest` za početnu provjeru. Ovisnost dodaj i
   zaključaj u istoj promjeni koja je prva koristi.
2. Uvedi `pyproject.toml`, `uv.lock`, paket `gitara` u rasporedu `src/` i test uvoza.
   Naredba za postavljanje je `uv sync --locked`.
3. Napiši `tools/check_project.py`:
   - pokreće testove u projektnom okruženju;
   - nedostaje li okruženje, ispisuje jasnu pogrešku i vraća kod različit od nule;
   - nikad ne javlja uspjeh kad provjera nije pokrenuta.

   Za njegovu logiku dodaj testove u `tools/`, kao za ostale alate.
4. U `.github/workflows/ci.yml` dodaj posao „Numeričke provjere”. On postavlja isto okruženje i
   pokreće `tools/check_project.py`. U zaštiti grane `main` dodaj ga kao obveznu provjeru.
5. Iz popisa `PLANNED` u `tools/check_docs.py` ukloni stvorene putanje. Ažuriraj:
   - naredbe u `AGENTS.md` (odjeljak 5);
   - [tijek rada](../PIPELINE.md) i `README.md`;
   - docstring u `tools/check_before_stop.py`.

   Upute uskladi s [ADR-0006](../adr/0006-start-with-python-312-and-simple-interfaces.md).
6. Zapiši varijable za broj dretvi (`OPENBLAS_NUM_THREADS`, `OMP_NUM_THREADS`,
   `MKL_NUM_THREADS`). One su važne za mjerenje vremena i za memoriju na računalima od oko
   8 GB RAM-a.

**Gotovo kada:** CI je zelen s novim poslom. Sara i Mislav kod sebe postave okruženje i pokrenu
`python3 tools/check_before_stop.py` bez pogreške. Sara je pregledala PR.

## B2: jezgra NMF-a (#10)

**Cilj:** `gitara.nmf` s KL i Frobeniusovim multiplikativnim pravilima. Kod prati izvod iz B4.

1. **Funkcije cilja:**
   - `kl_divergence(A, V)` računa $\sum(a\log(a/v)-a+v)$, uz $0\log0=0$; za $v=0$ i $a>0$
     vraća $+\infty$, bez prešutnog ε;
   - `frobenius(A, V)` računa $\tfrac12\|A-V\|_F^2$.
2. **Glavna funkcija** prima više blokova sa zajedničkim $W$, jer se predlošci uče na mnogo
   snimki istodobno:

   ```python
   fit(blocks, W0, H0s, *, objective="kl", update_W=True, update_H=True,
       max_iter=200, tol=1e-4, eps=1e-12, normalize=True) -> NMFResult
   ```

   `NMFResult` sadrži `W`, `Hs`, `objective` (vrijednosti po iteracijama), `n_iter`,
   `stop_reason` (`"tol"`, `"max_iter"` ili `"zero_objective"`) i `inactive` (indekse
   komponenti s nul-stupcem u $W$ ili nul-retkom u svakom bloku $H_b$).
3. **Pravila**, uz $\oslash$ kao dijeljenje po elementima:
   - KL:
     $H\leftarrow H\odot\bigl(W^T(A\oslash(WH))\bigr)\oslash(W^T\mathbf 1)$ i
     $W\leftarrow W\odot\sum_b\bigl((A_b\oslash(WH_b))H_b^T\bigr)\oslash\sum_b(\mathbf 1H_b^T)$;
   - Frobenius:
     $H\leftarrow H\odot(W^TA)\oslash(W^TWH)$ i
     $W\leftarrow W\odot\sum_b A_bH_b^T\oslash\bigl(W\sum_b H_bH_b^T\bigr)$.

   Djelitelji u ažuriranju i u $A\oslash(WH)$ imaju donju granicu ε. S ε = 0 koristi se
   izvorni djelitelj. Teorem vrijedi za pravilo bez ε pod pretpostavkama izvornog dokaza.
   Za omjer ažuriranja s nulom u brojniku i nazivniku koristi faktor 1, koji čuva postojeću
   vrijednost. U $A\oslash(WH)$ koristi nulu na mjestima gdje je $A=0$. KL cilj ima vrijednost
   $+\infty$ ako je $A>0$ na mjestu gdje je $WH=0$. `fit` takvu početnu ili ažuriranu
   rekonstrukciju prijavljuje kao numerički neuspjeh.
4. **Redoslijed** u jednoj iteraciji: najprije svi $H_b$, zatim $W$. Na kraju iteracije
   normaliziraj stupce od $W$ na $\ell_1$-normu 1 i istim faktorima pomnoži retke od $H_b$.
   Preskoči nul-stupce i primijeni preskaliranje samo kad se ažuriraju oba faktora.
   Umnožak $WH$ i funkcija cilja ostaju isti, što provjeri testom.
5. **Zaustavljanje:** cilj nula, nenegativni relativni pad $(f_t-f_{t+1})/f_t<\texttt{tol}$
   ili `max_iter`. Tolerancija nula isključuje provjeru relativnog pada. Povijest uključuje
   početnu vrijednost i eventualne poraste. Razlog zaustavljanja uvijek se vraća.
6. **Provjera ulaza:**
   - oblici blokova, $W_0$ i $H_0$ su usklađeni;
   - sve je konačno i nenegativno;
   - nul-stupac u $W_0$ i nul-redak u svakom $H_{0,b}$ dopušteni su i zadržavaju svoje mjesto.

   Za nevaljane oblike ili vrijednosti izaziva se `ValueError`.
7. **Memorija:** blokovi se obrađuju jedan po jedan, a zbrojevi za $W$ akumuliraju se. Matrica
   svih snimki za učenje ($m\approx500$ binova, stotine tisuća okvira) zauzela bi nekoliko GB,
   pa je ne spajaj.
8. **Testovi** (modul `test_nmf`). Testovi provjeravaju svojstva, a ne prepisuju implementaciju:
   1. mali točan primjer: za $A=W_*H_*$ ranga 2 funkcija cilja pada blizu nule, a $WH$ je blizu
      $A$. Ne traži se jednakost faktora (nejedinstvenost);
   2. funkcija cilja ne raste na nasumičnim nenegativnim podacima, za KL i Frobenius, unutar
      relativne tolerancije koju obrazložiš (zbog ε i aritmetike s pomičnim zarezom);
   3. izlazi su nenegativni i konačni;
   4. nule ostaju nule: elementi $H_0$ jednaki nuli ostaju nula, što je temelj maskiranog
      NMF-a u C3;
   5. jedna iteracija na primjeru $2\times2$ jednaka je vrijednostima koje izračunaš ručno u
      B4 i upišeš u test kao brojeve;
   6. normalizacija ne mijenja $WH$ ni funkciju cilja;
   7. uz `update_W=False` matrica $W$ ostaje točno ista;
   8. dva bloka daju isto što i jedan spojeni blok;
   9. negativan ulaz, NaN i krivi oblici izazivaju `ValueError`. Nulta komponenta s valjanom
      rekonstrukcijom ostaje na istom indeksu, a nedopuštena KL rekonstrukcija se prijavljuje;
   10. `kl_divergence(A, A) == 0`, vrijednost je nenegativna na nasumičnim podacima, a
       konvencija $0\log0$ radi.

**Gotovo kada:** svi testovi prolaze u CI-ju; Sara je pregledala kod i matematiku; Mislav može
koristiti `fit` u C2 i C3.

## B3: zapis podrijetla pokretanja (#11)

**Cilj:** `gitara.provenance`, tako da svaki broj u seminaru ima izvor (AGENTS.md, pravilo 6).

1. `start_run(name, config)` vraća zapis s ovim podacima:
   - identifikator (vrijeme i kratki hash);
   - naredba i konfiguracija;
   - git commit i podatak ima li necommitiranih promjena. Ako ih ima, sprema se i diff;
   - verzija Pythona i paketa, platforma i varijable dretvi;
   - MD5 manifesta podataka i sjemena.
2. `finish_run(record, status, results, errors)` sprema zapis u novu mapu unutar
   results/runs/ (izvan Gita). Nikad ne prepisuje postojeću mapu. Neuspjelo pokretanje također
   se sprema, sa statusom i porukom pogreške.
3. Testovi:
   - u privremenom git repozitoriju zapis prepoznaje necommitirane promjene;
   - postojeća mapa se ne prepisuje;
   - neuspjelo pokretanje je zapisano.

**Gotovo kada:** Sara (A4) i Mislav (C4) mogu ga koristiti; Sara je pregledala PR.

## B4: matematika optimalnosti, multiplikativnih pravila i nerasta

**Cilj:** nacrt tvojih poglavlja seminara s potpunim izvodima. Skripta je polazište, a ne gotov
tekst. Svaki izvod prođi na papiru; uz svaku tvrdnju označi je li citirana, vlastiti izvod ili
empirijsko opažanje.

1. **Gradijenti.** Za KL:
   $\partial D/\partial h_{kj}=\sum_i w_{ik}\bigl(1-a_{ij}/(WH)_{ij}\bigr)$, tj.
   $\nabla_HD=W^T(\mathbf 1-A\oslash WH)$ i $\nabla_WD=(\mathbf 1-A\oslash WH)H^T$.
   Za Frobenius: $\nabla_Hf=W^T(WH-A)$. Izvor: propozicija o gradijentima u skripti.
2. **Uvjeti optimalnosti.**
   - Nužni uvjeti prvog reda na nenegativnom ortantu: $H\ge0$, $\nabla_Hf\ge0$ i
     $H\odot\nabla_Hf=0$ (isto za $W$). Dokaz preko funkcije jedne varijable po koordinati.
   - Uz konveksnost uvjeti su i dovoljni; to je važno za potproblem po $H$.
   - Primjer: $(0,0)$ je stacionarna točka Frobeniusove funkcije cilja, a nije lokalni
     minimum. Objasni i zašto je kod KL divergencije domena drukčija.
   - Izvori: L1, odjeljak 3.1.1; L4, odjeljak 3.1; teorem o nužnim uvjetima i primjer u skripti.
3. **Izvod multiplikativnih pravila.**
   - Gradijentni korak $H\leftarrow H-\eta\odot\nabla_Hf$ s korakom po elementu
     $\eta_{kj}=h_{kj}/(W^T\mathbf 1)_{kj}$ daje KL pravilo.
   - Uz $\eta_{kj}=h_{kj}/(W^TWH)_{kj}$ dobiva se Frobeniusovo pravilo.
   - Svojstva: pravila čuvaju nenegativnost, a nule ostaju nule. Nepomična točka s
     $h_{kj}>0$ ima $\partial f/\partial h_{kj}=0$; za $h_{kj}=0$ to ne vrijedi.
   - Izvori: L3, odjeljci 4–5; L1, odjeljak 3.1.2; propozicija o svojstvima pravila u skripti.
4. **Pomoćna funkcija.** Ako je $G(h,h')\ge F(h)$ i $G(h,h)=F(h)$, onda
   $h^{t+1}=\arg\min_hG(h,h^t)$ zadovoljava $F(h^{t+1})\le F(h^t)$. Izvor: L3, lema 1.
5. **Majoranta za KL.**
   - Konkavnost logaritma (Jensen) daje
     $-\log\sum_kw_kh_k\le-\sum_k\alpha_k\log\frac{w_kh_k}{\alpha_k}$, uz
     $\alpha_k=w_kh^t_k/\sum_lw_lh^t_l$.
   - Iz toga se gradi $G$ za stupac od $H$. Minimizacija $G$ daje točno KL pravilo
     (L3, lema 3 i teorem 2).
   - Pažljivo obradi nule i pretpostavke: $W$ bez nul-stupca, $H$ bez nul-retka.
6. **Frobenius, ukratko** (referentna metoda): kvadratna majoranta s
   $K(h^t)=\mathrm{diag}\bigl((W^TWh^t)_k/h^t_k\bigr)$ i dokaz da je $K-W^TW$ pozitivno
   semidefinitna (L3, lema 2 i teorem 1).
7. **Praktični detalji:**
   - inicijalizacija pozitivnim slučajnim brojevima uz zapisano sjeme (L1, 3.1.8);
   - normalizacija i zašto ne mijenja funkciju cilja;
   - ε i kako mijenja pravilo, pa teorem više ne vrijedi doslovno;
   - zaustavljanje (L1, 3.1.7): relativni pad i najveći broj iteracija;
   - složenost $O(mnr)$ po iteraciji i memorija.
8. **Mali primjer.** Za $A=\left[\begin{smallmatrix}1&3\\2&4\end{smallmatrix}\right]$,
   $W_0=\left[\begin{smallmatrix}1&1\\1&2\end{smallmatrix}\right]$ i $H_0$ pun jedinica,
   stupci od $W_0H_0$ jednaki su $(2,3)^T$. Omjer $A\oslash(W_0H_0)$ ima retke
   $(1/2,3/2)$ i $(2/3,4/3)$. Nakon množenja s $W_0^T$ prvi redak dijelimo s 2, a drugi s 3:
   dobivamo $H_1$ s retcima $(7/12,17/12)$ i $(11/18,25/18)$.
   Zatim $W_0H_1$ ima retke $(43/36,101/36)$ i $(65/36,151/36)$. Oba retka od $H_1$
   imaju zbroj 2. Uvrštavanjem u pravilo za $W$ dobivamo retke
   $(4350/4343,4336/4343)$ i $(9801/9815,19644/9815)$. Ovi brojevi su referenca
   testa B2 uz ε = 0 i isključenu normalizaciju.

**Gotovo kada:** Sara je neovisno prošla nacrt (A9) i raspravila nejasnoće s Lovrom.

## B5: algoritam na stvarnim spektrogramima (#19)

**Cilj:** prije glavnog eksperimenta znati koliko iteracija treba, koliko to traje i
ponaša li se algoritam kako teorija kaže.

Sve radi samo na gitaristima za učenje, nikad na testnom.

1. Krivulje funkcije cilja za KL i Frobenius na jednoj snimki (bez nadzora) i pri učenju
   predložaka s maskom (u dogovoru s Mislavom). Izmjeri najveći relativni porast; očekuje se
   nula do numeričke tolerancije.
2. Vrijeme po iteraciji i memorija. KL iteracija skuplja je od Frobeniusove jer računa
   $A\oslash WH$ po elementu. Izmjeri koliko.
3. Iz krivulja predloži broj iteracija ili toleranciju za učenje i transkripciju. Odluka ide u
   Z2.
4. Utjecaj ε: vrijednosti $10^{-12}$ i $10^{-9}$ te bez ε gdje je to sigurno.
5. `python -m experiments.convergence` sa zapisom podrijetla; slike i JSON u `results/`.

## B6: konvergencija i stabilnost (#28)

1. **KL prema Frobeniusu:**
   - broj iteracija do relativnog pada $10^{-4}$ i $10^{-5}$;
   - vrijeme po iteraciji te broj iteracija i vrijeme transkripcije.

   Relativni padovi dviju različitih funkcija nisu iste jedinice; to izričito napiši.
2. **Stabilnost predložaka:**
   - kosinusna sličnost istog tona kroz sjemena i kroz foldove (maska fiksira permutaciju);
   - kod NMF-a bez nadzora na jednoj snimki pokaži nejedinstvenost: komponente se uparuju
     tek nakon permutacije (Hungarian) i skaliranja. To je eksperimentalna ilustracija
     Mislavove matematike.
3. **Udaljenost od stacionarnosti** na kraju: npr. $\|\min(H,\nabla_Hf)\|$. Usporedi s onim
   što je dokazano. Nerast je teorem, a mala udaljenost na kraju je opažanje.

**Gotovo kada:** slike konvergencije i stabilnosti imaju identifikatore pokretanja; zaključci su
u nacrtu poglavlja; sva sjemena su prikazana, ne samo povoljna.

## B7: seminar, poglavlja niti B

Nacrt iz B4 dopuni:

1. **Uvjeti optimalnosti:** gradijenti, KKT i primjer $(0,0)$.
2. **Multiplikativna pravila:** izvod, svojstva i ručno izračunata iteracija.
3. **Dokaz nerasta:** cijeli dokaz za KL i skica za Frobenius.
4. **Praktični detalji:** ε, normalizacija, zaustavljanje i složenost, uz rezultate iz B5 i B6.

Svaka tvrdnja u kodu (npr. „funkcija cilja ne raste”) ima pripadajući test ili pokretanje.

## B8: slajdovi niti B

Oko 4–6 slajdova:

- zašto puni problem nije lagan, a koraci jesu;
- pravilo kao skalirani gradijentni korak;
- slika pomoćne funkcije koja leži iznad funkcije cilja;
- krivulje konvergencije, s porukom što je dokazano, a što samo opaženo.

## B9: neovisna provjera dokaza niti C

Ti si recenzent Mislavove niti. Kad nacrt C1 bude spreman, na papiru neovisno izvedi:

1. nejedinstvenost: $(WD)(D^{-1}H)=WH$ i permutacije; normalizacija čuva $WH$;
2. primjer nekonveksnosti punog problema i dokaz konveksnosti po $H$ uz fiksni $W$. Za KL je
   Hessijan po stupcu $h$ jednak $\sum_ia_iw_iw_i^T/(w_i^Th)^2\succeq0$;
3. što jest, a što nije dokazano o konvergenciji multiplikativnih pravila: tvrdnja iz L3 nakon
   leme 1 i kritika u L4, odjeljak 3.1; primjer zapinjanja u točki koja nije stacionarna;
4. propoziciju o maskiranom NMF-u.

Razlike i nejasnoće prođi s Mislavom. Na prolazima Z1 i Z3 objašnjavaš nit C, a u Z4
reproduciraš Mislavov glavni eksperiment.

## Što trebaš znati iz tuđih niti

- **Iz niti A:** zašto je spektar akorda približno zbroj spektara i zašto je KL divergencija
  povezana s Poissonovim modelom. Pročitaj Sarin nacrt A3.
- **Iz niti C:** ovo je tvoj recenzentski posao, pa ćeš ga znati najbolje: maskirani NMF,
  transkripcija i ugniježđena unakrsna provjera.
