# Matematička i eksperimentalna metodologija

Ovo je okvir potrebne dubine obrade i donošenja odluka, a ne dovršeno teorijsko poglavlje ili
prihvaćena specifikacija implementacije. Gillis je glavni izvor; dopunski su radovi navedeni
u [vodiču kroz literaturu](../research/LITERATURE.md). Funkcija cilja i algoritam još nisu odabrani.

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

Ovaj primjer ne određuje konačnu funkciju cilja. Objasniti njezine pretpostavke o pogrešci
i, ako je relevantno, usporediti je s formulacijom pomoću generalizirane KL divergencije.
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

Na početku implementacije odabrati podržano Python okruženje i zaključane verzije ovisnosti.
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
