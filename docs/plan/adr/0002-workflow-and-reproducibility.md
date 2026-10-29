# ADR-0002: Male pregledane promjene, zajedničko razumijevanje i sljedivi eksperimenti

**Datum:** 2026-10-15 · **Status:** prihvaćeno (Lovro, 2026-10-15)

## Kontekst

Mislav, Sara i Lovro pripremaju seminar o NMF-u za kolegij Matrične i tenzorske metode u analizi
podataka. Predaju pisani seminar, prezentaciju, Python kod i eksperimentalne rezultate. Sve
troje mora razumjeti cijeli projekt. Primjena, skup podataka i detalji implementacije ostaju
otvoreni te će se dogovoriti kasnije.

Lovro je 2026-10-15 zatražio prilagodbu postojećeg načina rada iz projekta PelosiPlus. Korisne
su prakse male promjene, ljudski pregled, zapisi odluka, usklađivanje dokumentacije, nalazi i
dnevna provjera. Arhitektura tog proizvoda i granice odgovornosti ne opisuju ovaj seminar.
Ovaj zapis dokumentira postavljanje koje je zatražio Lovro, a ne odobrenje Mislava ili Sare.

## Odluka

1. Jedan zadatak obrađuje se na jednoj grani i u malom PR-u. Grane članova tima koriste
   `mislav/<topic>`, `sara/<topic>` i `lovro/<topic>`; grane koje stvara AI koriste `codex/<topic>`.
   Ne raditi commit izravno na `main`, prisilni push ni prepisivati tuđu granu.
2. Svaki PR prema `main` treba odobriti barem jedan drugi član tima. AI pregled dopunjuje taj
   pregled. Izmjenjujte rad i zajedničke prolaze kroz projekt kako bi sve troje moglo objasniti
   matematiku, implementaciju, eksperimente i zaključke; bilježite samo stvarno sudjelovanje.
3. Korijenski `AGENTS.md` ostaje jedini izvor pravila repozitorija, a `CLAUDE.md` sadrži
   `@AGENTS.md`. Važne odluke zapišite u ADR-ove te u istoj promjeni uskladite planove, naredbe
   i materijale na koje odluka utječe.
4. Neriješene znanstvene odluke ostaju jasno otvorene. Prije implementacije koja ovisi o njima
   pripremite mogućnosti i obrazloženje za timsku raspravu; rutinske odobrene ispravke obavite
   bez dodavanja novog koraka odobravanja.
5. AI alati trebaju izričito korisničko ovlaštenje u razgovoru prije commita, pusha, otvaranja
   PR-ova ili objavljivanja problema, komentara, pregleda, predaja ili javnih materijala.
   Već dano ovlaštenje vrijedi i dalje unutar svojeg opsega.
6. Pokrećite provjere dokumentacije i alata u CI-ju te zajedničkom završnom skriptom. Prije
   tvrdnje da je alat integriran provjerite jesu li lokalne završne provjere (*hooks*) stvarno
   aktivne. Numeričke provjere u CI-ju i zaključane ovisnosti dodaju se nakon izbora implementacije.
7. Za svako prijavljeno izvođenje sačuvajte označenu konfiguraciju eksperimenta, identitet
   podataka, podrijetlo koda i okruženja, podatke o zaustavljanju i izlaze. Ispravak dobiva
   novu oznaku izvođenja; citirani rezultati ne prepisuju se prešutno. Nedostajući dokazi
   ostaju jasno označeni kao nedostajući.
8. Koristite zajedničke nalaze i dnevnu GitHub provjeru stanja CI-ja, sukoba i zastarjelosti
   PR-ova, odobrenja te commitova koji su stigli na `main` bez PR-a. Provjera pravila počinje
   od zabilježenog početnog stanja, 2026-10-15 21:19:49 UTC; inicijalizacija prije uvođenja
   načina rada ne provjerava se retroaktivno. Aktivaciju na GitHubu i postavke identiteta
   treba zasebno provjeriti.

## Obrazloženje

Manje promjene drugi student lakše razumije i provjerava. Ljudski pregled i izmjenjivanje u
objašnjavanju podupiru cilj učenja bez dijeljenja znanja u odvojene uloge. Usklađivanje
dokumentacije sprječava da točna lokalna promjena ostavi netočan opis projekta. Zapisi odluka
razlikuju svjestan znanstveni izbor od usputnog detalja implementacije.

NMF nije jedinstven i osjetljiv je na metodološke izbore. Reproducibilne konfiguracije i
podrijetlo materijala omogućuju tumačenje rezultata nakon promjena koda, podataka ili okruženja.
Numerički testovi, znanstveni pregled i sljedivi eksperimenti daju različite dokaze; nijedan ne
zamjenjuje ostale. Zakazana provjera otkriva neka kršenja načina rada, ali ne može dokazati
razumijevanje ni znanstvenu točnost.

## Odbačene mogućnosti

- **Trajna podjela odgovornosti za matematiku, kod i eksperimente:** nespojiva je sa zahtjevom
  da svaki član razumije cijeli projekt.
- **Kopiranje tehnologija i ograničenja prethodnog proizvoda:** ovaj projekt nema dogovoren
  API, bazu podataka, mrežni proizvod ni potrebu za objavljivanjem aplikacije.
- **Izbor algoritma i podataka pri postavljanju načina rada:** Lovro je te odluke o
  implementaciji i primjeni izričito ostavio za kasniju raspravu.
- **AI odobrenje ili uspješan CI kao dovoljan uvjet:** nijedno ne zamjenjuje pregled drugog
  člana tima niti potvrđuje znanstvene tvrdnje.
- **Snimke rezultata bez reproducibilnih ulaza:** sama slika ne objašnjava koji su je izbori
  proizveli.
- **Zaseban repozitorij AI memorije sada:** trajne odluke, zadaci, bilješke o izvorima i nalazi
  ovdje već imaju zajednička mjesta; za ovo postavljanje ne treba dodatna infrastruktura.
- **Pretpostavka da su zaštite na GitHubu, oznake ili lokalne završne provjere aktivne:**
  lokalne datoteke ne utvrđuju stanje GitHuba ni računala pojedinog člana.

## Posljedice

- `docs/CHANGE_PROTOCOL.md` određuje postupak za zadatak, popis za usklađivanje i primopredaju.
- `docs/plan/PIPELINE.md` razlikuje trenutačne provjere od planiranog numeričkog rada i navodi
  minimalne podatke o podrijetlu rezultata.
- `docs/plan/AI_REVIEW.md` određuje nalaze, pregled i ograničenja dnevne provjere.
- `.github/pull_request_template.md`, `.github/workflows/ci.yml` i
  `.github/workflows/daily-check.yml` provode lokalno postavljanje načina rada.
- `tools/check_docs.py`, `tools/check_before_stop.py` i `tools/daily_check.py`, uz testove,
  provode automatizirane provjere. `.claude/settings.json` i `.codex/hooks.json` postavljaju
  istu završnu provjeru. Aktivacija lokalnih završnih provjera provjerava se neovisno o
  postojanju skripte.
- GitHub identiteti, dostupnost zaštite grane, aktivacija dnevne provjere na GitHubu, primjena,
  podaci, algoritam i numeričko okruženje ostaju izričito navedeni naknadni zadaci.

## Dodatak 2026-10-15: izričito odobreno spajanje početnog načina rada

Nakon pregleda pripremljenog postavljanja Lovro je u razgovoru izričito zatražio commit, push,
PR i spajanje. Time je odobrio objavu i spajanje početnog PR-a #1 za način rada s grane
`codex/seminar-workflow` bez čekanja pregleda drugog člana. To ne bilježi niti podrazumijeva
odobrenje Mislava ili Sare i ne mijenja pravilo pregleda za kasnije PR-ove.

Dnevna provjera prepoznaje samo taj broj PR-a i tu granu kao iznimku od pregleda. CI i dalje
mora proći; izravni commitovi i druga spajanja bez pregleda ostaju nalazi. Stvaranje oznaka
nalaza potrebnih objavljenoj dnevnoj provjeri dio je njezine aktivacije. Ova uputa ne odobrava
nepovezane prijave problema, poruke ni promjene pristupa repozitoriju.

## Dodatak 2026-10-15: hrvatski za tekstove namijenjene ljudima

Lovro je nakon početnog postavljanja izričito zatražio prijevod tekstova koje čitaju ljudi na
hrvatski jer se kolegij izvodi na hrvatskom. Dokumentacija za tim, pisani seminar, prezentacija,
commit poruke, tekstovi PR-ova i objašnjenja nalaza pišu se na hrvatskom. Kod, identifikatori,
nazivi datoteka i tehničke upute
AI alatima mogu ostati na engleskom kada to olakšava rad. Naredbe, oznake na GitHubu i drugi
tehnički identifikatori zadržavaju se kako bi postojeći alati nastavili raditi.

Ovo mijenja raniju jezičnu konvenciju; ne bira format predaje niti znanstvenu metodu. Prijevod
čuva povijest odluka i gore navedenu iznimku za početni PR #1.

## Dodatak 2026-10-15: odobreno spajanje hrvatskog prijevoda bez pregleda tima

Nakon dovršenog prijevoda Lovro je izričito zatražio i njegovo spajanje bez pregleda Mislava
ili Sare. Uputa obuhvaća commit, push, otvaranje PR-a i spajanje prijevoda u `main`.
Iznimka vrijedi samo za PR #2 s grane `codex/croatian-project-docs`; ne bilježi tuđe odobrenje
i ne mijenja pravilo pregleda budućih PR-ova. CI i ostale provjere moraju proći.

Pravila, protokol, PR predložak i dnevna provjera bilježe tu konkretnu iznimku. Prethodna
iznimka za PR #1 ostaje dio povijesti; drugi PR-ovi nisu izuzeti iz provjere odobrenja.

## Dodatak 2026-10-29: autorstvo i AI alati kao pomoćno sredstvo

Lovro je izričito zatražio da se svaki commit, redak koda i dokument pripisuje isključivo članu
tima koji radi zadatak, a ne AI alatu kojim se pritom služi. Naveo je da se Mislav i Sara s tim
slažu. Zatim je izričito zatražio commit, push, otvaranje PR-a i spajanje te promjene u `main`
bez pregleda drugog člana. Iznimka vrijedi samo za PR #4 s grane `lovro/ai-authorship`; ne
bilježi odobrenje Mislava ili Sare i ne mijenja pravilo pregleda budućih PR-ova. CI i ostale
provjere moraju proći.

Od tog datuma:

1. AI alati pomoćno su sredstvo, poput uređivača koda ili sustava za simboličko računanje, a ne
   suradnici ni autori. Član koji koristi alat jedini je autor rezultata i odgovara za svaki
   redak i tvrdnju; mora ih moći objasniti i bez alata.
2. Commitovi nose git identitet tog člana. Alati ne dodaju `Co-Authored-By`, „Generated with”
   ni drugi vlastiti potpis u commitove, PR-ove, kod ili dokumente. `.claude/settings.json`
   to isključuje za Claude Code.
3. Nove grane koriste samo `mislav/<topic>`, `sara/<topic>` i `lovro/<topic>`; AI alat radi na
   grani člana koji ga koristi. Prefiks `codex/<topic>` iz prve točke odluke više se ne koristi
   za nove grane.

Ne mijenjaju se obvezni ljudski pregled PR-ova, zabrana izmišljanja zapisa o pregledu ili
razumijevanju ni povijest odluka. Grane `codex/seminar-workflow` i `codex/croatian-project-docs`
PR-ova #1 i #2 ostaju zabilježene kakve jesu jer se na njih oslanjaju iznimke dnevne provjere.
