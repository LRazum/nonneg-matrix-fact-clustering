# ADR-0001: Proučiti i implementirati NMF uz razumijevanje cijelog projekta za sve troje

**Datum:** 2026-10-15 · **Status:** prihvaćeno (opseg odredio Lovro, 2026-10-15)

## Kontekst

Kolegij je Matrične i tenzorske metode u analizi podataka. Mislav, Sara i Lovro zajedno rade
seminar. Priloženo je šest znanstvenih radova; Lovro je odredio Gillisov rad
main_NNMF-general.pdf kao glavni obvezni izvor, a NMF kao glavnu metodu.

## Odluka

1. Naučiti teoriju uz detaljnu matematičku razradu, razumjeti numeričku metodu, implementirati
   je u Pythonu i primijeniti na nov konkretan problem i skup podataka.
2. Dovoljan je nov konkretan slučaj u domeni koju radovi već spominju; moguća je i druga domena.
   Razvoj novog algoritma za NMF nije obvezan.
3. Predati pisani seminar, prezentaciju, kod i eksperimentalne rezultate.
4. Svaki član uči matematiku, algoritam, podatke, implementaciju i interpretaciju. Znanje se
   dugoročno ne dijeli po područjima između članova. Podjela zadataka dogovara se kasnije.
5. Primjena, skup podataka, funkcija cilja i algoritam, ovisnosti, formati dokumenata i rok
   ostaju otvoreni. Postavljanje načina rada ne uključuje izbor ni implementaciju metode.

## Obrazloženje

Cilj učenja je razumjeti metodu dovoljno dobro za njezinu implementaciju, objašnjenje i
evaluaciju. Matematički izvodi i reproducibilni dokazi podupiru to razumijevanje. Sve troje
treba moći objasniti cijeli projekt.

## Odbačene mogućnosti

- Matematička obrada ograničena na definiciju NMF-a: Lovro je izričito zatražio veću dubinu.
- Trajna podjela odgovornosti za matematiku, kod i eksperimente po članovima: Lovro izričito
  traži da svi poznaju cijeli projekt.
- Pretpostavka da je klasteriranje dokumenata ili hijerarhija ranga 2 već obvezna: NMF je glavna
  metoda, a primjena je još otvorena.
- Izbor detalja implementacije tijekom postavljanja načina rada: tim će ih dogovoriti kasnije.

## Posljedice

Opseg je prenesen u `AGENTS.md`, `docs/plan/PROJECT.md`, `docs/plan/TASKS.md`,
`docs/plan/METHODOLOGY.md` i `docs/research/LITERATURE.md`. Buduće odluke moraju zadržati
zajedničko učenje cijelog projekta i povezati matematiku, kod i interpretaciju eksperimenata.
