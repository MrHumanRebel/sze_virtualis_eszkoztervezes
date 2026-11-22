# Egyetemi követelmények — PS beadandó.pdf (2 oldal)

A feladat: számítógép-konfigurációk összeszerelésével foglalkozó cég
minőségellenőrzési, csomagolási és szállítás-előkészítési folyamatainak
szimulációja Siemens Tecnomatix Plant Simulationben.

| PDF pont | Elvárás | Megvalósítás |
|---|---|---|
| 1 | Új modell 2D-ben | Siemens NewModel (vagy üres sablon) |
| 2 | Új mappa, 3 külön vázlat a főmodellbe illesztve | BeadandoModulok / QA, PACK, SHIP Frame |
| 3 | Ellenőrzés 3 perc | 180 s |
| 4 | 30% hibás termék | jó 70 / rossz 30 Percentage exit |
| 5 | Jó és rossz címkézés 20–20 s | 2 állomás |
| 6 | PC és csomagolóanyag előkészítés 20–20 s | 2 állomás |
| 7 | Csomagolás 10 perc, 1 termék + 1 csomagolóanyag | Assembly, 600 s, 2 előd |
| 8 | Adminisztrációk 1–1 perc | 2 × 60 s |
| 9 | Rakodó 1 5 perc, Rakodó 2 10 perc, 66/34% | 300 / 600 s, Percentage exit |
| 10 | Kiszállítás 1 perc | 60 s |
| 11 | Állomások statisztikája grafikonon | Chart |
| 12 | 10000 PC beérkezés teljes átfutási ideje | SimTime + két Drain számláló |

A minden állomás közötti szállítás 2 méteres szállítószalagon történik:
6 db QA, 6 db csomagolás, 7 db szállítás-előkészítés, 4 db főmodell = 23 db.

## A feladatban nem definiált paraméterek

- Beérkezési időköz 1 s minden forrásnál.
- Szalagsebesség 1 m/s. Egy szalag névleges utazási ideje 2 s.
- A 70/30 és 66/34 statisztikai súly; nem garantál pontos darabszámot.
- Batch lead time = az első PC beérkezésétől az utolsó jó/selejt
  feldolgozásáig eltelt teljes modellidő; nem átlagos egyedi várakozás.

## Fájlformátum

A feladat kizárólag Neptun-kód.spp leadását kéri. A repó szöveges
generátort tartalmaz, nem előre érvényesített Plant Simulation modellt.
