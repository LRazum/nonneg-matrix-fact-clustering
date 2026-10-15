# AI pregled, nalazi i dnevna provjera

Ovaj postupak osigurava da Mislav, Sara i Lovro mogu pratiti probleme i primopredaje.
Korijenski `AGENTS.md` i `docs/CHANGE_PROTOCOL.md` ostaju mjerodavna pravila; AI alat suradnik
je, a ne ljudski pregledavatelj niti dokaz da tim razumije neki rezultat.

## Nalazi kao zajednička memorija

Reproducibilan problem zabilježite jednom, a kasnija otkrića povežite s njim. Koristite GitHub
prijavu s oznakama:

- `finding`.
- Jedna oznaka izvora: `source:codex`, `source:claude-code`, `source:human-review`, `source:ci`
  ili `source:daily-check`.
- Jedna oznaka ozbiljnosti: `severity:high` za nevaljan središnji rezultat, neispravan `main`
  ili otkrivenu tajnu; `severity:medium` za blokiran rad, zavaravajuću dokumentaciju ili
  nedostajuće podatke o podrijetlu; `severity:low` za dorade i čišćenje.

U tekstu navedite PR ili da ga nema, datoteku i mjesto, konkretan problem, postupak
reprodukcije/dokaze, znanstvenu ili praktičnu posljedicu i predloženi sljedeći korak.
Za eksperimentalne nalaze uključite pripadajući identifikator izvođenja. Sumnja bez dokaza
otvoreno je pitanje, a ne dokazana pogreška.

Na početku rada provjerite `gh issue list --label finding --state open`. PR koji rješava
problem koristi `Closes #<number>` kada je problem stvarno riješen. Ne zatvarajte nalaz
prešutno zato što je kod premješten. Nazivi oznaka opisuju predviđeni sustav; njihovo postojanje
na GitHubu mora se provjeriti, a lokalna konfiguracija nije dokaz da su stvorene.

AI alati smiju lokalno pripremiti tekst nalaza. Objavljivanje prijave, oznake, komentara ili
pregleda zahtijeva izričito korisnikovo odobrenje za tu radnju u sesiji, osim ako je riječ o
radnji dnevne provjere već odobrenoj uključenim tijekom rada repozitorija. Ne tražite isto
odobrenje ponovno unutar njegova odobrenog opsega.

## Dnevna provjera na GitHubu

`.github/workflows/daily-check.yml` zakazuje `tools/daily_check.py` u 07:00 UTC i podržava
ručno pokretanje. Uz trenutačni pomak u zoni Europe/Copenhagen to je 09:00; zimi je lokalno
vrijeme 08:00. GitHub ne jamči točno vrijeme zakazanih pokretanja. Tijek rada mora stići na
zadanu granu, a Actions mora biti uključen da bi se zakazana provjera mogla izvoditi.

Dnevna provjera provjerava:

1. Postoji li CI tijek rada i je li njegovo zadnje dovršeno izvođenje na `main` uspjelo.
2. Imaju li otvoreni PR-ovi prijavljene konflikte pri spajanju.
3. Ima li otvorenih PR-ova bez ažuriranja dulje od tri dana.
4. Imaju li PR-ovi spojeni u `main` u posljednjih 48 sati ljudsko odobrenje koje je prije
   spajanja dao netko drugi, a ne autor.
5. Imaju li commitovi vidljivi na `main` s datumom commitiranja (`committer date`) unutar posljednjih 48 sati
   pridružen PR spojen u `main`.

Provjera povijesti pregleda i izravnih commitova počinje od zabilježene početne točke
postavljanja, 2026-10-15 21:19:49 UTC. Inicijalizacija repozitorija prije uvođenja tijeka rada
ne prijavljuje se retroaktivno kao kršenje novih pravila. Preklapajući vremenski prozor
smanjuje mogućnost propuštenih prijava nakon odgođenog izvođenja; nije cjelovita provjera
povijesti. Nepoznato stanje mogućnosti spajanja, API pogreške ili nedostajuće obvezne
informacije prikazuju se kao dijagnostika, a ne kao uspješne provjere.

Opseg provjere ograničen je: čita do 200 otvorenih PR-ova, 200 spojenih PR-ova i 100 commitova.
Koristi datume commitiranja (`committer date`) umjesto vremenskih oznaka pusha pa stari commit tek izravno poslan
na `main` može ostati izvan vremenskog prozora. Ta su ograničenja primjerena malom seminarskom
timu; provjera nije potpuna povijesna provjera niti zamjena za zaštitu grane.

Pravilo za ljudski pregled strože je: pregledavatelj mora biti drugi član tima koji čine
Mislav, Sara i Lovro. Dok njihovi GitHub identiteti nisu konfigurirani i provjereni, ljudsko
odobrenje osobe koja nije autor provjerava samo taj ograničeni uvjet; sudionici PR-a i dalje
provjeravaju članstvo u timu. Automatski pregledi i odobrenja botova nikad ne ispunjavaju
pravilo ljudskog pregleda. Dnevna provjera ne može potvrditi da pregledavatelji razumiju
matematiku, da su sva tri člana naučila gradivo ni da su rezultati znanstveno utemeljeni.

Lovro je 2026-10-15 izričito odobrio spajanje bez pregleda drugih članova za početni PR #1
iz `codex/seminar-workflow` i za prijevod u PR-u #2 iz `codex/croatian-project-docs`.
Dodaci zapisa ADR-0002 bilježe te upute. Dnevna provjera prepoznaje samo ta dva točna para
broja i grane, bez tvrdnje da je postojalo ljudsko odobrenje. Iznimke ne obuhvaćaju druge
PR-ove, pad CI-ja ni izravne commitove.

Kada otkrije probleme, dnevna provjera održava jednu prijavu s naslovom
„Dnevna provjera: main ili otvoreni PR-ovi zahtijevaju pozornost”, oznakama `finding`,
`source:daily-check` i najvišom otkrivenom ozbiljnošću. Ažurira postojeću otvorenu prijavu
provjere umjesto otvaranja duplikata. Uredna provjera zatvara postojeći izvještaj. Nikad ne
ispravlja kod, spaja PR, odobrava rad niti mijenja istraživačke odluke. Predviđene oznake i
ovlasti tijeka rada moraju postojati da bi objava uspjela; API pogreška ostaje pogreška.

Pokrenite `python3 tools/daily_check.py --dry-run` za pregled predložene radnje bez pisanja.
Prisutnost ove konfiguracije u radnom stablu ne znači da je dnevna provjera na GitHubu već
izvedena. Koristite i zaštitu grane na GitHubu kada je dostupna; provjerite stvarnu
konfiguraciju umjesto pretpostavke da ovdje vrijedi ograničenje iz GitHub paketa drugog projekta.

### Oznake i prvo uključivanje

Navedeni sustav oznaka konfiguracija je koju treba stvoriti nakon odobrenja objavljivanja, a
ne tvrdnja da oznake na GitHubu već postoje. Za dnevno objavljivanje potrebne su barem oznake
`finding`, `source:daily-check`, `severity:high` i `severity:medium`. Primjerice, ove naredbe
pokrenite samo u sklopu odobrenog postavljanja GitHuba:

```bash
gh label create finding --color B60205 --description "Provjeren problem u projektu ili tijeku rada"
gh label create source:daily-check --color 5319E7
gh label create severity:high --color D93F0B
gh label create severity:medium --color FBCA04
```

Preostale oznake izvora i `severity:low` mogu se dodati kada se počnu koristiti. Prije
stvaranja provjerite postojeće oznake, dostupne zaštite koje zahtijevaju ljudski pregled,
uspješno CI izvođenje i probni pregled dnevne provjere bez pisanja. Objavljivanje tijeka rada
omogućuje njegovoj zakazanoj provjeri održavanje jednog izvještaja; ne odobrava nepovezane
poruke ili promjene.

## Pregled promjene

Pregledajte PR u odnosu na njegovu stvarnu osnovu i navedite pregledani commit. Pročitajte
pozivatelje, matematičko objašnjenje i pogođene eksperimente, a ne samo razlike. Ako osnova
zaostaje za `main`, navedite neizvjesnosti vezane uz integraciju. Čuvajte tuđe necommitirane
promjene: po potrebi koristite izdvojeno radno stablo za testove i uklonite samo ono koje ste
sami stvorili.

Provjerite dokaze primjerene promjeni:

- Matematičke tvrdnje: pretpostavke, dimenzije, izvod, mjesto u izvoru i točnu tvrdnju o
  konvergenciji ili optimalnosti. Pad vrijednosti funkcije cilja ne dokazuje globalnu
  optimalnost ni konvergenciju prema određenoj faktorizaciji.
- Numerički kod: nevaljane ulaze, konačnost vrijednosti, nenegativnost, dimenzije i ponašanje
  pri zaustavljanju; male primjere s poznatim svojstvima. Skaliranje/permutacije faktora mogu
  učiniti izravnu jednakost faktora nevaljanim testom. Usporedba s bibliotekom korisna je
  potkrepa, a ne dokaz istog rješenja.
- Eksperimenti: izvorne podatke, pretprocesiranje, konfiguraciju, odabir ranga, varijabilnost
  među izvođenjima, interpretaciju metrika, podrijetlo artefakata i vezu između tvrdnji i dokaza.
- Dokumentacija/tijek rada: popis povezanih ažuriranja, istinit prikaz stanja, izvršive naredbe
  i razliku između uključene automatizacije i lokalno pripremljene konfiguracije.

Sumnju na pogrešku provjerite izračunom, minimalnim testom ili izvorom prije nego što je
prijavite kao nalaz. Nalaze koji zahtijevaju radnju prijavite prema ozbiljnosti, uz točna
mjesta i posljedice; odvojite neobvezna poboljšanja od pogrešaka. Navedite što je provjereno i
što ostaje nepokrenuto. Kad se commitovi promijene, usredotočite se na nove promjene i njihove
pogođene ovisnosti. Pregled objavite samo uz izričito odobrenje. Nikad ne tvrdite da AI pregled
ispunjava obvezno ljudsko odobrenje.

## Primopredaja i timsko učenje

Koristite polja primopredaje iz odjeljka 9 u `docs/CHANGE_PROTOCOL.md`. Prihvaćene odluke
čuvajte u ADR-ovima, zadatke u `docs/plan/TASKS.md`, bilješke o izvorima u
`docs/research/LITERATURE.md`, a provjerene probleme u nalazima. Ova konfiguracija nema zaseban
repozitorij memorije ni automatski pull/push osobnih AI bilježaka. Buduća usluga zajedničke
memorije zahtijeva konkretnu timsku odluku.

Na zajedničkim prolascima kroz etape izmjenjujte tko objašnjava model, izvod, implementaciju i
interpretaciju eksperimenata. Neriješena pitanja zabilježite kao zadatke. Sudjelovanje,
pregled ili razumijevanje člana označite tek nakon stvarnog sudjelovanja ili potvrde;
generirani popis provjera nije dokaz da su ga Mislav, Sara ili Lovro ispunili.
