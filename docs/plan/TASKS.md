# Zadaci i ključne točke

Status se temelji na dokazima: plan nije implementacija, uspješne provjere alata nisu numerički
rezultati, a AI sažetak nije ljudsko odobrenje. Ovo su etape projekta. Konkretni zadaci po
osobama su GitHub issuei iz [podjele rada](PODJELA.md), a svaki pripada jednoj od etapa niže.
Svi su zadaci zajednički: nositelj vodi zadatak, a recenzent iz pregleda u krug ga provjerava.

## Pregled

| Zadatak | Cilj | Ovisi o | Stanje |
|---|---|---|---|
| T0 | Utvrditi kontekst projekta i prilagoditi tijek rada u repozitoriju | Korisnikove odluke o opsegu | Provedeno; objava odobrena za početni PR, povjerenje hookovima preostaje provjeriti na svakom računalu |
| T1 | Razviti zajedničko matematičko razumijevanje na temelju Gillisa i dopunske literature | Kontekst T0 | Spremno za početak |
| T2 | Odabrati konkretan problem i skup podataka s opravdanim NMF prikazom | Kontekst T0 | Odlučeno 2026-11-05: ADR-0003 (GuitarSet, prepisivanje gitare) |
| T3 | Dogovoriti funkciju cilja, algoritam i plan eksperimenata | T1, T2 | Djelomično: funkcija cilja i algoritam u ADR-0003; plan eksperimenata je zadatak Z2 |
| T4 | Implementirati i provjeriti dogovorenu NMF metodu u Pythonu | T3 | Python 3.12 dogovoren na Z0. Slijedi početno okruženje B1 i implementacija po nitima |
| T5 | Provesti eksperimente koji omogućuju reprodukciju rezultata i protumačiti ih | T4, priprema podataka | Otvoreno |
| T6 | Sastaviti pisani seminar i prezentaciju | Od T1 nadalje; konačni rezultati iz T5 | Otvoreno |
| T7 | Reproducirati konačne rezultate i zajedno uvježbati cjelovito objašnjenje | T5, T6 | Otvoreno |

Ovo je redoslijed ovisnosti. Faze i zadaci po osobama nalaze se u [podjeli rada](PODJELA.md):

- T1 pokrivaju A3, B4, C1 te neovisne provjere A9, B9 i C9;
- T3 pokriva Z2;
- T4 pokrivaju B1, B2, B3, A1, A2, A5, C2, C3 i C4;
- T5 pokrivaju A4, A6, B5, B6, C5 i C6;
- T6 pokrivaju A7, B7, C7, A8, B8, C8 i Z5;
- T7 pokrivaju Z4 i Z6.

## T0: postavljanje tijeka rada

Pripremiti pravila, pregled literature, metodološki plan, zapise odluka, popis za usklađivanje
dokumentacije, predložak PR-a, CI, završne provjere i definiciju dnevnog audita. Provjeriti
lokalno. Razlikovati pripremljenu konfiguraciju od pouzdanih i aktivnih hookova te tijekova
rada omogućenih na udaljenom repozitoriju. Ne raditi commit, push ni objavljivati sadržaj
na GitHubu bez ovlaštenja.

Lokalna provjera 2026-10-15: provjera dokumentacije prijavila je 0 upozorenja i prošla su sva
43 testa alata za tijek rada. Obje konfigurirane naredbe hookova ručno su pokrenute iz korijena
repozitorija i podmape: valjan JSON, uz izričitu oznaku NOT RUN za numeričke provjere.
Provjereni su YAML tijekova rada i oblikovanje teksta. To ne dokazuje povjerenje na računalu
ni automatsko pokretanje hookova.

Snimka stanja GitHuba prije objave pokazivala je zadanu granu main s početnim README-om,
bez objavljene CI definicije i bez oznaka finding. Lovro je zatim izričito odobrio commit,
push, PR i spajanje. Početni PR #1 za tijek rada koristi dokumentiranu iznimku od pregleda
pri početnom postavljanju; ne tvrdi se da ga je odobrio drugi član. PR i izvršavanja GitHub
Actions bilježe objavu i udaljenu provjeru. Preduvjeti objave i aktivacije navedeni su u
[uputama za tijek rada](PIPELINE.md); povjerenje hookovima na pojedinom računalu ostaje zasebno provjeriti.

## T1: matematičko razumijevanje

Proći sadržaj iz [metodološkog plana](METHODOLOGY.md), uz odgovarajuće odjeljke izvora iz
[vodiča kroz literaturu](../research/LITERATURE.md). Izraditi čitljive izvode s navedenim pretpostavkama
i malim razrađenim primjerom. Razlikovati dokazanu tvrdnju od intuicije ili empirijskog
opažanja. Zajedno proći oznake, funkciju cilja i mehanizam ažuriranja.

Zadatak je dovršen kada su bilješke pregledane, nejasnoće zabilježene i sva tri člana mogu
objasniti matematički argument. Ne označiti ga dovršenim samo zato što su bilješke generirane.

Za odabranu temu 2 postoji radni nacrt
[skripte](../research/skripta-gitara/skripta-gitara.pdf) (2026-11-05). Nitko ga još nije pregledao
i on ne dokazuje zajedničko razumijevanje; stanje zadatka T1 se ne mijenja. Matematiku dijele
niti: Sara (A3), Lovro (B4) i Mislav (C1). Svaki dio neovisno izvodi recenzent (A9, B9, C9).

## T2: problem i skup podataka

Usporediti manji broj konkretnih kandidata prema pitanju na koje odgovaraju, konstrukciji
nenegativne matrice, dostupnosti i licenci, izvedivoj veličini, interpretaciji i evaluaciji.
Objasniti po čemu se konkretni problem i podaci razlikuju od primjera u priloženim radovima.
Tim odabire kandidata i bilježi odluku.

Odlučeno 2026-11-05 u [ADR-0003](adr/0003-choose-guitar-transcription-with-kl-nmf.md), na temelju
[prijedloga tema](prijedlog-tema/prijedlog-tema-nmf.pdf): prepisivanje gitare u note, GuitarSet 1.1.0.
Preuzimanje, kontrolni zbrojevi i provjera predobrade su zadaci A1 i A4.

Zadatak završava dogovorenim istraživačkim pitanjem, opisom izvora i podataka, planom
predobrade, predviđenim značenjem faktora i izvedivom evaluacijom.

## T3: metoda i plan eksperimenata

Povezati funkciju cilja i algoritam s odabranim prikazom i pitanjem. Dogovoriti rangove,
inicijalizacije i sjemena generatora slučajnih brojeva, kriterije zaustavljanja, zaštite,
referentnu metodu, metrike i raspoložive računalne resurse. Hipoteze i pitanja zapisati prije
pregleda konačnih rezultata. Ne dodavati algoritme samo radi popunjavanja usporedne tablice.
Važne izbore i odbačene mogućnosti zabilježiti u ADR-u.

## T4: implementacija u Pythonu

U B1 postaviti osnovu za Python 3.12, projektne provjere i CI. Zatim dodavati ponovno upotrebljiv
numerički kod i smislene testove. Ovisnosti zaključati uz kod koji ih prvi koristi.
Ponašanje usporediti s neovisnim malim primjerima i, kada je korisno, bibliotečnom
implementacijom s usklađenim postavkama.
Objasniti razlike u funkciji cilja i skaliranju.

## T5: eksperimenti i interpretacija

Implementirati ponovljiva pokretanja i sačuvati podatke o podrijetlu rezultata. Izvijestiti o
ponašanju rekonstrukcije, pitanju domene, stabilnosti kroz dogovorena pokretanja te
neuspjesima i ograničenjima. Svaku prikazanu tablicu i sliku povezati s pokretanjem koje ju
je proizvelo. Sam povoljan primjer nije dovoljan.

## T6: seminar i prezentacija

Pisati nacrte odjeljaka kako se razvija razumijevanje, zatim privremeni sadržaj zamijeniti
provjerenim rezultatima. Oznake, algoritam, postavke, slike i zaključke uskladiti s kodom.
Odabrati izvorne formate i naredbe za izradu prije tvrdnje da je bilo koji od tih materijala
moguće izgraditi. Seminar i prezentaciju pisati na hrvatskom. Uključiti citate i razlikovati
preuzete slike od slika nastalih u ovom projektu.

## T7: završna reprodukcija rezultata i zajednički prolazak

U novom okruženju reproducirati prikazane rezultate. Predaju provjeriti prema naknadno
utvrđenim zahtjevima kolegija. Svaki član vježba objašnjavanje cijelog puta od problema
i matematike do koda, rezultata i ograničenja. Zabilježiti stvarnu provjeru, preostale
nejasnoće i mjesta konačnih materijala; ne izmišljati odobrenja ni spremnost za predaju.
