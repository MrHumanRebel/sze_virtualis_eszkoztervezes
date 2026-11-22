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


## Plant Simulation 2404: Unknown identifier 'EndTime'

A 2404-es EventController COM objektuma a futási végidőt az **End**
attribútumban kezeli. Az EndTime ebben a telepített verzióban nem található.
A generátor az End nevet próbálja először, majd újabb verziók esetén az
EndTime-ot. A 12 000 000 másodperces végidőt visszaolvassa és ellenőrzi,
mielőtt folytatná a modellépítést. A StartStat beállítás 0 s marad.

A hiba a 2026-11-22 19:57-es, valódi Siemens 2404 COM-naplóban szerepelt.


## Futás 0 / 10 000 kimenettel, normál szimulációs sebességen

A naplóban 2026-11-22 20:00:02-kor a valódi Siemens-szimuláció
sikeresen elindult, de az első 30 valódi másodpercben 0 kimenetet adott.
Ez önmagában **nem hiba**: az első ellenőrzés 180 szimulációs
másodpercet vesz igénybe, majd 20 másodperc címkézés következik.
A csomagolás további 600 másodperc.

Az EventController `start` alapértelmezett sebessége megtarthatja
a valós időskálázást, ezért a 10 000 darabos futás rendkívül sokáig tarthat.
Az új indítás:

`EventController.start(false,false)`

Ez a Siemens hivatalos SimTalk paraméterezése: nincs animáció
(`WithAnimation=false`), nincs real-time korlátozás
(`RealTime=false`). A modell teljes szimulációs idejét nem rövidíti:
csak a számítás faliórás végrehajtását gyorsítja.

Az `output/progress.json` minden 15 valódi másodpercben frissül, és
külön mutatja a szimulációs időt, a forrás/kontroll/címkézés/csomagolás
statisztikáit és a két kimenetet. Ha 7200 szimulációs másodperc
elteltével a forrás vagy a QC biztosan nem halad, a program
figyelmeztetéssel leáll, és a diagnosztika alapján javítható.


## Plant Simulation 2404 — `copyBitmapToFile` (2026.11.22, 20:05)

A teljes 10 000 darabos futás a 2404-es Siemensben **sikerrel befejeződött**
(élő log szerint: `SimTime=4200734.0 s`, kb. 48 nap 14 óra 52 perc),
a kész `JAXC3C.spp` 335 872 bájtos változatát a Siemens elmentette.
A hibát ezután a képexport okozta: a `Frame.copyBitmapToFile` csak
három paramétert kapott, pedig ötöt vár.

Az eltérő, dokumentált metódusok:

- Frame: `Frame.copyBitmapToFile("kimenet.png", 0, 0, 1800, 1000)`
- Chart: `Chart.copyBitmapToFile("kimenet.png", 1500, 900)`

**Legkevesebb munka, ha már megvan az eredmény:**

1. A korábbi `output` mappát (benne az SPP + JSON fájlokkal) **tartsd meg**.
2. Töltsd le az új `main` ág fájljait, és frissítsd vele a programot
   az `output` mappa törlése nélkül.
3. Indítsd az új **`EXPORT_KEPEK.bat`** fájlt (nem az `INDITAS.bat`-ot).
4. A program újranyitja az SPP-t, összeveti a mentett Siemens-statisztikákat
   a korábbi futás eredményével, és legenerálja az öt valódi PNG-t.
5. Az öt kép a `output/screenshots` mappába, a mérési PDF pedig az
   `output/Siemens_meresi_jegyzokonyv.pdf` fájlba kerül.

A képek generálásakor a régi, azonos nevű fájlok törlődnek, így az ellenőrzés
nem fogad el véletlenül egy korábbi screenshotot.

**Ha a Siemens egy elmentett `.spp` újranyitásakor nullázza a
statisztikákat:** az `EXPORT_KEPEK.bat` szándékosan hibával leáll. Ilyenkor
a teljes szimuláció újrafuttatása a megoldás, de az új `INDITAS.bat`
már a javított képexportot használja.
