# Zapisi odluka

Zapis odluke (ADR, engl. *architecture decision record*) bilježi jednu važnu projektnu odluku,
dokaze i razloge odbacivanja drugih mogućnosti. Ovdje to obuhvaća znanstvenu metodologiju i
način rada u repozitoriju. `docs/INDEX.md` sadrži popis zapisa, a `docs/CHANGE_PROTOCOL.md`
objašnjava kada treba napisati novi zapis.

## Naziv datoteke i format

Upotrijebite sljedeći slobodan četveroznamenkasti broj, a zatim kratak engleski naslov malim
slovima, s riječima odvojenima spojnicama. Brojevi se ne koriste ponovno. Primjer:

```text
docs/plan/adr/0003-choose-application-and-dataset.md
```

Koristite sljedeću strukturu i redoslijed:

```markdown
# ADR-NNNN: Naslov koji izriče odluku

**Datum:** YYYY-MM-DD · **Status:** predloženo

## Kontekst
Činjenice, zahtjevi, dokazi i otvorena pitanja.

## Odluka
Konkretan izbor i njegov opseg. Navedite što ostaje otvoreno.

## Obrazloženje
Razlozi i dokazi, uz mjesto u izvoru gdje je to primjenjivo.

## Odbačene mogućnosti
Razmotrene mogućnosti i stvarni razlog odbacivanja svake od njih.

## Posljedice
Pravila, plan, kod, testovi, eksperimenti i materijali za predaju na koje odluka utječe.
```

Za pododjeljke koristite `###`. Provjera dokumentacije provjerava strukturu zapisa; ljudi
provjeravaju valjanost obrazloženja i dokaza.

## Status i ovlasti za donošenje odluke

- `predloženo`: pripremljeno za raspravu; ako implementacija ovisi o toj odluci, čeka se odluka.
- `prihvaćeno (<tko>, YYYY-MM-DD)`: navedite samo osobe koje su stvarno odlučile i datum odluke.
- `zamijenjeno zapisom ADR-NNNN`: novi zapis objašnjava novu odluku i povezuje se sa starim.

Prihvaćen način rada koji je zatražio Lovro ne znači da su ga odobrili Mislav ili Sara.
Znanstvene odluke otvorene u `docs/plan/PROJECT.md` ostaju otvorene dok se stvarno ne rasprave
i zabilježe. Nepoznate činjenice zapišite kao otvorena pitanja; nemojte izmišljati pristup
podacima, izbor algoritma, rezultat eksperimenta ili nečije odobrenje da biste popunili predložak.

## Naknadne promjene

Sačuvajte povijest odluka. Dopunu koja je u skladu s postojećom odlukom dodajte na kraj:

```markdown
## Dodatak YYYY-MM-DD: što se promijenilo
```

Pri zamjeni odluke napišite novi ADR, označite stari kao zamijenjen i u kontekstu novog zapisa
navedite koju odluku zamjenjuje. Nemojte brisati stari zapis ni prepisivati njegove odbačene
mogućnosti kao da je nova odluka vrijedila od početka. U istoj promjeni uskladite sve dokumente
na koje odluka utječe.
