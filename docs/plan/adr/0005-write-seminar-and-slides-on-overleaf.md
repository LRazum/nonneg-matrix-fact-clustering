# ADR-0005: Pisati seminar i prezentaciju na Overleafu, odvojeno od GitHuba

**Datum:** 2026-11-05 · **Status:** prihvaćeno (prema Lovrinoj izjavi, 2026-11-05)

## Kontekst

ADR-0003 ostavio je otvorenima format seminara i prezentacije te rok. Struktura repozitorija
predviđala je mape seminar/ i presentation/ (AGENTS.md, odjeljak 4), a osobni planovi
tražili su da nacrti matematičkih poglavlja budu u mapi seminar/ i da ih recenzent provjeri
u PR-u. [Prijedlog za Z0](../Z0_PRIJEDLOG.md) prvo je predložio LaTeX u repozitoriju.

Lovro je 2026-11-05 u razgovoru naveo da će se seminar i prezentacija pisati na Overleafu,
potpuno odvojeno od GitHuba. Isti je dan naveo da tim termin dobiva u tjednu od 2026-11-09 i
da rok zatim određuje sam. Sara i Mislav zapis potvrđuju na sastanku Z0 (issue #5) zajedno s
ADR-0003 i ADR-0004.

## Odluka

1. **Seminar i prezentacija** pišu se u dva Overleaf projekta. Repozitorij ih ne sadrži i nema
   mape seminar/ ni presentation/.
2. **Repozitorij** sadrži kod, testove, eksperimente, opis podataka i rezultate, uključujući
   slike i tablice koje ulaze u seminar.
3. **Matematički nacrti** (A3, B4 i C1) i poglavlja (A7, B7 i C7) nastaju u Overleafu.
   Recenzent niti komentira ih u Overleafu, a sažetak nejasnoća i ishod provjere zapisuje u
   issue zadatka, jer GitHub ne vidi Overleaf.
4. **Veza s pokretanjima** (AGENTS.md, pravilo 8):
   - slike se spremaju kao PDF u `results/`, s identifikatorom pokretanja u nazivu, i takve se
     učitavaju na Overleaf;
   - brojevi u tablicama prepisuju se iz zapisa pokretanja, a u izvoru seminara uz tablicu stoji
     komentar s identifikatorom pokretanja.
5. **Predaja:** pri predaji se izvoze PDF i izvorni kod oba Overleaf projekta.
6. **Ostaje otvoreno** i dogovara se na Z0: prevoditelj, struktura datoteka, zajedničke oznake i
   literatura u Overleafu (prijedlog u [prijedlogu za Z0](../Z0_PRIJEDLOG.md), odjeljak 4) te rok.

## Obrazloženje

- Tim radije piše u Overleafu: istodobno uređivanje i komentari bez lokalne instalacije
  TeX-a i bez Git postupka za tekst.
- Kod i rezultati ostaju pod istim pravilima ponovljivosti kao i dosad, pa odvajanje teksta ne
  slabi pravilo 6 iz AGENTS.md.
- Pravilo 8 zadovoljava se identifikatorom pokretanja u nazivu slike i komentaru uz tablicu,
  bez potrebe da seminar bude u Gitu.

## Odbačene mogućnosti

- **LaTeX u repozitoriju** (prvi prijedlog za Z0): svaka bi promjena teksta išla kroz PR, a svaki
  član trebao bi lokalni TeX. Tim ga nije odabrao.
- **Overleaf sinkroniziran s GitHubom:** tim je izričito tražio potpuno odvajanje.

## Posljedice

- `AGENTS.md` (odjeljci 1 i 4), `README.md`, [projekt](../PROJECT.md), [zadaci](../TASKS.md),
  [tijek rada](../PIPELINE.md), [podjela rada](../PODJELA.md), osobni planovi i popis
  `PLANNED` u `tools/check_docs.py` više ne predviđaju mape seminar/ i presentation/.
- Issuei A3, B4, C1, A7, B7, C7, A8, B8, C8, A9, B9 i C9 (#9, #12, #13, #27, #29, #32–#35,
  #18, #20, #23) upućuju na Overleaf umjesto na mape u repozitoriju i PR.
- Z5 (#37) usklađuje oznake i brojeve između Overleafa i koda ručno.
- Kad tim odredi rok, milestonei dobivaju datume, a TASKS.md i PODJELA.md bilježe ga.
