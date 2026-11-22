# Hibakeresés / Validáció

1. A projekt ZIP-ből kicsomagolva fusson, ne a tömörített fájl belsejéből.
2. Windows és telepített Plant Simulation Student szükséges.
3. Python 3.10+ szükséges; a Windowsos telepítő pywin32 csomagot használ.
4. Először futtasd a modell szerkezeti ellenőrzését:
   python -m sze_virtualis_eszkoztervezes --plan
5. Majd: INDITAS.bat
6. A napló és az ellenőrzési JSON az output könyvtárba kerül.

## COM szerver nem található

Ellenőrizd, hogy a Plant Simulation telepítése regisztrálta-e
a Tecnomatix.PlantSimulation.RemoteControl COM szervert. Egyes Student
kiadások nem támogatnak minden COM-automatizálási funkciót.
A generátor nem képes jogszerűen feloldani az ilyen korlátozást.

## Az új Frame nem elérhető

Hozz létre a Siemens alkalmazásban egy tiszta új 2D modellt,
mentsd például C:\Temp\empty.spp útvonalra, és indítsd:

python -m sze_virtualis_eszkoztervezes --neptun ABC123 --template C:\Temp\empty.spp

## Assembly / Interface / Chart hibák

A Siemens verziófüggő objektumnevek és az Interface-osztály
viselkedése eltérhet. A hiba teljes SimTalk kódja a naplóban szerepel.
Nézd meg a generált Frame-ek csatlakozási pontjait és az Assembly
elődök sorrendjét (1. PC, 2. csomagolóanyag).

## Mit ellenőriz az élő validátor?

- 23 × 2 m szalag (Siemens adatvisszaolvasással);
- 11 feldolgozóállomás és 2 százalékos elágazás;
- időparaméterek, Source 10000-es mennyiség;
- 10000 PC jó vagy selejt kimenete és a 30%-os arány ±2 százalékpont;
- a teljes tétel szimulációs átfutási ideje.

## Beadás

Az egyetemi feladatra **csak a Neptun-kódod.spp** adandó be. Az offline
tesztek zöld státusza önmagában nem elég: a helyi Siemens futtatás
sikerét, az állomásstatisztikai Chartot és a modell teljes folyását
is ellenőrizni kell. Részlegesen generált SPP-t ne adj be.


## Plant Simulation 2404 / Unknown identifier Amount

A Source felületén a mező neve Amount, de SimTalkban a hozzá tartozó
attribútum **Number**. A javított kód előbb beállítja az Interval Adjustable
módot, majd a Number=10000, Stop=0 és Interval=1 s értékeket.

## Drain kimeneti számláló

A Drain törli a beérkező darabokat, ezért a NumMU (pillanatnyi tartalom)
nem alkalmas a teljes darabszám mérésére. A kumulatív érték a
**StatDeleted**. Az ellenőrzés két Drain számlálóját összegzi.

## Frissítés

A régi ZIP nem frissül: töltsd le újra a main ágat, vagy a repo
mappájában futtasd a git pull parancsot. A generátor új modellt hoz létre,
nem a korábbi félkész Frame-en folytatja a munkát.


## Ha a GitHub-feltöltő nem talál .git mappát

A Download ZIP nem Git-klón. A helyi modellgenerálás ZIP-ből is működik,
de a feltöltéshez `git clone` + GitHub-hitelesítés kell. A kész `output`
mappát át lehet másolni a friss Git-klónba, majd abból indítani a
`tools/publish_results.ps1` szkriptet.


## Plant Simulation 2404: `Unknown identifier 'AssemblyTableMode'`

A 2404-es COM szerver nem ismeri a `AssemblyTableMode` nevet. A régebbi
SimTalk név: **`PartListMode`**. Az új generátor előbb a `PartListMode`
attribútumot próbálja, szükség esetén az `AssemblyTableMode`-ot.
Minden esetben visszaolvassa, hogy a modellben ténylegesen `None` van-e.
Ez a mód mindkét elődről egy-egy elemet vár; a `MainMU=1` a PC,
a második bemenet a csomagolóanyag. Hibás visszaolvasásnál a program
nem menti jóvá a modellt.

A 2404-es logban szintén látható `SingleProc`, `Line` és `Assembly`
elnevezések a 2404-ben nem létező próbálkozások voltak, és a generátor
átváltott `Station`, `Conveyor`, `AssemblyStation` típusokra. Ezek
most elsődlegesen kerülnek kipróbálásra; így a napló rövidebb és tisztább.
