# Virtuális eszköztervezés

**Széchenyi István Egyetem · GKLM_AUTM029 · 2026/27 I. félév**

Számítógép-konfigurációk minőségellenőrzése, csomagolása és szállítás-előkészítése Siemens Plant Simulation 2D-ben.

A feladatot három különálló Frame-re bontottam. A főmodell összeköti őket, minden állomásközi szalag 2 méteres. Nem akartam túlbonyolítani: ahol lehet, a Siemens saját, beépített funkcióit használom.

[**Eredeti beadandó kiírás (PDF)**](docs/assignment/PS_beadando_original.pdf) · [Modellbemutató (PDF)](docs/generated/Modelltajekoztato.pdf) · [Szöveges átirat](docs/generated/Feladatkiiras_atirat.pdf)

## A modell

| Rész | Beállítás |
| --- | --- |
| Minőségellenőrzés | 3 perc, 70% jó / 30% hibás |
| Címkézés | 20 másodperc mindkét ágon |
| Előkészítés | PC és csomagolóanyag: 20–20 másodperc |
| Csomagolás | 10 perc, 1 PC + 1 csomagolóanyag |
| Adminisztráció | 1 perc a csomagolás után és 1 perc a szállítás előtt |
| Rakodók | 5 és 10 perc, 66/34%-os elosztás |
| Kiszállítás | 1 perc |
| Szállítószalagok | 23 darab, mindegyik 2 m |
| Szimuláció | 10 000 beérkező számítógép |

Az eredeti kiírás nem ad meg beérkezési ütemet és szalagsebességet. Ezeket egyelőre **1 másodperc / darab** és **1 m/s** értékkel vettem fel. Az elágazási százalékok sztochasztikusak.

## Futtatás

A Plant Simulation Student Windowsra készült. Python 3.10+ is kell.

1. Klónozd le a repót (ha később GitHubra is publikálod az eredményt), vagy töltsd le ZIP-ben (csak helyi futtatáshoz).
2. Nyisd meg Windows alatt, és futtasd az **INDITAS.bat** fájlt.
3. Add meg a **saját hatkarakteres Neptun-kódodat**.
4. A sikeres futás után az output mappában lesz a Neptun-kód.spp, a mért eredmény, öt valódi Siemens-képernyőkép és a SHA256 ellenőrző manifeszt.

A kétféle ellenőrzés nem ugyanaz. A **GitHub CI** a Python-forrást és a modellgráfot teszteli, a **helyi Plant Simulation** pedig a tényleges .spp fájlt és a 10 000 darabos szimulációt.

Windows parancssorból:

    py -3 -m pip install -e ".[windows]"
    py -3 -m sze_virtualis_eszkoztervezes --neptun ABC123

Az ABC123 helyére a saját Neptun-kódod kerüljön.

### Ha a 10 000 darab már lefutott, csak a képexport hibázott

A 2404-es Siemens-futtatásban 2026. november 22-én a teljes modell
**4 200 734 másodperc** szimulációs időig eljutott, és a Siemens
elmentette a végső `.spp` fájlt. A hibát a régi képexport okozta.

A meglévő **`output` mappát ne töröld!** Frissítsd a programfájlokat,
majd indítsd az új **`EXPORT_KEPEK.bat`** fájlt. Ez egyetlen .spp-t
automatikusan kiválaszt, ellenőrzi a korábbi számlálókat, és legenerálja
az öt képet és a mérési PDF-et, teljes újraszimulálás nélkül.

Ha az SPP újranyitásakor a Siemens nullázta a futási statisztikát,
az ellenőrzés hibával leáll. Akkor a normál `INDITAS.bat` futtatásra
van szükség.

## Ellenőrzött beadandó

A 2026. november 22-i Siemens Plant Simulation 2404-futtatás kimenete már fent van:
**[JAXC3C.spp](output/JAXC3C.spp)** · [Mérési jegyzőkönyv](output/Siemens_meresi_jegyzokonyv.pdf) · [5 eredeti Siemens-kép](output/screenshots) · [teljes 12 pontos audit](docs/audit_2404.md).

A feltöltött eredményben **10 000 PC**, ebből **7 000 jó és 3 000 selejt**.
A rakodó 1 / rakodó 2 darabszáma **4 620 / 2 380**; a teljes mért
átfutási idő **4 200 734 s (48 nap, 14 óra, 52 perc, 14 másodperc)**.

A külön bináris fájlaudit az eredeti PDF-et, a Siemens SPP
konténerstruktúráját, a bemeneti/kimeneti számlálókat, a grafikonképeket,
a PDF-ben beágyazott képeket és a SHA256-értékeket ellenőrzi.
**61/61 ellenőrzés sikeres.** A [GitHub Actions-jegyzőkönyv](https://github.com/MrHumanRebel/sze_virtualis_eszkoztervezes/actions/workflows/submission-audit.yml) visszakereshető.

Az újranyitásos, interaktív Windowsos ellenőrzést a fájlaudit nem helyettesíti:
a `.spp`-t érdemes Plant Simulation 2404-ben ismét megnyitni és a
három beágyazott Frame-et átnézni.

## Bizonyítás és feltöltés

Sikeres helyi futás után az ellenőrzött állományok feltöltése:

    .\tools\publish_results.ps1 -Neptun ABC123

Az eredeti feladatlap már változatlanul fent van. A publikáló parancshoz **Git klón és hitelesített Git push** kell: a Download ZIP nem tartalmaz Git-adatokat. A Windowsos önhosztolt GitHub-runnerhez külön workflow is van.

A kimeneti feltöltés tartalmazza a modellellenőrzést, a szimuláció darabszámait, az átfutási időt, a screenshotokat és a fájlok SHA256-azonosítóit.

## Követelmények és határok

A részletes megfeleltetés a [docs/requirements.md](docs/requirements.md) fájlban, a folyamat [docs/architecture.md](docs/architecture.md) alatt van. A Windowsos hibakeresési lépések: [docs/troubleshooting.md](docs/troubleshooting.md).

A repóhoz tartozó forráskód és a PDF-generátor offline tesztelhető. A licencköteles Siemens programot nem lehet a GitHub ubuntu-latest runnerén lefuttatni. Valódi szimulációs igazolás csak Windowsos, telepített Plant Simulation környezetben készülhet.

**Beadásra a végleges Neptun-kód.spp fájl kell, nem ez a repó vagy a PDF.**
