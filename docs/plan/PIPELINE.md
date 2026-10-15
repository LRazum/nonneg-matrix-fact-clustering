# Tijek rada

Struktura repozitorija, automatske provjere i put od istraživačkog pitanja do reproducibilnih
rezultata seminara. Postavljanje tijeka rada odvojeno je od numeričkog rada koji će tim
odabrati kasnije.

## Struktura repozitorija

Ovo stablo ručno održavajte usklađenim; stablo u bloku koda nije zamjena za provjerene poveznice.

```text
AGENTS.md                           jedinstveni izvor pravila repozitorija
CLAUDE.md                           @AGENTS.md
README.md                           svrha, tim, trenutačno stanje i naredbe
.gitignore
docs/
  INDEX.md                          indeks dokumentacije
  CHANGE_PROTOCOL.md                zadaci, pregled i povezana ažuriranja dokumentacije
  plan/
    PROJECT.md                      opseg, materijali za predaju i otvorene odluke
    TASKS.md                        mali zadaci i njihove ovisnosti
    METHODOLOGY.md                  matematički i eksperimentalni plan
    PIPELINE.md                     ova datoteka
    AI_REVIEW.md                    nalazi, dnevna provjera i postupak pregleda
    adr/                            zapisi odluka
  research/
    LITERATURE.md                   bibliografski podaci, uloge izvora i bilješke uz čitanje
tools/
  check_docs.py
  test_check_docs.py
  daily_check.py
  test_daily_check.py
  check_before_stop.py               zajedničke završne provjere
  test_check_before_stop.py
  check_project.py                   planirano: dogovorene numeričke provjere
.github/
  pull_request_template.md
  workflows/
    ci.yml
    daily-check.yml
.claude/
  settings.json                      konfiguracija Claude Stop hooka
  hooks/check_before_stop.py         omotač oko zajedničke završne provjere
.codex/
  hooks.json                         konfiguracija Codex Stop hooka; povjerenje je lokalno
pyproject.toml                       planirano: dogovoreno numeričko okruženje
uv.lock                              planirano: zaključane numeričke ovisnosti
src/                                 planirano: višekratno upotrebljiva Python implementacija
tests/                               planirano: numeričke provjere i provjere podataka
experiments/                         planirano: konfiguracije i reproducibilne ulazne točke
data/                                planirano: dokumentirana nabava/priprema podataka
results/                             planirano: označena izvođenja, slike i tablice
seminar/                             planirano: izvor pisanog seminara
presentation/                        planirano: izvor prezentacije
```

Planirane mape uvode se kada za njih postoji stvaran sadržaj. Naziv mape ne određuje skup
podataka, algoritam rješavanja ni format dokumenta. Predložena datoteka zaključanih ovisnosti
za uv slijedi referentni tijek rada; numeričko okruženje i upravitelj paketa još nisu dogovoreni.
Provjerite integraciju s aplikacijom prije tvrdnje da je Codex završni hook aktivan.

## Provjere dostupne pri postavljanju

`.github/workflows/ci.yml` pokreće se na PR-ovima, pri pushu na `main` i ručnim pokretanjem.
Izvodi provjeru dokumentacije i testove za `tools/` koji koriste standardnu biblioteku.
Te provjere ne zahtijevaju NMF paket, odabran skup podataka ni plaćenu uslugu. Još ne provjeravaju
numeričku implementaciju.

Pokrenite lokalno iz korijena repozitorija:

```bash
python3 tools/check_docs.py
python3 -m unittest discover -s tools -p 'test_*.py'
python3 tools/check_before_stop.py
python3 tools/daily_check.py --dry-run
```

Probno pokretanje dnevne provjere čita GitHub kada je pristup dostupan i prikazuje predloženu
radnju bez objavljivanja. Nedostatak autentifikacije ili nedostupan API prijavljuje se, a ne
bilježi kao uredan rezultat. Točan opseg dnevne provjere opisan je u `docs/plan/AI_REVIEW.md`.

Verzije GitHub Actions radnji zaključane su punim SHA oznakama commitova, uz oznake verzija u
komentarima. CI dobiva samo potrebne ovlasti; preuzimanje repozitorija ne zadržava pristupne
podatke. Dnevni tijek rada treba ovlast pisanja prijava (issues) kako bi održavao svoj izvještaj.
Lokalno dodavanje tog tijeka rada ne uključuje zakazana pokretanja dok ne stigne na zadanu
granu repozitorija i dok GitHub Actions ne dopusti izvođenje.

## Numeričko okruženje: naknadna timska odluka

Python je dogovoren; algoritam rješavanja, verzije ovisnosti, numeričke naredbe i primjena
ostaju otvoreni. Zadatak implementacije zajedno će dodati specifikaciju okruženja i datoteku
zaključanih ovisnosti, a zatim dokumentirati jednu podržanu naredbu za postavljanje, naredbu
za testove i ulaznu točku eksperimenta. Dodajte CI zadatak koji instalira zaključane ovisnosti
i pokreće male determinističke provjere. Cjelovita preuzimanja podataka i dugačke serije
eksperimenata držite izvan zadanog PR zadatka, osim uz izričito obrazloženje.

Završna skripta, CI, korijenski popis naredbi i ova stranica moraju se promijeniti zajedno.
Dok `pyproject.toml` ne postoji, završna skripta označava numeričku provjeru kao NOT RUN.
Kad ta datoteka postoji, zahtijeva `tools/check_project.py`, uveden zajedno s dogovorenim
okruženjem radi izvođenja numeričkih provjera. Nedostajuća skripta tada uzrokuje jasno vidljiv
pad provjere. Numerički CI zadatak mora pasti i pri neispravnom okruženju ili nevaljanom ulazu;
odsutna provjera nikad se ne računa kao uspješna.

## Završni hookovi

`tools/check_before_stop.py` lokalni je CLI. Način `--hook` daje JSON za Stop hook, a Claude
omotač poziva tu zajedničku implementaciju. `.codex/hooks.json` poziva istu provjeru preko
korijena Git repozitorija, pa klonovi i radna stabla ne ovise o Lovrinoj apsolutnoj putanji.
Codex zahtijeva i pouzdanu projektnu konfiguraciju i pregled te potvrdu povjerenja za točnu
definiciju hooka kojom ne upravlja sustav; nova ili promijenjena definicija preskače se dok
nije potvrđena kao pouzdana. Provjerite konfiguraciju i stvaran poziv prije tvrdnje o
aktivaciji u izvođenju. To su zahtjevi proizvoda opisani u
[službenim uputama za hookove](https://learn.chatgpt.com/docs/hooks), provjerenima 2026-10-15,
i odvojeni su od pravila repozitorija o ljudskom pregledu PR-a.

Konfiguracijske datoteke za oba alata postoje. Ručno pokretanje konfigurirane naredbe potvrđuje
da naredba radi, ali ne i da ju je neka aplikacija učitala. Pregledajte Codex hook naredbom
/hooks u CLI-ju, potvrdite povjerenje za namjeravanu definiciju i provjerite stvaran poziv na
svakom računalu. Nemojte zaobilaziti povjerenje ni mijenjati osobne/globalne postavke povjerenja
u sklopu ovog postavljanja repozitorija.

## Aktivacija na GitHubu

Sama prisutnost datoteka ne stvara commit, push, PR, prijavu, oznaku ni postavku repozitorija.
Lovro je naknadno, 2026-10-15, odobrio commit, push, PR i spajanje početnog tijeka rada;
jednokratna iznimka od pregleda zabilježena je u ADR-u 0002. Kad datoteke stignu na zadanu
granu, provjerite jesu li Actions/Issues uključeni, stvorite oznake nalaza opisane u
`docs/plan/AI_REVIEW.md` te pregledajte jedno CI izvođenje i probni pregled dnevne provjere
bez pisanja prije oslanjanja na dnevni izvještaj. Postavite dostupnu zaštitu grane za pravilo
ljudskog pregleda. Ne pretpostavljajte da se ograničenja GitHub paketa referentnog projekta
odnose i na ovaj repozitorij.

## Tijek istraživanja i eksperimenata

1. **Razumjeti:** pročitajte glavni Gillisov rad, razradite matematičko objašnjenje i
   zabilježite pretpostavke, dimenzije i mjesta u izvoru. Prema potrebi usporedite tvrdnje o
   algoritmima s izvornim radovima.
2. **Odlučiti:** dogovorite nov konkretan problem i skup podataka, interpretaciju ulazne
   matrice, funkciju cilja, algoritam i evaluaciju. Bitne izbore zabilježite u ADR-ovima i
   `docs/plan/METHODOLOGY.md` prije izrade eksperimenata koji o njima ovise.
3. **Implementirati i provjeriti:** povežite izvod s Python implementacijom. Koristite male
   analitički razumljive primjere, invarijante i, gdje je primjereno, obrazloženu usporedbu s
   referentnom implementacijom. Testovi moraju uzeti u obzir matematičku nejedinstvenost metode.
4. **Pokrenuti:** izvodite eksperimente iz zabilježenih konfiguracija i zaključanog okruženja.
   Razlikujte neuspješna od uspješnih izvođenja; sačuvajte dovoljno podataka o podrijetlu da
   se može reproducirati ili objasniti svaki rezultat upotrijebljen u materijalima za predaju.
5. **Protumačiti:** odvojeno procijenite rekonstrukciju i stvarno pitanje primjene.
   Zabilježite osjetljivost, ograničenja i nerazjašnjena opažanja. Mala pogreška rekonstrukcije
   sama ne potvrđuje korisnost komponenti ili klastera.
6. **Napisati i predstaviti:** stvarajte slike/tablice iz označenih izvođenja, citirajte ta
   izvođenja u radnim bilješkama i uskladite tvrdnje u seminaru i slajdovima. Svaki član tima
   prolazi cijelo obrazloženje i može objasniti zaključke prije predaje.

## Najmanji skup podataka o podrijetlu za prijavljeno izvođenje

Konkretan format zapisa odaberite tijekom implementacije. Mora sačuvati:

- Jedinstven identifikator izvođenja, vremensku oznaku, status i korištenu naredbu/konfiguraciju.
- Commit koda i podatak o necommitiranim promjenama u radnom stablu. Sačuvajte pripadajuće
  razlike ili stanje ako rezultati ovise o necommitiranom kodu; sam hash commita tada nije
  dovoljan.
- Python okruženje i ovisnosti te bitne pojedinosti izvođenja kada se prikazuje vrijeme rada.
- Izvor podataka, verziju ili kontrolni zbroj, datum nabave/pristupa, licenciju i konfiguraciju
  pretprocesiranja; označite generirane matrice ili podjele upotrijebljene pri izvođenju.
- Funkciju cilja, rang, algoritam rješavanja, inicijalizaciju, sjeme ili sjemena generatora
  slučajnih brojeva, tolerancije, ograničenja iteracija i stvarni razlog zaustavljanja. Samo
  sjeme nije potpun zapis za reproducibilnost.
- Metrike, nastale artefakte, upozorenja i pogreške. Sačuvajte neovisna ponovljena izvođenja
  pri istraživanju utjecaja inicijalizacije ili drugih izvora varijabilnosti.

Identifikatori objavljenih rezultata stabilni su: ispravak stvara novo izvođenje i povezuje ga
s prethodnim. Ne prepisujte dokaze na kojima se temelji postojeća slika. Veliki artefakti ili
artefakti s ograničenim pristupom mogu biti izvan Gita, ali repozitorij mora sačuvati njihove
identifikatore i upute za dohvat. Nikad ne izmišljajte nedostajuće podatke o podrijetlu.

## Podaci i artefakti

Provjerite licenciju, privatnost i uvjete redistribucije prije commitiranja podataka.
Preuzete sirove podatke i velike izvedene artefakte zadano držite izvan Gita; umjesto njih
zabilježite postupak nabave i ponovnog stvaranja. Mali testni podaci dopušteni za
redistribuciju i odabrane slike mogu se commitirati uz obrazloženje i pregled. Ne kopirajte
radove iz osobnih lokalnih mapa u repozitorij samo da bi apsolutna poveznica radila. Indeks
literature bilježi prenosive bibliografske podatke.

Postavljanje ne uključuje postavljanje aplikacije u produkciju, uslugu na poslužitelju ni
vanjsku predaju. Predaja i javna objava zahtijevaju izričitu korisnikovu uputu za konkretnu
radnju.
