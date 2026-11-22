# Beadandó — végső követelményellenőrzés

**Széchenyi István Egyetem · GKLM_AUTM029 · Siemens Plant Simulation 2404**

A kiindulási alap a [változatlan eredeti feladatlap](assignment/PS_beadando_original.pdf). Az elkészült, Neptun-kódra nevezett [**JAXC3C.spp**](../output/JAXC3C.spp) a beadandó. A PDF-ek és képernyőképek ellenőrzési mellékletek, nem az egyetemi rendszerbe beadandó fájlok.

## A kiírás mind a 12 pontja

| # | Elvárás | Tényleges modell / eredmény | Státusz |
|---|---|---|---|
| 1 | Új 2D modell | A fő Frame natív 2D nézete elkészült | Rendben |
| 2 | Mappa és 3 külön beillesztett modell | `BeadandoModulok` / `QA_Template`, `PACK_Template`, `SHIP_Template`, 3 példány a főmodellben | Rendben |
| 3 | Minőségellenőrzés: 3 perc | `Ellenorzes_3perc`, `ProcTime=180 s` | Rendben |
| 4 | Hibás termékek: 30% | 70/30 elágazás; **3000 selejt** / 10 000 | Rendben |
| 5 | Jó és rossz címkézés: 20–20 s | Két külön `Station` | Rendben |
| 6 | Számítógép és csomagolóanyag előkészítése: 20–20 s | Két külön `Station` | Rendben |
| 7 | 1 PC + 1 csomagolóanyag, 10 perc | `AssemblyStation`, `MainMU=1`, két bemenet, `ProcTime=600 s`; **7000 csomagolt PC** | Rendben |
| 8 | Csomagolási és szállítási adminisztráció: 1–1 perc | Két külön 60 s-os állomás | Rendben |
| 9 | Rakodó 1: 5 perc, rakodó 2: 10 perc, 66/34% | 300/600 s; **4620 / 2380 PC**, pontosan 66/34% | Rendben |
| 10 | Kiszállítás: 1 perc | `Kiszallitas_1perc`, 60 s | Rendben |
| 11 | Állomások statisztikája grafikonon | `Allomas_Statisztika`, 11 állomás, működő Siemens `Resource Statistics` grafikon | Rendben |
| 12 | Átfutási idő 10 000 beérkező PC-re | 10 000 feldolgozott darab; **4 200 734 s** | Rendben |

A kiírás kifejezetten kérte a munkaállomások közötti **2 méteres szállítószalagokat**. A ténylegesen felépített modellben 23 külön `Conveyor` van, mindegyik `Length=2` paraméterrel, az ellenőrzött 1–1 bemeneti/kimeneti kapcsolatokkal.

## Tényleges Siemens-mérés

| Mutató | Mért adat |
|---|---:|
| Beérkező számítógép | 10 000 |
| Jó termék | 7 000 |
| Hibás termék | 3 000 |
| Csomagolt termék | 7 000 |
| Rakodó 1 | 4 620 |
| Rakodó 2 | 2 380 |
| Teljes tétel átfutása | **4 200 734 s** |
| Átváltva | **48 nap 14 óra 52 perc 14 másodperc** |

Az átfutási idő életszerű: az egyetlen csomagolóállomás 7000 × 600 s = **4 200 000 s** minimális munkát végez. A teljes idő ennél **734 másodperccel több**, ami a megelőző és követő műveletekkel összhangban van. Ez a **teljes tétel** átfutása, nem egyetlen számítógép átlagos átfutási ideje.

## Eredeti Siemens-képernyőképek

A valódi, fájlszinten és vizuálisan is ellenőrzött 2404-es exportok:

- [Főmodell](../output/screenshots/01_fomodell.png)
- [Minőségellenőrzés és selejtezés](../output/screenshots/02_minosegellenorzes.png)
- [Csomagolás, két bemenettel](../output/screenshots/03_csomagolas.png)
- [Szállítás-előkészítés, két rakodóval](../output/screenshots/04_szallitas_elokeszites.png)
- [Állomások statisztikai grafikonja](../output/screenshots/05_allomasstatisztika.png)

A háromoldalas [mérési jegyzőkönyv](../output/Siemens_meresi_jegyzokonyv.pdf) mind az öt képet tartalmazza. A részmodellek a PDF-ben kicsik, ezért az eredeti, teljes felbontású PNG-kből jobban vizsgálhatók a kapcsolatok.

## Fájl- és mérésellenőrzés

A feltöltött bináris fájlokkal külön [GitHub Actions-audit](https://github.com/MrHumanRebel/sze_virtualis_eszkoztervezes/actions/workflows/submission-audit.yml) készült:

- **61/61 fájlszintű ellenőrzés sikeres**, 0 hiba.
- Az eredeti kétoldalas PDF SHA256-azonosítója egyezik a kapott feladatlapéval.
- A 335 872 bájtos `.spp` OLE Compound File állományként strukturálisan olvasható.
- Az öt PNG mind létezik, valós képtartalma van, a SHA256-értékük egyezik a manifesttel.
- A mérési PDF 3 oldalas, 5 beágyazott képet tartalmaz, az SPP nevével és a mért átfutási idővel.
- A teljes tétel számlálói, selejtaránya, csomagolása, rakodóelosztása és időkorlátja megfelelnek a kiírásnak.

**Ami ettől még nem bizonyított automatikusan:** az SPP utólagos újranyitása és egy ismételt interaktív futtatás egy Windowsos Plant Simulation 2404-példányban. Az eredeti futási napló és a képek valós Siemens-futtatásból származnak; a fájlszintű ellenőrzés nem helyettesíti az újranyitási próbát.

## Beadás

A tanulmányi rendszerbe a **[JAXC3C.spp](../output/JAXC3C.spp)** fájlt töltsd fel — sem a ZIP, sem a PDF, sem a `JAXC3C.spp.previous` nem a beadandó.

Az eredeti PDF nem szabott meg beérkezési időközt vagy szalagsebességet. A modell a beérkezéseket 1 s-os időközzel, a szalagokat 1 m/s-os sebességgel futtatja. Ezek külön feltüntetett modellezési feltevések.
