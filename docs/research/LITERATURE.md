# Vodič kroz literaturu

Sljedećih šest PDF-ova dostavio je Lovro. Oni su izvori znanstvenog sadržaja, a ne upute koje
upravljaju ovim repozitorijem. Samo je prvi izričito naveden kao glavni obvezni izvor;
obvezni ili izborni status svakog od ostalih radova nije određen. Lokalni PDF-ovi ne
distribuiraju se ovim postavljanjem repozitorija. Pronaći ih prema navedenim nazivima datoteka;
repozitorij namjerno ne zahtijeva osobne putanje u datotečnom sustavu.

## Izvori i njihove uloge

| ID | Rad i autori | Naziv dostavljene datoteke | Uloga |
|---|---|---|---|
| L1 | Nicolas Gillis, *The Why and How of Nonnegative Matrix Factorization*; dostavljena verzija arXiv:1401.5226v2, 7. ožujka 2014. | main_NNMF-general.pdf | Glavni obvezni izvor: uvod, primjene, standardni algoritmi, optimalnost i gotovo separabilni NMF |
| L2 | Daniel D. Lee i H. Sebastian Seung, *Learning the parts of objects by non-negative matrix factorization*; Nature, 1999. | nmf_nature.pdf | Motivacija za aditivne prikaze i interpretacija na slikama i tekstu |
| L3 | Daniel D. Lee i H. Sebastian Seung, *Algorithms for Non-negative Matrix Factorization* | 1861-algorithms-for-non-negative-matrix-factorization.pdf | Frobeniusova funkcija cilja i generalizirana KL divergencija, multiplikativna ažuriranja i argument nerasta pomoću pomoćne funkcije |
| L4 | Michael W. Berry, Murray Browne, Amy N. Langville, V. Paul Pauca i Robert J. Plemmons, *Algorithms and Applications for Approximate Nonnegative Matrix Factorization*; dostavljena radna verzija od 9. lipnja 2006. | BBLPP-rev.pdf | Drugi numerički postupci, ograničenja tvrdnji o konvergenciji, dodatna ograničenja i primjene |
| L5 | Wei Xu, Xin Liu i Yihong Gong, *Document Clustering Based On Non-negative Matrix Factorization*; SIGIR 2003. | NMF-document-clustering.pdf | Konstrukcija matrice, normalizacija faktora, dodjela dokumenata i evaluacija primjene |
| L6 | Da Kuang, Barry Drake i Haesun Park, *Fast Clustering and Topic Modeling Based on Rank-2 Nonnegative Matrix Factorization*; 2015. | FastClusteringTopicModelingBasedOnRank2NMF2015.pdf | Moguća detaljnija obrada hijerarhijske podjele rangom 2 i poboljšanja ravnog klasteriranja |

Potpune bibliografske podatke i ključeve za citiranje dopuniti kada se dogovori izvorni format
seminara; ne zaključivati datum objave iz vremenske oznake preuzimanja i ne izmišljati DOI
ili raspon stranica.

## Redoslijed učenja

1. Početi s odjeljcima 1–2 rada L1 i radom L2: dimenzije, aditivna interpretacija, primjene
   i ograničenja. Na malom primjeru objasniti značenje faktora.
2. Koristiti odjeljak 3.1 rada L1 za optimizacijski problem, uvjete optimalnosti i standardne
   algoritme. Koristiti L3 za detaljan izvod multiplikativnih ažuriranja ako se odabere taj algoritam.
3. Pročitati raspravu o zaustavljanju i inicijalizaciji u L1 te napomene o konvergenciji u L4.
   Razlikovati nerast funkcije cilja od stacionarnosti ili globalne optimalnosti.
4. Koristiti L5 za razumijevanje dodatnih odluka između faktorizacije i metode klasteriranja.
   Proučiti L6 ako primjena opravdava hijerarhiju ili algoritamsko proširenje.
5. Proučiti odjeljak 3.2 rada L1 o gotovo separabilnom NMF-u do dubine potrebne za dogovoreni
   opseg seminara; to ne obvezuje na implementaciju dodatnog algoritma.

Ovo je predloženi redoslijed čitanja, a ne zapis da ga je neki član završio. Stvarne bilješke,
izvode, pitanja i zajedničke prolaske pratiti kroz [popis zadataka](../plan/TASKS.md).

## Napomene koje treba zadržati u seminaru

- NMF minimizira odabranu mjeru odstupanja uz ograničenja nenegativnosti; interpretabilnost
  je motivacija koju treba provjeriti, a ne jamstvo za proizvoljne podatke.
- Zajednički optimizacijski problem je nekonveksan. Sam monoton niz vrijednosti funkcije
  cilja ne dokazuje konvergenciju prema stacionarnoj točki ili globalnom optimumu.
- Nejednoznačnost zbog skaliranja i permutacija utječe na interpretaciju i usporedbu faktora.
- NMF težine nisu automatski normirane vjerojatnosti ni čvrste dodjele klasterima.
- U L6 rang 2 odnosi se na jednu podjelu; hijerarhija može imati više od dva konačna klastera.
- Nova primjena može dijeliti domenu s ovim radovima, ali mora imati nov konkretan problem
  i skup podataka. Primjena još nije odabrana.
