# ADR-0004: Podijeliti rad na tri niti od matematike do rezultata, uz pregled u krug

**Datum:** 2026-11-05 · **Status:** prihvaćeno (tim prema Lovrinoj izjavi, 2026-11-05)

## Kontekst

ADR-0001 traži da svaki član razumije cijeli projekt i da se znanje dugoročno ne dijeli po
područjima. Podjelu zadataka ostavio je za kasnije. Prijedlog tema predložio je rad po nitima.
Nakon izbora teme 2 (ADR-0003) Lovro je predložio tri niti, A, B i C. Svaka nit sadrži
matematiku, kod, eksperimente, dio seminara i dio prezentacije. Tim je birao tko preuzima koju nit.

Lovro je 2026-11-05 u razgovoru naveo raspored: **Sara je osoba A, Lovro osoba B, Mislav osoba
C.** Isti je dan zatražio da se raspored zabilježi i da svatko dobije detaljan plan. Planove je
napisao Lovro uz pomoć AI alata. Oni su prijedlog sadržaja koji Sara i Mislav potvrđuju ili
mijenjaju pregledom PR-a u kojem su uvedeni.

## Odluka

1. **Tri niti.**

   | Nit | Nositelj | Sadržaj |
   |---|---|---|
   | A: od snimke do matrice i od nota do $F_1$ | Sara | Signal i STFT, KL divergencija i njezina statistička interpretacija, podaci, vrednovanje, metoda spektralnih vrhova |
   | B: od matrice do faktora | Lovro | Uvjeti optimalnosti, izvod multiplikativnih pravila, dokaz nerasta, jezgra NMF-a i njezini testovi, okruženje, zapis podrijetla, konvergencija |
   | C: od faktora do nota | Mislav | Model i struktura problema, granice tvrdnji o konvergenciji, maskirani NMF, učenje predložaka, transkripcija, unakrsna provjera i glavni eksperiment |

   Svaka nit ima matematiku, kod s testovima, eksperimente, poglavlja seminara i slajdove.
   Detalji su u [podjeli rada](../PODJELA.md) i osobnim planovima.
2. **Nositelj, a ne vlasnik.** Niti i pojedine zadatke smijemo zamijeniti ako se dogovorimo.
   Promjenu bilježimo u issueu i u podjeli rada.
3. **Pregled u krug: A pregledava B, B pregledava C, C pregledava A.** Recenzent pregledava
   PR-ove niti. Neovisno izvodi njezine dokaze, objašnjava je na zajedničkim prolazima i
   reproducira njezine eksperimente. `.github/CODEOWNERS` automatski traži njegov pregled.
   Pravilo pregleda iz ADR-0002 ispunjava odobrenje bilo kojeg drugog člana tima.
4. **Zadaci su GitHub issuei.** Imaju oznake niti i područja i pripadaju milestoneima
   Faza 0 do Faza 4. Jedan issue znači jednu granu; PR zatvara issue s `Closes #N`.
5. **Zajedničko razumijevanje.** Održavamo tri zajednička prolaza i probnu obranu.
   Na probnoj obrani svatko odgovara i na pitanja iz tuđih niti.
6. **Rok nije poznat**, pa faze nemaju datume. Datume dodajemo milestoneima kad rok saznamo.

## Obrazloženje

- Korisnik je tražio da svatko radi u svakom području: kod pišu svi i matematiku rade svi.
  Svaka nit zato ide od izvoda do rezultata.
- Najzahtjevniji dokazi su podijeljeni:
  - A dokazuje nenegativnost KL divergencije i vezu s Poissonovom izglednošću;
  - B dokazuje teorem o nerastu;
  - C obrađuje granice tvrdnji o konvergenciji i maskirani NMF.
- Moduli niti su razdvojeni, pa paralelne grane rijetko mijenjaju iste datoteke.
- Pregled u krug znači da svaku nit dobro poznaju barem dvije osobe. Na prolazima se treća
  osoba uči od recenzenta, a ne samo od nositelja.

## Odbačene mogućnosti

- **Podjela po području** (jedna osoba matematika, druga kod, treća eksperimenti). Protivi se
  ADR-0001 i stvara jedinog stručnjaka za svako područje.
- **Niti po etapama iz prijedloga tema** (do prve faktorizacije, do strukture, do odgovora).
  Za temu 2 rang određuje skup tonova, pa bi etapa „struktura” bila pretanka.
- **Podjela po gitaristima ili dijelovima podataka.** Ne dijeli matematiku i svima daje isti
  kod.
- **Svi rade sve istodobno.** Grane bi se sudarale, a odgovornost ne bi bila jasna.

## Posljedice

- `AGENTS.md` (odjeljci 1 i 3), [projekt](../PROJECT.md), [zadaci](../TASKS.md),
  [protokol promjena](../../CHANGE_PROTOCOL.md), predložak PR-a i [tijek rada](../PIPELINE.md)
  navode podjelu i način rada s issueima.
- Na GitHubu postoje:
  - oznake niti i područja;
  - milestonei Faza 0 do Faza 4;
  - issuei za svaki zadatak iz osobnih planova;
  - predlošci issuea i `.github/CODEOWNERS`;
  - zaštita grane `main` koja traži odobrenje drugog člana i uspješan CI.
- Kad Sara i Mislav pregledaju PR, svaku promjenu osobnih planova treba unijeti i u
  pripadajuće issuee.
