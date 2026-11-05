# ADR-0003: Primijeniti KL-NMF na automatsko prepisivanje gitare u note

**Datum:** 2026-11-05 · **Status:** prihvaćeno (tim prema Lovrinoj izjavi, 2026-11-05)

## Kontekst

ADR-0001 ostavio je otvorenima primjenu, skup podataka, funkciju cilja i algoritam.
[Prijedlog tema](../prijedlog-tema/prijedlog-tema-nmf.pdf) od 2026-11-01 usporedio je četiri teme.
Preporučio je temu 1, a temu 2 naveo kao rezervu. Za temu 2 postoji radni nacrt
[skripte](../../research/skripta-gitara/skripta-gitara.pdf) koji nitko još nije pregledao.
Lovro je 2026-11-04 lokalno isprobao cijeli lanac za temu 2. Ta proba nije dio repozitorija,
a njezini brojevi nisu rezultati projekta.

Lovro je 2026-11-05 u razgovoru naveo da je tim prihvatio temu 2. Ovaj zapis bilježi tu izjavu.
PR #39, koji ga uvodi, spojen je bez pregleda na GitHubu (ADR-0002, dodatak 2026-11-05).
Lovro je naveo da Sara i Mislav to dopuštaju. Oni zapis potvrđuju na sastanku Z0 (issue #5)
ili traže izmjenu novim PR-om.

## Odluka

1. **Pitanje.** Može li NMF iz snimke akustične gitare prepoznati koje se note sviraju i kada,
   i to za gitarista kojeg model nije vidio tijekom učenja?
2. **Podaci.** GuitarSet 1.1.0 (Zenodo, zapis 3371780, CC BY 4.0): mono snimke mikrofona i
   anotacije. Skup ima 360 snimki šest gitarista. Sirovi podaci ostaju izvan Gita, a repozitorij
   čuva upute za preuzimanje i kontrolne zbrojeve.
3. **Matrica.** $A\in\mathbb{R}_{\geq0}^{m\times n}$ je amplitudni spektrogram: retci su
   frekvencijski binovi, a stupci vremenski okviri. Stupci $W\in\mathbb{R}_{\geq0}^{m\times r}$
   su predlošci tonova, a retci $H\in\mathbb{R}_{\geq0}^{r\times n}$ njihove aktivacije. Rang $r$
   jednak je broju tonova u modelu, uz moguću dodatnu komponentu za pozadinu.
4. **Funkcija cilja i algoritam.** Koristimo generaliziranu KL divergenciju
   $D(A\,\|\,WH)$ i izmjenična multiplikativna ažuriranja Leeja i Seunga (L3, teorem 2).
   Predlošci se uče na gitaristima za učenje. Novu snimku obrađujemo uz fiksirani $W$, pa
   rješavamo konveksan problem po $H$ istim pravilom.
5. **Vrednovanje.** Koristimo unakrsnu provjeru s izostavljenim gitaristom (šest podjela).
   Mjere su preciznost, odziv i $F_1$ na razini nota, uz toleranciju početka 50 ms i
   toleranciju visine 50 centi. Rezultate prijavljujemo po gitaristu i kao prosjek.
   Hiperparametre biramo samo na gitaristima za učenje.
6. **Referentne metode.** Isti postupak s Frobeniusovom normom (L3, teorem 1) i jednostavan
   odabir spektralnih vrhova.
7. **Ostaje otvoreno:**
   - način učenja predložaka (maskirani NMF ili prosjek spektara);
   - parametri STFT-a, normalizacija razine snimki i pozadinska komponenta;
   - mreža hiperparametara i dodatne mjere;
   - Python ovisnosti, format seminara i prezentacije te rok.

   O tome se odlučuje u zadacima iz [podjele rada](../PODJELA.md), a odluke se bilježe u ADR-u
   ili u [metodologiji](../METHODOLOGY.md).

## Obrazloženje

- Prema prijedlogu tema, tema 2 ima najčišći dokaz i najjasniju mjeru uspjeha.
  Cijeli dokaz nerasta pomoću pomoćne funkcije nalazi se u L3 (odj. 6). L4 (odj. 3.1) i L1 (odj. 3.1.2)
  omogućuju preciznu raspravu o tome što taj dokaz ne pokazuje.
- Pokriva glavni izvor: L1 odj. 2 (analiza glazbe kao primjena), odj. 3 (NP-težina,
  nejedinstvenost) te odj. 3.1, 3.1.2, 3.1.7 i 3.1.8 (potproblemi, multiplikativna pravila,
  zaustavljanje, inicijalizacija).
- Spektar akorda približno je zbroj spektara tonova, pa je aditivni nenegativni model prirodan.
  Uz fiksirani $W$ problem je konveksan, što se dobro objašnjava i brzo računa.
- Podaci su mali (oko 0,7 GB za mono snimke i anotacije), označeni i pod licencom koja dopušta
  uporabu uz navođenje izvora.
- Problem se razlikuje od primjera u priloženim radovima. L1 navodi analizu glazbe tek kao
  područje primjene, a mi radimo konkretnu transkripciju gitare na GuitarSetu, uz provjeru
  na novom gitaristu.

## Odbačene mogućnosti

Tim nije zabilježio razloge izvan prijedloga tema; navedeni su rizici iz prijedloga.

- **Tema 1, Kopački rit.** Najviše pokriva Gillisa, ali traži najviše pripreme podataka
  (oblaci, malo proljetnih snimaka). Referenca WorldCover je nesavršena, a pravilo dijeljenja
  iz L6 možda ne odgovara spektrima.
- **Tema 3, šahovski repertoar.** Najbliža je L5 i L6, ali otvaranje ovisi i o protivniku.
  NMF možda ne bi pobijedio igračev vlastiti histogram.
- **Tema 4, histološka bojila.** Ima najzorniju geometriju, ali traži medicinsko predznanje.
  Validacijske slike možda su već normalizirane, a podrijetlo isječaka nije poznato.

## Posljedice

- U istoj promjeni usklađuju se `AGENTS.md`, `README.md`, [projekt](../PROJECT.md),
  [zadaci](../TASKS.md), [metodologija](../METHODOLOGY.md) i
  [literatura](../../research/LITERATURE.md). T2 je dovršen, a T3 djelomično.
- Implementacija treba učitavanje podataka, STFT, multiplikativna pravila za KL i Frobeniusovu
  normu, transkripciju, vrednovanje i zapis podrijetla pokretanja.
- Seminar prati strukturu skripte. Skripta ostaje nepregledan nacrt dok je tim ne prođe.
- U ograničenjima treba prijaviti da su predlošci nadzirani i da gitaristi u skupu možda
  sviraju isti repertoar. To treba provjeriti iz podataka.
