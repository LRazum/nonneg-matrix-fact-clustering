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
