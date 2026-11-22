# SzE – Virtuális eszköztervezés (GKLM_AUTM029)

**Siemens Tecnomatix Plant Simulation 2D beadandó: PC minőségellenőrzés, csomagolás és szállítás-előkészítés.**

Ez a repó a 2026/27. I. féléves, kétoldalas egyetemi feladat alapján épül. A megoldás tiszta, ellenőrizhető modellspecifikációból és **Windowsos Siemens COM-modellgenerátorból** áll.

## Gyors indítás (Windows)

1. Telepítsd a Siemens Plant Simulation Student verziót és a Python 3-at.
2. Töltsd le a repót (Code → Download ZIP), és csomagold ki.
3. Kattints az **INDITAS.bat** fájlra, majd add meg a 6 karakteres Neptun-kódodat.
4. Ellenőrizd az output mappában a NEPTUNKOD.spp fájlt, a szimuláció eredményét és a Plant Simulation grafikont.

Parancssori futás (a telepített csomaggal):

- Offline szerkezet megtekintése: python -m sze_virtualis_eszkoztervezes --plan
- Modell és teljes futtatás: python -m sze_virtualis_eszkoztervezes --neptun ABC123
- Csak modellépítés: python -m sze_virtualis_eszkoztervezes --neptun ABC123 --build-only
- Sablonból építés régebbi COM verzióhoz: python -m sze_virtualis_eszkoztervezes --neptun ABC123 --template C:\utvonal\ures.spp

A példa Neptun-kódot **cseréld ki a sajátodra**.

## Pontos specifikáció

- 3 külön 2D Frame: minőségellenőrzés, csomagolás, szállítás-előkészítés.
- 23 db, egyenként 2 m-es szállítószalag.
- Ellenőrzés: 180 s, 70% jó / 30% selejt; mindkét címkézés 20 s.
- PC és csomagolóanyag előkészítése: 20–20 s; 1 PC + 1 csomagolóanyag összeállítása 600 s.
- Csomagolási és szállítás-előkészítési adminisztráció: 60–60 s.
- Rakodó 1: 300 s / 66%, Rakodó 2: 600 s / 34%; kiszállítás: 60 s.
- Állomásstatisztikai Chart; 10 000 PC beérkezésének teljes átfutási ideje.

A PDF-ben **nem rögzített** szalagsebességet és érkezési időközt 1 m/s és 1 s modellezési feltételezésként állítottuk be. A véletlen százalékos elágazások darabszámai futásonként eltérhetnek.

## Minőség és státusz

A GitHub Actions **offline gráf- és paraméterteszteket** futtat; a CI nem Siemens-kompatibilitási teszt. Valódi, átadható SPP-fájl csak a helyben telepített Plant Simulation futtatása után jön létre. Amíg ez nem történik meg hibamentesen, **nem tekinthető teljesített beadandónak**.

Kapcsolódó dokumentáció: docs/requirements.md, docs/architecture.md, docs/troubleshooting.md.

A már meglévő MIT-licencet megtartottuk.
