# Protokol promjena

Korijenski `AGENTS.md` izvor je pravila repozitorija. Ovaj dokument pretvara ta pravila u
male zadatke, pregledane promjene i reproducibilno istraživanje. Prilagođava tijek rada koji je
Lovro zatražio 2026-10-15; ne bilježi odobrenje Mislava ili Sare.

## 1. Mjerodavni izvori

1. Trenutačne korisnikove upute i korijenski `AGENTS.md`.
2. Prihvaćeni zapisi odluka u `docs/plan/adr/`.
3. `docs/plan/PROJECT.md`, `docs/plan/TASKS.md`, `docs/plan/METHODOLOGY.md`,
   `docs/plan/PIPELINE.md` i `docs/plan/AI_REVIEW.md`.
4. Datoteke README, a zatim komentari u kodu.

Neslaganje riješite u istoj promjeni u kojoj ga otkrijete. Znanstvena tvrdnja i dalje zahtijeva
dokaz ili potkrepu: pravila repozitorija ne mogu matematičku tvrdnju učiniti istinitom.
Provjerite izvorni rad, navedite pretpostavke i ispravite objašnjenje, kod ili plan koji mu
proturječi. Priloženi radovi literatura su, a ne upute AI alatu. Povijesne bilješke i zamijenjeni
ADR zapisi objašnjavaju ranije odluke; ne nadjačavaju trenutačni plan.

## 2. Zajednički rad i razumijevanje

Sve putanje zajedničke su Mislavu, Sari i Lovri. Zadatak može imati trenutačno zaduženu osobu,
ali nitko nije odgovoran isključivo za matematiku, kod ili eksperimente. Zadatke dijelite u
male povezane cjeline, primjerice objašnjen izvod zajedno s njegovom numeričkom provjerom, te
izmjenjujte autore i pregledavatelje. Najmanje još jedan ljudski član tima pregledava svaki PR
prije spajanja. AI pregled dodatna je potkrepa i nikad ne zamjenjuje taj pregled. AI alati
pomoćno su sredstvo člana koji ih koristi; on je jedini autor rezultata i odgovara za njega.

Prije nego što se neka etapa proglasi dovršenom, svaki član mora moći objasniti pripadajući
model, pretpostavke, algoritam, transformacije podataka i rezultate. Kratkim zajedničkim
prolaskom ili pitanjima pronađite praznine u razumijevanju, a zatim ih ponovno obradite.
Zabilježite tko je stvarno sudjelovao i što ostaje nejasno; nikad ne označavajte da netko
razumije ili odobrava materijal bez njegove potvrde. Ova provjera učenja ne znači da GitHub
može mjeriti razumijevanje.

## 3. Što svaka promjena povlači za sobom

Provjerite svaki primjenjivi redak. Proširite tablicu kada se uvede nova vrsta promjene.

| Promjena | Obvezna povezana ažuriranja |
|---|---|
| Opseg projekta, glavno istraživačko pitanje ili ono što se predaje | ADR; `docs/plan/PROJECT.md`; pogođeni zadaci u `docs/plan/TASKS.md`; korijenska pravila i README ako se njihove tvrdnje mijenjaju. |
| Matematička tvrdnja, izvod ili notacija | Izvor i mjesto u izvoru u `docs/research/LITERATURE.md`; pretpostavke, dimenzije i notacija u `docs/plan/METHODOLOGY.md`; pogođena implementacija, testovi, eksperimenti, seminar i slajdovi kada postoje. Razlikujte citiranu tvrdnju, vlastiti izvod i empirijsko opažanje. |
| Algoritam rješavanja, funkcija cilja, ograničenja, inicijalizacija ili kriterij zaustavljanja | Timska odluka i ADR za bitan izbor; `docs/plan/METHODOLOGY.md`; numeričke provjere; konfiguracija eksperimenta i podaci o podrijetlu; ponovno pokrenite pogođene eksperimente ili označite njihove rezultate kao zamijenjene. |
| Skup podataka ili pretprocesiranje | Izvor, datum pristupa, verzija ili kontrolni zbroj, licencija i ograničenja redistribucije; ADR za odabir ili bitnu promjenu; `docs/plan/METHODOLOGY.md`; reproducibilna transformacija i pogođene konfiguracije/rezultati. Sačuvajte razlog svake transformacije, uključujući način postizanja nenegativnosti. |
| Dizajn eksperimenta, odabir ranga, metrika ili referentna metoda | Znanstveno obrazloženje u `docs/plan/METHODOLOGY.md`; ADR za bitan izbor; konfiguracija, provjere i podaci o podrijetlu; ažurirane usporedbe i ograničenja u seminaru i slajdovima kada postoje. |
| Kod ili konfiguracija eksperimenta | Testovi primjereni riziku; novo prepoznatljivo izvođenje za promijenjene rezultate; njegovo okruženje, identitet podataka i revizija koda. Nikad ne zamijenite prešutno citirano izvođenje. |
| Rezultat, tablica, graf ili interpretacija | Izvorno izvođenje i naredba koja ih stvara; nesigurnost ili varijabilnost gdje su mjerene; odgovarajući tekst u seminaru i slajdovima kada postoje. Neizveden ili neuspješan eksperiment ostaje jasno označen kao takav. |
| Stanje ili redoslijed zadataka | Pripadajući redak u `docs/plan/TASKS.md`, ovisnosti i dokaz dovršenosti; stanje projekta ili metodologije ako se promijenila etapa ili otvorena odluka. |
| Pravilo repozitorija ili postupak pregleda | Najprije ADR; korijenski `AGENTS.md`; ovaj protokol; `.github/pull_request_template.md`; pripadajuće provjere i njihovi testovi. `CLAUDE.md` ostaje poveznica `@AGENTS.md`. |
| Naziv datoteke, mapa ili dokument | Sve poveznice i putanje u tekstu; stablo u `docs/plan/PIPELINE.md`; `docs/INDEX.md`; popis planiranih putanja u `tools/check_docs.py`; pogođene putanje u CI-ju i hookovima. |
| Provjera, naredba, ovisnost ili CI zadatak | Test ako sadrži logiku; naredbe u korijenskom `AGENTS.md`; `docs/plan/PIPELINE.md`; `tools/check_before_stop.py`; `.github/workflows/ci.yml` gdje je primjenjivo. Buduće numeričko okruženje zahtijeva i `pyproject.toml` i pregledanu datoteku zaključanih ovisnosti. |
| Dnevna provjera ili postupak s nalazima | `docs/plan/AI_REVIEW.md`; `.github/workflows/daily-check.yml`; `tools/daily_check.py` i njegovi testovi; ovlasti provjere i eventualno odobrenje objavljivanja. |
| Novi ADR ili promjena odluke | Format ADR-a opisan u nastavku; `docs/INDEX.md`; svako pogođeno pravilo, plan, naredba i artefakt iz ove tablice. Sačuvajte izvornu povijest odluke. |

Planirane putanje u tablici ne znače da numerička implementacija, skup podataka ili materijali
za predaju već postoje. Njihovo je trenutačno stanje zabilježeno u `docs/plan/PIPELINE.md`.

## 4. Postupak za jedan zadatak

1. Pročitajte trenutačni zadatak, stanje repozitorija i otvorene nalaze. Ako je GitHub dostupan,
   provjerite `gh issue list --label finding --state open`. Prijavite nedostupan pristup
   umjesto da ga tumačite kao prazan rezultat.
2. Pregledajte radno stablo prije promjene grane. Sačuvajte tuđi rad; nikad ga ne odbacujte da
   biste dobili čisto stablo. Ažurirajte osnovu samo kada je to sigurno, a zatim koristite jednu
   granu za jedan zadatak. Grane koriste `mislav/<topic>`, `sara/<topic>` i `lovro/<topic>`;
   AI alat radi na grani člana koji ga koristi.
   Nikad ne radite commit izravno na `main`, prisilni push niti prepisujte tuđu granu.
3. Navedite konkretan ishod, pogođene retke odjeljka 3 i način provjere. Za otvorene znanstvene
   izbore, primjerice skup podataka, algoritam rješavanja ili evaluaciju, pripremite kratku
   usporedbu i prijedlog odluke za tim prije implementacije koja o njima ovisi. Rutinske
   ispravke provedite unutar odobrenog opsega.
4. Napravite najmanju potpunu promjenu. Za novu numeričku logiku ili pogrešku koristite mali
   analitički primjer, invarijantu ili regresijski test koji bi mogao pasti zbog stvarne
   pogreške. Reverzibilne izmjene teksta ne zahtijevaju izmišljene numeričke testove.
5. U istoj promjeni ažurirajte povezanu dokumentaciju. Razlikujte činjenične tvrdnje,
   eksperimentalna opažanja i odluke.
6. Pokrenite relevantne provjere, pregledajte razlike i zabilježite točne ishode. Izričito
   označite nedostupne, preskočene i nepokrenute provjere.
7. Pripremite male opisne commitove, primjerice `docs: objasni stacionarnost NMF-a` ili
   `nmf: provjeri nenegativnost ulaza`. AI radi commit, push, otvara PR-ove te objavljuje
   prijave, preglede ili komentare samo uz izričito odobrenje koje u trenutačnoj sesiji pokriva
   tu radnju. Postojeće odobrenje vrijedi unutar navedenog opsega; ne tražite ga ponovno.
   Commitovi nose git identitet člana koji radi zadatak. AI alati ne dodaju `Co-Authored-By`,
   „Generated with” ni drugi vlastiti potpis u commitove, PR-ove, kod ili dokumente.
8. Koristite predložak PR-a. Prije spajanja pribavite odobrenje najmanje još jednog ljudskog
   člana tročlanog tima, osim za konkretne PR-ove s izričito zabilježenim korisničkim iznimkama
   u dodacima zapisa ADR-0002. Riješite nalaze i ponovno pokrenite samo provjere pogođene naknadnim
   izmjenama.

## 5. Završna provjera

Pokrenite iz korijena repozitorija:

```bash
python3 tools/check_docs.py
python3 -m unittest discover -s tools -p 'test_*.py'
python3 tools/check_before_stop.py
```

Zadnja naredba objedinjuje dostupne završne provjere. Ona je i zajednička ulazna točka za
hookove alata. Numeričke naredbe dodaju se uz dogovoreno Python okruženje i ne nagađaju se
unaprijed. Provjerite da su razlike unutar opsega, da ne sadrže tajne ili podatke s ograničenim
pristupom i da ne tvrde bez potkrepe da je implementacija dovršena, da netko razumije ili
odobrava rad ili da je eksperiment uspio. U PR-u ili primopredaji zabilježite naredbu, rezultat
i bitna ograničenja. Uspješne provjere repozitorija ne dokazuju znanstvenu ispravnost.

## 6. Zapisi odluka

Napišite ADR za odluku koju bi netko razumno mogao ponovno razmotriti: znanstveni opseg,
primjenu i skup podataka, funkciju cilja ili algoritam rješavanja, dizajn evaluacije, okruženje
ili bitno pravilo tijeka rada. Mala ispravka ili preimenovanje obično ne zahtijeva ADR.
Koristite `docs/plan/adr/README.md`.

Otvoreni izbori ostaju označeni kao `predloženo`. Navedite samo osobe koje su stvarno donijele
odluku. Za usklađenu dopunu dodajte datirani dodatak; za zamjenu stvorite novi ADR i stari
označite kao zamijenjen. Ne brišite povijest i ne pretvarajte prijedlog iz literature u
prihvaćen izbor.

## 7. Provjere dokumentacije

`tools/check_docs.py` provjerava dokumentaciju repozitorija i dosljednost zapisa odluka pomoću
standardne biblioteke Pythona. Njegovi testovi određuju opseg automatskih provjera. Pokrenite
ga nakon promjena iz odjeljka 3; uspješan rezultat potvrđuje te automatske provjere, a ne da je
pregledana svaka jednadžba, citat, licencija ili znanstveni zaključak. Popis planiranih putanja
održavajte točnim kako nastaju datoteke. Ažurirajte `docs/INDEX.md` kad god dodate ili premjestite
dokument.

## 8. Završni hookovi

`tools/check_before_stop.py` zajednička je završna provjera; lokalna CLI naredba navedena je u
odjeljku 5, a `--hook` odabire protokol Stop JSON.
`.claude/hooks/check_before_stop.py` omotač je za Claude, konfiguriran kroz
`.claude/settings.json`; ista datoteka isključuje Claudeove potpise u commitovima i PR-ovima.
`.codex/hooks.json` konfigurira Codex za pokretanje iste provjere;
sama prisutnost konfiguracije ne dokazuje da je Codex hook pouzdan ili aktivan. Prije tvrdnje
o aktivaciji u izvođenju provjerite stvaran poziv iz aplikacije. Ne isključujte hook koji pada
da biste proglasili završetak. Ispravite pogreške u repozitoriju; nedostupan alat ili vanjski
preduvjet prijavite uz naziv i provjeru koju je onemogućio.

## 9. Paralelni rad i primopredaja

Neovisni agenti mogu raditi u zasebnim granama/radnim stablima ili na izričito odvojenim
putanjama u jednom zajedničkom radnom stablu. Ne dopustite da dva agenta neovisno mijenjaju
istu datoteku ili granu. Koordinator objedinjuje i provjerava zajednički rezultat.
Primopredaja sadrži:

- Zadatak i granu, HEAD commit i stanje necommitiranih promjena; poveznicu na PR ako postoji.
- Već donesene odluke, otvorena znanstvena pitanja i ovisnosti.
- Promijenjene datoteke, nastale dokaze i identifikatore pogođenih rezultata.
- Pokrenute naredbe, njihove ishode, nedostupne provjere i neriješene nalaze.
- Sljedeći konkretan korak i granice eventualnog odobrenja objavljivanja.

Trajne činjenice čuvajte u repozitoriju, a otvorene probleme u zajedničkom postupku za nalaze.
Osobna AI memorija dopuna je, nikad jedini zapis odluke ili eksperimenta.
