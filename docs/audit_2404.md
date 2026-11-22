# Modell- és beadásellenőrzés · Plant Simulation 2404

**A cél az eredeti feladatlap 12 pontjának teljesítése.** Az egyetemi kiírásból nem következik, hogy külön jelentést kell beadni: a **Neptun-kód.spp** az előírt leadási fájl.

## Követelmények

| # | Elvárás | Modellbeállítás | Ellenőrzés |
|---|---|---|---|
| 1 | Új 2D modell | Új fő-Frame, `.Models.Model` | Programból létrehozva; Siemensben vizuálisan ellenőrizendő |
| 2 | 3 külön részmodell saját mappában | `BeadandoModulok`, QA/PACK/SHIP, majd példányosítás | Modellgráf és objektumlétrehozási teszt |
| 3 | Ellenőrzés 3 perc | 180 s | `ProcTime` visszaolvasás |
| 4 | 30% rossz termék | 70/30 véletlen elágazás | 2 kimenet; mért selejtarány 28–32% |
| 5 | Jó és rossz címkézés 20 s | 20–20 s | 2 külön állomás |
| 6 | PC és csomagolóanyag előkészítése 20 s | 20–20 s | 2 külön bemenet |
| 7 | Csomagolás 10 perc, 1 PC + 1 csomagolóanyag | Assembly 600 s, 2 bemenet, `MainMU=1`, `Delete MUs` | 2 előd; kimenet egyezzen a kész PC-k számával |
| 8 | Csomagolási és szállítási adminisztráció | 60–60 s | 2 külön állomás |
| 9 | Rakodó 1/2: 5 és 10 perc, 66/34 | 300/600 s; kétágú százalékos irányítás | Mért rakodómegoszlás 63–69% / 31–37% |
| 10 | Kiszállítás 1 perc | 60 s | Külön állomás |
| 11 | Állomásstatisztika grafikonon | `Allomas_Statisztika` | 11 állomás felvétele; valódi screenshot szükséges |
| 12 | 10 000 PC teljes átfutási ideje | Source `Number=10000`; 2 Drain `StatDeleted` | Az összes jó + rossz kimenet = 10 000; mért `SimTime` |

**Minden állomásközi szállítás 2 méteres**: 23 külön `Line`, minden szalag ellenőrzött hosszal és pontosan egy be-/kimeneti kapcsolattal.

## Amit az egyetemi PDF nem ad meg

A beérkezési időköz és a szalag sebessége nincs előírva. Választott értékeim: 1 PC/s és 1 m/s. A sztochasztikus százalékos elágazások miatt az egyes futások jó/selejt és rakodó darabszámai eltérnek.

## Ésszerűségi kontroll

Az egyetlen csomagolóállomás munkadarabonként 600 másodpercet dolgozik. Ha megközelítőleg 7000 jó PC-t csomagolunk, akkor **csak ez az állomás legalább 4 200 000 másodpercet (kb. 48,6 napot)** igényel. Ez *elméleti alsó korlát*, nem a Siemensben mért átfutási idő. A valós futásnál a mérés ennél nem lehet rövidebb.

## Mi van igazolva, és mi nincs?

- **Igazolt:** az eredeti PDF bájtra azonos feltöltése; Python CI; a 12 követelmény paraméterezése; a 23 szalag, 46 kapcsolat, 11 állomás és a negatív tesztesetek.
- **Részben igazolt a felhasználó képe alapján:** Plant Simulation 2404 elindul, COM-vezérléssel új modellt és osztálykönyvtári mappát hoz létre. A korábban hibás Source-attribútum javítva.
- **Még nem igazolt:** a teljes 10 000 darabos futás valódi 2404 alatt, a végleges NEPTUNKOD.spp megnyitása és öt eredeti Siemens-screenshot. Az offline CI nem helyettesíti ezeket.

## Siemens oldali záró ellenőrzés

1. A legfrissebb `main` ágon futtasd az `INDITAS.bat` fájlt **Windows + Plant Simulation 2404** alatt.
2. Az `output/run.log` hibamentes, `config_validation.json` szerint nincs szerkezeti hiba.
3. A `simulation_result.json` szerint 10 000 input és output, ellenőrzött csomagolás, két rakodó és valós szimulációs idő.
4. Készüljön el `output/NEPTUNKOD.spp`, az öt `output/screenshots` PNG, és a mért PDF-jegyzőkönyv.
5. Nyisd meg **újra** a `.spp`-t Siemensben. Ellenőrizd az állomások elhelyezkedését, a százalékos ágakat, a Chartot és az átfutási időt.
6. Ha mindez rendben van, a Git-klónból futtatható a `tools/publish_results.ps1`. A tanulmányi rendszerbe a kiírás szerinti **egyetlen .spp fájl** kell.

A hiányzó valós Siemens-futást nem jelölöm sikeresnek.
