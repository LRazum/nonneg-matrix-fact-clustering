# Opseg seminara i predaja

## Dogovoreni cilj

Kolegij: **Matrične i tenzorske metode u analizi podataka**.
Tim: **Mislav, Sara i Lovro**. Svaki član mora razumjeti cijeli projekt.

Proučiti nenegativnu matričnu faktorizaciju (NMF) uz rad Nicolasa Gillisa,
*The Why and How of Nonnegative Matrix Factorization*, kao glavni obvezni izvor.
Razraditi matematiku detaljnije od uvodne definicije, razumjeti odabranu numeričku metodu,
implementirati je u Pythonu i primijeniti na nov konkretan problem i skup podataka.
Prihvatljiva je poznata domena s drugim konkretnim problemom i podacima. Moguća je i nova
domena; istraživačka novost algoritma nije uvjet.

Ove je zahtjeve Lovro naveo 2026-10-15. Vidjeti
[ADR-0001](adr/0001-seminar-scope-and-shared-understanding.md). Ne pretpostavljati da su
ostali članovi odobrili određeni skup podataka, algoritam ili pregled tijeka rada.

## Što se predaje i trenutačno stanje

| Stavka | Obvezni sadržaj | Trenutačno stanje |
|---|---|---|
| Pisani seminar | Motivacija, detaljna matematika, algoritam, podaci i metodologija, eksperimenti, interpretacija, ograničenja i literatura | Planiran na hrvatskom; format i opseg otvoreni |
| Prezentacija | Povezano objašnjenje istog modela, metode, rezultata i zaključaka | Planirana na hrvatskom; format i trajanje otvoreni |
| Python kod | Dogovorena NMF metoda, smislene provjere i dokumentirano pokretanje koje omogućuje reprodukciju rezultata | Planirano; funkcija cilja, algoritam i ovisnosti otvoreni |
| Rezultati | Numerički rezultati i nalazi u domeni s jasnim podrijetlom, slike i tablice te iskreno navedena ograničenja | Planirano; eksperimenti nisu provedeni |

## Razumijevanje cijelog projekta

Zadatak može imati privremenog nositelja i drugu osobu koja ga pregledava. Time se ne smije
stvoriti matematički stručnjak koji jedini razumije izvod ili programerski stručnjak koji
jedini zna pokrenuti projekt. Pojedinačna zaduženja i način izmjene uloga dogovorit će se
kasnije.

Na ključnim točkama zajednički proći matematiku, algoritam, podatke, kod i interpretaciju.
Svaki član treba moći objasniti:

1. Što predstavljaju retci i stupci ulazne matrice te zašto je prikaz nenegativan.
2. Što predstavljaju rang i faktori te što je višeznačno ili nije jednoznačno odredivo.
3. Što funkcija cilja optimizira i kako iz nje slijede implementirana ažuriranja.
4. Koje su tvrdnje o optimalnosti i konvergenciji opravdane te uz koje pretpostavke.
5. Kako reproducirati rezultate pokretanja, protumačiti prikazane metrike i objasniti
   ograničenje ili neuspjeh.

Stvarna pitanja i preostale nejasnoće zabilježiti u zadatku ili primopredaji. Popis za provjeru
poticaj je za stvarni razgovor, a ne dokaz da se razgovor održao. Svaka osoba potvrđuje vlastito
razumijevanje; AI alat to ne može potvrditi umjesto nje.

## Još otvorene odluke

- Konkretna primjena, istraživačko pitanje, skup podataka te uvjeti pristupa i daljnje distribucije.
- Funkcija cilja, algoritam, inicijalizacija, numeričke zaštite, kriterij zaustavljanja i odabir ranga.
- Znanstvene Python ovisnosti, podržana verzija, okruženje i referentna bibliotečna implementacija.
- Prikladna referentna metoda, metrike domene i opseg eksperimenata.
- Format seminara i prezentacije, opseg i trajanje, kriteriji ocjenjivanja i rok.
- Pojedinačna zaduženja; Mislavova i Sarina GitHub korisnička imena i pristup.
- Dostupnost zaštite grana na GitHubu te povjerenje i aktivacija hookova na pojedinom računalu.

Za važne izbore pripremiti argumente i prijedlog, zatim dogovor zabilježiti u ADR-u i ažurirati
povezane dokumente. Postavljanje tijeka rada ne donosi te odluke.

## Granice opsega

NMF je središnja metoda. Klasteriranje dokumenata, modeliranje tema i hijerarhijski NMF
ranga 2 moguće su primjene ili proširenja iz literature, a nisu obvezne implementacije.
Tenzorske metode dio su naziva kolegija, a ne dodatni projektni zahtjev koji je korisnik
naveo. Trenutačno nisu potrebni web-proizvod, postupak objave aplikacije ni produkcijska usluga.
