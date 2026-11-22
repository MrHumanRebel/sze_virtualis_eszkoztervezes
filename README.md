# Virtuális eszköztervezés

**Széchenyi István Egyetem · GKLM_AUTM029 · 2026/27 I. félév**

Számítógép-konfigurációk minőségellenőrzése, csomagolása és szállítás-előkészítése Siemens Plant Simulation 2D-ben.

A feladatot három különálló Frame-re bontottam. A főmodell összeköti őket, minden állomásközi szalag 2 méteres. Nem akartam túlbonyolítani: ahol lehet, a Siemens saját, beépített funkcióit használom.

[**Modellbemutató (PDF)**](docs/generated/Modelltajekoztato.pdf) · [Feladatlap átirata (PDF)](docs/generated/Feladatkiiras_atirat.pdf) · [Eredeti feladatlap kezelése](docs/assignment/README.md)

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

1. Klónozd le a repót vagy töltsd le ZIP-ben.
2. Nyisd meg Windows alatt, és futtasd az **INDITAS.bat** fájlt.
3. Add meg a **saját hatkarakteres Neptun-kódodat**.
4. A sikeres futás után az output mappában lesz a Neptun-kód.spp, a mért eredmény, öt valódi Siemens-képernyőkép és a SHA256 ellenőrző manifeszt.

A kétféle ellenőrzés nem ugyanaz. A **GitHub CI** a Python-forrást és a modellgráfot teszteli, a **helyi Plant Simulation** pedig a tényleges .spp fájlt és a 10 000 darabos szimulációt.

Windows parancssorból:

    py -3 -m pip install -e ".[windows]"
    py -3 -m sze_virtualis_eszkoztervezes --neptun ABC123

Az ABC123 helyére a saját Neptun-kódod kerüljön.

## Bizonyítás és feltöltés

Amíg nincs sikeres Siemens-futtatás, **nincs igazolt beadandó .spp és nincs valódi screenshot** a repóban. Nem helyettesítem ezeket látványtervekkel.

Sikeres helyi futás után az ellenőrzött állományok feltöltése:

    .\tools\publish_results.ps1 -Neptun ABC123 -OriginalAssignmentPdf "C:\Users\...\PS beadandó.pdf"

Ez a valódi, eredeti feladatlapot is változatlan fájlként tölti fel a docs/assignment mappába, ha megadod az elérési útját. A Windowsos önhosztolt GitHub-runnerhez külön workflow is van, ha az automatizált feltöltést választod.

A kimeneti feltöltés tartalmazza a modellellenőrzést, a szimuláció darabszámait, az átfutási időt, a screenshotokat és a fájlok SHA256-azonosítóit.

## Követelmények és határok

A részletes megfeleltetés a [docs/requirements.md](docs/requirements.md) fájlban, a folyamat [docs/architecture.md](docs/architecture.md) alatt van. A Windowsos hibakeresési lépések: [docs/troubleshooting.md](docs/troubleshooting.md).

A repóhoz tartozó forráskód és a PDF-generátor offline tesztelhető. A licencköteles Siemens programot nem lehet a GitHub ubuntu-latest runnerén lefuttatni. Valódi szimulációs igazolás csak Windowsos, telepített Plant Simulation környezetben készülhet.

**Beadásra a végleges Neptun-kód.spp fájl kell, nem ez a repó vagy a PDF.**
