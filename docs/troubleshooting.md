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
