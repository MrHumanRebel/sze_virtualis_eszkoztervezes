# Felépítés

Az összekötő nyilak a generált Siemens modellben külön 2 méteres
Line (Conveyor) objektumokkal valósulnak meg.

~~~mermaid
flowchart LR
    P["10000 PC beérkezése"] --> Q["Minőségellenőrzés 180 s"]
    Q -- "30% rossz" --> R["Címkézés 20 s"] --> X["Selejt"]
    Q -- "70% jó" --> G["Címkézés 20 s"] --> E["PC előkészítés 20 s"]
    B["Csomagolóanyag"] --> F["Anyag előkészítés 20 s"]
    E --> A["Assembly 600 s / 1 PC + 1 doboz"]
    F --> A
    A --> C["Csomagolás utáni admin 60 s"] --> D["Szállítási admin 60 s"]
    D --> S{"66 / 34"}
    S -- "66%" --> L1["Rakodó 1: 300 s"] --> K["Kiszállítás 60 s"]
    S -- "34%" --> L2["Rakodó 2: 600 s"] --> K
~~~

A 3 külön Frame: QA_Template, PACK_Template és SHIP_Template.
Ezek a BeadandoModulok osztálykönyvtári mappában keletkeznek,
majd a fő Frame három példányt helyez el.

## Modulok
- model.py: változtathatatlan, tesztelhető modellgráf
- builder.py: Siemens COM, SimTalk, mentés, validáció, számlálók
- cli.py: Neptun-kód és Windows futtatás
- tests/: tisztán offline, Siemens nélküli szerkezeti tesztek

A GitHub CI **nem tudja lefuttatni** a Siemens licencköteles alkalmazást.
Az élő működéshez Windows + Plant Simulation szükséges.
