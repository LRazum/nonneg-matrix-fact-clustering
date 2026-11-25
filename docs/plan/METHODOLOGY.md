# Matematička i eksperimentalna metodologija

Ovo je okvir potrebne dubine obrade i donošenja odluka, a ne dovršeno teorijsko poglavlje ili
prihvaćena specifikacija implementacije. Gillis je glavni izvor; dopunski su radovi navedeni
u [vodiču kroz literaturu](../research/LITERATURE.md). Funkcija cilja i algoritam odabrani su u
[ADR-0003](adr/0003-choose-guitar-transcription-with-kl-nmf.md) (vidi odjeljak 2.1). Detalji
implementacije i eksperimenata dogovaraju se u zadacima iz [podjele rada](PODJELA.md).

## 1. Oznake i model

Dosljedno koristiti orijentaciju: $A\in\mathbb{R}_{\geq0}^{m\times n}$ ima po jedan uzorak
u svakom stupcu, $W\in\mathbb{R}_{\geq0}^{m\times r}$ sadrži komponente, a
$H\in\mathbb{R}_{\geq0}^{r\times n}$ njihove težine. Model je $A\approx WH$;
$\operatorname{rank}(WH)\leq r$. Navesti što retci, stupci i unutarnja dimenzija znače za
odabrane podatke. Ako kod pohranjuje uzorke po retcima, izričito objasniti transponiranje.

Objasniti aditivne kombinacije, konus generiran komponentama, kompresiju niskim rangom,
odnos prema skraćenom SVD-u i PCA-u te ograničenja interpretabilnosti. Nenegativni faktori
ne moraju biti jedinstveni, rijetki ni semantički smisleni.

## 2. Funkcija cilja i optimizacija

Referentna formulacija za raspravu jest

$$
\min_{W,H\geq0} f(W,H)=\frac12\lVert A-WH\rVert_F^2.
$$

Za odabranu temu ova formulacija je referentna metoda, a odabrana funkcija cilja opisana je u
odjeljku 2.1. Objasniti pretpostavke obiju formulacija o pogrešci i usporediti ih.
Za ovaj primjer izvesti gradijente:

$$
\nabla_W f=(WH-A)H^T,\qquad \nabla_H f=W^T(WH-A).
$$

Pokazati zašto fiksiranje jednog faktora daje konveksni potproblem najmanjih kvadrata uz
ograničenje nenegativnosti, dok je zajednički problem nekonveksan. Izvesti KKT uvjete prvog reda: nenegativnost
faktora, nenegativne elemente gradijenta u stacionarnoj točki te komplementarnost
$W\odot\nabla_W f=0$ i $H\odot\nabla_H f=0$. Objasniti zašto oni ne potvrđuju globalni
optimum zajedničkog problema.

Izričito obraditi nejednoznačnost zbog skaliranja i permutacija: za pozitivnu dijagonalnu
matricu $D$ vrijedi $(WD)(D^{-1}H)=WH$. Zato pojedinačne faktore općenito nije moguće
provjeravati zahtjevom da im se svi elementi točno podudaraju s drugim pokretanjem.
Normalizacija mijenja interpretaciju faktora i mora sačuvati rekonstrukciju ako joj je svrha
samo ukloniti nejednoznačnost skaliranja.

### 2.1 Odabrana formulacija (ADR-0003)

Za temu prepisivanja gitare $A$ je amplitudni spektrogram s $m$ frekvencijskih binova u retcima i
$n$ vremenskih okvira u stupcima. Stupci od $W$ su predlošci tonova, a retci od $H$ aktivacije.
Minimiziramo generaliziranu KL divergenciju

$$
D(A\,\|\,WH)=\sum_{i,j}\Bigl(a_{ij}\log\frac{a_{ij}}{(WH)_{ij}}-a_{ij}+(WH)_{ij}\Bigr),
\qquad 0\log0=0,
$$

s gradijentima $\nabla_H D=W^T(\mathbf 1-A\oslash WH)$ i $\nabla_W D=(\mathbf 1-A\oslash WH)H^T$.
Pritom je $\oslash$ dijeljenje po elementima, a $\mathbf 1$ matrica jedinica dimenzija
$m\times n$. Multiplikativna pravila Leeja i Seunga (L3, teorem 2) glase

$$
H\leftarrow H\odot\frac{W^T(A\oslash WH)}{W^T\mathbf 1},\qquad
W\leftarrow W\odot\frac{(A\oslash WH)H^T}{\mathbf 1H^T},
$$

uz dijeljenje po elementima. Frobeniusova formulacija gore ostaje referentna metoda. Izvode
razrađuju zadaci A3, B4 i C1. Izvor pravila su odjeljci 4–6, teoremi 1 i 2 u
[radu Leeja i Seunga](https://proceedings.neurips.cc/paper/2000/file/f9d1152547c0bde01830b7e8bd60024c-Paper.pdf).

### 2.2 Numerička izvedba B2

Za blok $b$ neka je $A_b$ oblika $m\times n_b$, $W$ oblika $m\times r$, a $H_b$ oblika
$r\times n_b$. Cilj je zbroj divergencija ili pogrešaka po blokovima. U jednoj iteraciji
najprije se izračuna svaki slobodni $H_b$ uz isto $W$. Zatim se ažurira slobodni $W$, uz zbroj
brojnika i nazivnika preko blokova. Kad se ažuriraju oba faktora, svaki nenulti stupac od $W$
dijeli se svojim zbrojem, a pripadni redci svih $H_b$ množe se istim zbrojem. Time se
$WH_b$ čuva do pogreške zaokruživanja. Blokovi se ne spajaju. Privremeni spektrogram i
rekonstrukcija zauzimaju prostor reda $m\max_b n_b$, uz spremljene faktore i akumulatore.

Podaci i faktori računaju se u aritmetici `float64`. Za omjer ažuriranja s nulom i u brojniku
i u nazivniku faktor je 1. Nulti elementi faktora zadržavaju se, a nulte komponente ostaju na
istim indeksima. Za $A\oslash WH$ mjesta s $A=0$ daju nulu. Pozitivan $A$ uz $WH=0$ izvan je
domene konačne KL divergencije. Funkcija cilja tada vraća $+\infty$, a `fit` prijavljuje
neuspjeh. Kada je ε pozitivan, djelitelji u ažuriranju i u $A\oslash WH$ imaju donju granicu ε
(zadano $10^{-12}$). S ε = 0 koriste se izvorni djelitelji i opisane konvencije za nule.
Funkcija cilja računa se na stvarnom $WH$ bez ε. Za bliske pozitivne vrijednosti $a$ i $v$
račun koristi $t=(a-v)/v$ i $(1+t)\log(1+t)-t$. Za $|t|<10^{-4}$ evaluira se razvoj do
člana $t^4$, a ostatak počinje članom $-t^5/20$. To smanjuje poništavanje znamenki blizu nule.

Povijest cilja uključuje početnu vrijednost i vrijednost nakon svake iteracije. Iteracija
završava kad cilj dosegne nulu, dosegne se najveći broj iteracija ili je nenegativni relativni
pad strogo manji od tolerancije. Tolerancija nula isključuje tu provjeru. Porast se zadržava
u povijesti. Nerast iz izvornog dokaza odnosi se na točna multiplikativna pravila pod njihovim
pretpostavkama. U kodu su porasti mogući zbog zaštite ε ili aritmetike s pomičnim zarezom.
Ograničenja stacionarnosti opisuje [Gillis, odjeljak 3.1.2](https://arxiv.org/abs/1401.5226v2).

### 2.3 Ponašanje na stvarnim spektrogramima (B5)

Brojevi u ovom odjeljku potječu iz pokretanja `20261125T092016Z-convergence-6f2ff9`
(`python -m experiments.convergence`, commit `eb94a59`, čisto radno stablo, jedna BLAS
dretva). Slike i sažetak zapisa nalaze se u mapi
[results/convergence/](../../results/convergence/README.md). Učitani su samo gitaristi 0–4;
gitarist 5 (testni u ovom foldu) nije učitan. Svaka postavka pokrenuta je za KL i Frobenius,
za ε jednak $10^{-12}$, $10^{-9}$ i 0 te za sjemena 0, 1 i 2. Svako pokretanje ima `tol=0`, pa
jedna povijest pokazuje gdje bi `fit` stao za svaku toleranciju.

- **Bez nadzora:** snimka `00_BN1-129-Eb_comp` ($511\times962$), $r=49$, $W_0$ i $H_0$ iz
  $U(0{,}5;\,1{,}5)$, 2000 iteracija.
- **Učenje s maskom:** 20 snimki, po dvije za svaki par gitarista 0–4 i načina (sjeme odabira 0),
  ukupno 26 438 okvira. $H_0$ je maska iz klavirske role s pozadinskim retkom. $W_0$ je iz
  $U(0{,}5;\,1{,}5)$ za 38 označenih tonova i pozadinu; ostalih 11 tonova ima nul-stupac.
  Ovo je zamjena za C3 prema njegovom planu, a ne konačna metoda. 200 iteracija.
- **Transkripcija:** ista snimka kao bez nadzora, koja nije u uzorku za učenje. $W$ je fiksan i
  jednak predlošcima iz učenja s maskom s istim ciljem i sjemenom. $H_0$ ima jedinice za
  nenulte predloške, prema planu C2. Ažurira se samo $H$, 1000 iteracija.

Opažanja su empirijska i vrijede za ove podatke i početke:

1. Ni u jednom od 54 pokretanja funkcija cilja nije porasla. To je u skladu s nerastom točnih
   pravila (L3, teoremi 1 i 2), ali to opažanje nije dokaz.
2. Povijesti za tri vrijednosti ε jednake su bit po bit. Donja granica ε, dakle, ni u jednom
   pokretanju nije promijenila izračun, a uz ε = 0 nijedno pokretanje nije palo. Izvedeno
   pravilo ovdje je jednako izvornom.
3. Iteracija u kojoj relativni pad prvi put padne ispod tolerancije, uz raspon po sjemenima. U
   zagradi je koliko je vrijednost cilja u toj iteraciji veća od vrijednosti u posljednjoj
   iteraciji:

   | Postavka | Cilj | $10^{-3}$ | $10^{-4}$ | $10^{-5}$ |
   |---|---|---|---|---|
   | Bez nadzora | KL | 117–132 | 481–588 (2,8–5,0 %) | 1545, 1879, iza 2000 |
   | Bez nadzora | Frobenius | 259–297 | 1499–1953 (0,4–5,3 %) | iza 2000 |
   | S maskom | KL | 15 | 27–29 (0,12–0,22 %) | 58–95 |
   | S maskom | Frobenius | 30–34 | 68–73 (0,34 %) | 165–171 |
   | Transkripcija | KL | 23 | 46 (0,17 %) | 88 |
   | Transkripcija | Frobenius | 35 | 84–86 (0,52–0,55 %) | 210–217 |

   Relativni padovi KL-a i Frobeniusa nisu u istim jedinicama, pa se brojevi iteracija dvaju
   ciljeva ne uspoređuju izravno. Razlika do posljednje iteracije nije udaljenost od optimuma.
   Bez nadzora relativni pad po iteraciji nije monoton, pa pravilo zaustavljanja može stati na
   privremenom usporavanju. Kod transkripcije, gdje je problem po $H$ konveksan, pad glatko
   opada.
4. Bez nadzora različita sjemena završavaju na različitim vrijednostima: KL od 3109,7 do 3177,4,
   a Frobenius od 1114,0 do 1125,4 nakon 2000 iteracija. To je u skladu s nekonveksnošću
   punog problema. S maskom se završne vrijednosti razlikuju najviše 0,03 % (KL) i 0,12 %
   (Frobenius).
5. Vrijeme po iteraciji (medijan, jedna dretva, uključuje izračun cilja u svakoj iteraciji)
   je okvirno, jer računalo nije bilo izolirano za mjerenje:

   | Postavka | KL | Frobenius |
   |---|---|---|
   | Bez nadzora | 24,3 ms | 14,6 ms |
   | S maskom | 694 ms | 128 ms |
   | Transkripcija | 20,2 ms | 4,3 ms |

   Jedan izračun KL cilja javnom funkcijom traje 69–81 % vremena KL iteracije. To je gornja
   procjena, jer javna funkcija dodatno provjerava ulaz. Uz isti omjer KL iteracija na
   cijelom skupu za učenje jednog folda (oko 390 000 okvira) trajala bi oko 10 s.
6. Uz podatke `fit` je dodatno zauzeo najviše 73 MiB pri učenju s maskom (KL, 103 MiB
   podataka) i 32 MiB bez nadzora. Za cijeli fold to treba ponovno izmjeriti.

**Prijedlog za Z2** (#24); ovo je prijedlog, a ne odluka:

- učenje predložaka: `tol` $=10^{-4}$, uz `max_iter` $=200$ kao gornju granicu;
- transkripcija: `tol` $=10^{-5}$, uz `max_iter` $=500$, jer je jedna snimka jeftina;
- ε ostaje $10^{-12}$: ovdje nije utjecao, a štiti od dijeljenja nulom;
- razmotriti rjeđi izračun funkcije cilja u `fit`, jer on nosi većinu vremena KL iteracije.
  To mijenja pravilo zaustavljanja, pa traži odluku tima, izmjenu B2 i testove;
- brojeve iteracija provjeriti na cijelom foldu kada postoje C3 i C4, jer je ovdje uzorak od 20
  snimki.

## 3. Izvod odabranog algoritma

Nakon odabira algoritma izvesti njegova stvarna ažuriranja iz funkcije cilja, umjesto pukog
navođenja pseudokoda. Objasniti redoslijed izmjeničnog ažuriranja, dimenzije, inicijalizaciju,
nenegativnost, računalni trošak i kriterij zaustavljanja. Ako su odabrana multiplikativna
ažuriranja, obraditi njihovu vezu sa skaliranim gradijentnim korakom i argument pomoću
pomoćne funkcije kojim se pokazuje da funkcija cilja ne raste.

Razdvojiti tri tvrdnje: nerast funkcije cilja, konvergenciju i stacionarnost iterata te globalnu
optimalnost. Točno navesti pretpostavke koje podupiru pojedinu tvrdnju. Raspraviti nule koje
ostaju nule, nulte nazivnike, neaktivne komponente, konačnu preciznost i svaku zaštitu koja se
stvarno koristi u kodu; dodavanje epsilona mijenja implementirano pravilo i traži objašnjenje.

Uključiti barem jednu malu razrađenu iteraciju ili neovisno provjerljiv numerički primjer.
Usporedba s drugim algoritmom mora biti opravdana pitanjem; ovaj je plan ne zahtijeva.

## 4. Od stvarnog problema do matrice

Prije odabira podataka zapisati pitanje i što bi korisna komponenta ili težina predstavljala.
Zabilježiti izvor, licencu i pristup, verziju ili kontrolni zbroj, uzorke i značajke, nedostajuće
vrijednosti, predobradu i orijentaciju matrice. Objasniti zašto prikaz i funkcija cilja imaju
smisla za ta mjerenja. Ne pomicati negativne podatke prešutno samo da bi se NMF mogao pokrenuti.

Ako je primjena klasteriranje, definirati pretvorbu težina u dodjelu klasterima, uključujući
normalizaciju i nejednoznačne dodjele. Prikaz temama ili komponentama i čvrsta particija
različiti su rezultati. Težine uz dodatne pretpostavke mogu predstavljati vjerojatnosti.

### 4.1 Podaci i učitavanje (A1)

Koristimo GuitarSet 1.1.0 (Zenodo 3371780, CC BY 4.0): 360 snimki šest gitarista, za svaki od
30 isječaka po jednu snimku pratnje (`comp`) i jednu solo snimku (`solo`). Ulaz je snimka
mikrofona (mono, 16 bita, 44 100 Hz), a referentne note potječu iz heksafonskog pickupa.
Izvor, kontrolni zbrojevi, provjere i poznate greške zapisani su u
[opisu podataka](../../data/README.md); arhive i datoteke provjeravaju se prema MD5 vrijednostima
i manifestu `data/manifest.csv`.

`gitara.data.load_audio` dijeli uzorke s $2^{15}$, pa su u $[-1,1)$, a zatim ih preuzorkuje na
22 050 Hz funkcijom `scipy.signal.resample_poly`, čiji niskopropusni filtar uklanja sadržaj iznad
nove Nyquistove frekvencije od 11 025 Hz prije prorjeđivanja. Harmonici koje koristimo leže
ispod oko 5,5 kHz. Razina se ne normalizira i vrijednosti se ne odrezuju: generalizirana KL
divergencija je homogena, $D(cA\,\|\,cV)=c\,D(A\,\|\,V)$, pa bi normalizacija promijenila
težinu snimki u funkciji cilja. Najveće vrijednosti snimki razlikuju se oko 17 puta; odluka o
normalizaciji pripada provjeri pretprocesiranja (A4).

`gitara.data.load_notes` vraća note iz anotacija `note_midi` kao intervale $[t_0, t_0+d]$ u
sekundama, izvorne necijele MIDI visine i žice 0–5, sortirano po početku. Zaokruživanje visina
na tonove iz `PITCHES` dio je klavirske role (A2). Postupanje s poznatim greškama (dvije snimke
s pomaknutim anotacijama, unisoni i duplikati na susjednim žicama) predlaže se u issueu #7 i
čeka potvrdu tima.

### 4.2 Spektrogram i klavirska rola (A2)

`gitara.spectrogram.stft_magnitude` računa amplitudni spektrogram
$A_{kt}=\bigl|\sum_{n=0}^{N-1} w[n]\,y[tH+n-N/2]\,e^{-2\pi i kn/N}\bigr|$, gdje je
$w[n]=\tfrac12-\tfrac12\cos(2\pi n/N)$ periodični Hannov prozor, a signal je s obje strane
dopunjen s $N/2$ nula. Okvir $t$ centriran je na uzorku $tH$, pa je
$t_j = jH/f_s$; to je zajedničko sučelje iz [podjele rada](PODJELA.md). Implementacija koristi
`numpy.fft.rfft`, a test je uspoređuje sa `scipy.signal.stft` (podudaranje do $10^{-9}$).

Početni parametri (konačan izbor u A6) su $f_s = 22\,050$ Hz, $N = 2048$ (92,9 ms),
$H = 512$ (23,2 ms, preklapanje 75 %) i $f_{\max} = 5{,}5$ kHz, pa je
$\Delta f = f_s/N \approx 10{,}77$ Hz i $m = 511$ binova. Ispod granice ostaje 66 harmonika
tona E2 (82,4 Hz), 6 harmonika tona A5 (880 Hz, najviši ton u anotacijama) i 4 harmonika tona E6
(1318,5 Hz, vrh raspona `PITCHES`). Polustepen ispod oko 181 Hz uži je od jednog bina (kod E2
iznosi 4,9 Hz), pa se susjedni duboki tonovi razlikuju po višim harmonicima, a ne po osnovnoj
frekvenciji. Dulji prozor poboljšao bi frekvencijsku, a pogoršao vremensku rezoluciju.

Amplituda se ne normalizira: sinus amplitude $a$ točno na frekvenciji bina daje $a\sum_n w[n]/2$.
Model $A\approx WH$ pretpostavlja da se amplitude nota zbrajaju. Za kompleksne spektre to vrijedi
točno, a za module vrijedi samo nejednakost trokuta $|X_1+X_2|\le|X_1|+|X_2|$; jednakost je
približna kad se spektri ne preklapaju. Kod tonova s zajedničkim harmonicima (npr. oktava) zbroj
modula može precijeniti stvarni spektar. Test to ilustrira na dvama udaljenim sinusima
(relativna razlika ispod $10^{-4}$ u unutrašnjim okvirima); u rubnim okvirima nagli početak i
kraj signala razlijevaju energiju po svim binovima.

`gitara.spectrogram.piano_roll` vraća logičku matricu $R\in\{0,1\}^{K\times n}$ s
$R_{kt}=1$ ako neka nota visine $\lfloor p+\tfrac12\rfloor=\texttt{PITCHES}[k]$ zadovoljava
$t_0\le t_j<t_0+d$. Note izvan raspona `PITCHES` (MIDI 40–88, $K = 49$) izostavljaju se uz
upozorenje s njihovim brojem. Najkraća nota traje 0,029 s, dulje od koraka od 23,2 ms, pa svaka
nota pokriva barem jedan okvir.

Na svih 360 snimki (2026-11-24): svaka ima 511 binova i 621–1969 okvira (14,4–45,7 s), ukupno
472 560 okvira (oko 3,05 h zvuka). Spektrogram svih snimki u `float64` zauzeo bi oko 1,9 GB, pa
se računa po snimci. Najveća vrijednost u $A$ je 368,5. Nijedna nota nije bez okvira i nijedna
nije izvan raspona 40–88.

## 5. Provjera implementacije

Na početku implementacije postaviti Python 3.12. Ovisnosti zaključati uz kod koji ih prvi koristi.
Numeričku metodu omogućiti pozivati neovisno o bilježnici ili stvarnom skupu podataka.
Obuhvatiti provjeru ulaza, nenegativnost i konačne izlazne vrijednosti, malu poznatu
rekonstrukciju, odgovarajuće ponašanje funkcije cilja, zaustavljanje i rubne slučajeve
odabrane metode.

Koristiti opravdane tolerancije i neovisne izračune. Kada se biblioteka koristi kao referenca,
uskladiti funkcije cilja i postavke te uzeti u obzir nejedinstvenost. Testovi i CI koriste
male sintetičke podatke ili testne podatke koje je dopušteno dalje distribuirati te ne traže
preuzimanje cijelog skupa podataka ni plaćenu uslugu.

## 6. Eksperimenti i evaluacija

Prije glavnih pokretanja dogovoriti pitanja, rangove, sjemena generatora i inicijalizacije,
postavke zaustavljanja, referentnu metodu, metrike i raspoložive računalne resurse.
Evaluaciju u domeni odabrati nakon što je poznata primjena; jedna metrika klasteriranja ili
podjela za klasifikaciju ne odgovara svakom NMF problemu.

Za svako prikazano pokretanje navesti:

- Izvor i verziju ulaza ili kontrolni zbroj te predobradu i postavke.
- Reviziju koda i postojanje nezabilježenih izmjena; ako commit još ne postoji, navesti tu
  činjenicu i identificirati radnu snimku umjesto izmišljanja revizije.
- Python okruženje i ovisnosti, rang, funkciju cilja, algoritam i sve numeričke postavke.
- Sjeme generatora i inicijalizaciju, razlog zaustavljanja, broj iteracija i vrijednost
  funkcije cilja ili pogreške.
- Metrike domene i interpretaciju te svaki neuspjeh ili izostanak konvergencije; hardver,
  postavke dretvi i obuhvat mjerenja vremena pri usporedbama brzine.

Sirove i opsežne izlaze držati lokalno, uz identifikator pokretanja. Sačuvati dovoljno
metapodataka te male odabrane tablice i slike za svaku prikazanu tvrdnju. Ne prebrisati jedini
zapis pokretanja čiji su rezultati prikazani. Stabilnost kroz dogovorena sjemena i rangove,
interpretabilnost i ograničenja raspraviti odvojeno od kvalitete rekonstrukcije. Ako postoji
izdvojeni skup za evaluaciju, parametre predobrade odrediti na dijelu za učenje i razvoj,
a konačni evaluacijski skup ne koristiti za podešavanje.

## 7. Pisano i usmeno objašnjenje

Seminar povezuje problem, matricu, funkciju cilja, izvod, kod, eksperimente i zaključke.
Teorijske izvore citirati navođenjem odjeljka ili teorema gdje je moguće. Projektne slike
povezati s pokretanjem koje ih je proizvelo i razlikovati ih od preuzetih ilustracija.
Seminar i prezentacija pišu se na hrvatskom. Prezentacija koristi iste definicije i rezultate.
Sva tri člana vježbaju objašnjavanje cijelog postupka.
