"""Declarative specification for GKLM_AUTM029's PC quality, packing and dispatch model."""
from __future__ import annotations
from dataclasses import dataclass, asdict

@dataclass(frozen=True)
class Node:
    name: str
    kind: str
    x: int
    y: int
    seconds: int = 0
    amount: int = 0
    interval: int = 0
    percentages: tuple[int, int] = (0, 0)
    template: str = ""

@dataclass(frozen=True)
class Edge:
    name: str
    source: str
    target: str
    x: int
    y: int
    length_m: float = 2.0

@dataclass(frozen=True)
class Frame:
    name: str
    nodes: tuple[Node, ...]
    edges: tuple[Edge, ...]

def n(name, kind, x, y, **kwargs):
    return Node(name, kind, x, y, **kwargs)

def e(name, source, target, x, y):
    return Edge(name, source, target, x, y)

QA = Frame("QA_Template", (
    n("In", "interface", 40, 260),
    n("Out", "interface", 1030, 155),
    n("Ellenorzes_3perc", "station", 250, 260, seconds=180),
    n("Jo70_Rossz30", "split", 475, 260, percentages=(70, 30)),
    n("Cimke_JO_20mp", "station", 730, 155, seconds=20),
    n("Cimke_ROSSZ_20mp", "station", 730, 370, seconds=20),
    n("Rossz_Termekek", "drain", 1030, 370),
), (
    e("Q01", "In", "Ellenorzes_3perc", 145, 260),
    e("Q02", "Ellenorzes_3perc", "Jo70_Rossz30", 365, 260),
    e("Q03_JO", "Jo70_Rossz30", "Cimke_JO_20mp", 590, 155),
    e("Q04_ROSSZ", "Jo70_Rossz30", "Cimke_ROSSZ_20mp", 590, 370),
    e("Q05", "Cimke_JO_20mp", "Out", 865, 155),
    e("Q06", "Cimke_ROSSZ_20mp", "Rossz_Termekek", 865, 370),
))

PACK = Frame("PACK_Template", (
    n("In", "interface", 35, 310),
    n("Out", "interface", 1090, 310),
    n("Csomagoloanyag_Forras", "source", 35, 100, amount=10000, interval=1),
    n("PC_Elokeszites_20mp", "station", 275, 310, seconds=20),
    n("Anyag_Elokeszites_20mp", "station", 275, 100, seconds=20),
    n("Csomagolas_10perc", "assembly", 615, 310, seconds=600),
    n("Csomagolas_Admin_1perc", "station", 875, 310, seconds=60),
), (
    e("P01", "In", "PC_Elokeszites_20mp", 145, 310),
    e("P02_PC", "PC_Elokeszites_20mp", "Csomagolas_10perc", 440, 310),
    e("P03", "Csomagoloanyag_Forras", "Anyag_Elokeszites_20mp", 145, 100),
    e("P04_ANYAG", "Anyag_Elokeszites_20mp", "Csomagolas_10perc", 440, 100),
    e("P05", "Csomagolas_10perc", "Csomagolas_Admin_1perc", 740, 310),
    e("P06", "Csomagolas_Admin_1perc", "Out", 990, 310),
))

SHIP = Frame("SHIP_Template", (
    n("In", "interface", 30, 290),
    n("Out", "interface", 1220, 290),
    n("Szallitas_Admin_1perc", "station", 250, 290, seconds=60),
    n("Rakodo_66_34", "split", 480, 290, percentages=(66, 34)),
    n("Rakodo1_5perc", "station", 770, 150, seconds=300),
    n("Rakodo2_10perc", "station", 770, 410, seconds=600),
    n("Kiszallitas_1perc", "station", 1010, 290, seconds=60),
), (
    e("S01", "In", "Szallitas_Admin_1perc", 145, 290),
    e("S02", "Szallitas_Admin_1perc", "Rakodo_66_34", 370, 290),
    e("S03_66", "Rakodo_66_34", "Rakodo1_5perc", 620, 150),
    e("S04_34", "Rakodo_66_34", "Rakodo2_10perc", 620, 410),
    e("S05", "Rakodo1_5perc", "Kiszallitas_1perc", 890, 150),
    e("S06", "Rakodo2_10perc", "Kiszallitas_1perc", 890, 410),
    e("S07", "Kiszallitas_1perc", "Out", 1120, 290),
))

MASTER = Frame("Model", (
    n("PC_Beerkezes_10000", "source", 80, 240, amount=10000, interval=1),
    n("Minosegellenorzes", "module", 390, 240, template="QA_Template"),
    n("Csomagolas", "module", 750, 240, template="PACK_Template"),
    n("Szallitas_Elokeszites", "module", 1110, 240, template="SHIP_Template"),
    n("Kiszallitott_JO", "drain", 1440, 240),
), (
    e("MAIN01", "PC_Beerkezes_10000", "Minosegellenorzes", 235, 240),
    e("MAIN02", "Minosegellenorzes", "Csomagolas", 570, 240),
    e("MAIN03", "Csomagolas", "Szallitas_Elokeszites", 930, 240),
    e("MAIN04", "Szallitas_Elokeszites", "Kiszallitott_JO", 1270, 240),
))

FRAMES = (QA, PACK, SHIP, MASTER)
ASSUMPTIONS = {
    "quantity": 10000,
    "conveyor_speed_m_s": 1,
    "arrival_interval_s": 1,
    "end_time_s": 12000000,
    "quality": "stochastic 70/30",
    "loading": "stochastic 66/34",
}

def validate() -> None:
    assert len({frame.name for frame in FRAMES}) == 4
    for frame in FRAMES:
        nodes = {node.name: node for node in frame.nodes}
        assert len(nodes) == len(frame.nodes)
        assert len({edge.name for edge in frame.edges}) == len(frame.edges)
        for edge in frame.edges:
            assert edge.source in nodes and edge.target in nodes
            assert edge.length_m == 2.0
            assert edge.source != edge.target
        for node in frame.nodes:
            if node.kind == "split":
                outgoing = [edge for edge in frame.edges if edge.source == node.name]
                assert len(outgoing) == 2 and sum(node.percentages) == 100
            if node.kind == "assembly":
                assert sum(edge.target == node.name for edge in frame.edges) == 2
            if node.kind == "station" or node.kind == "assembly":
                assert node.seconds > 0
    assert [edge.target for edge in QA.edges if edge.source == "Jo70_Rossz30"] == [
        "Cimke_JO_20mp", "Cimke_ROSSZ_20mp"
    ]
    assert [edge.target for edge in SHIP.edges if edge.source == "Rakodo_66_34"] == [
        "Rakodo1_5perc", "Rakodo2_10perc"
    ]
    assert [edge.source for edge in PACK.edges if edge.target == "Csomagolas_10perc"] == [
        "PC_Elokeszites_20mp", "Anyag_Elokeszites_20mp"
    ]
    assert sum(len(frame.edges) for frame in FRAMES) == 23
    assert sum(node.kind in ("station", "assembly") for frame in FRAMES for node in frame.nodes) == 11

def export_plan() -> dict:
    validate()
    return {"assumptions": ASSUMPTIONS,
            "frames": [asdict(frame) for frame in FRAMES],
            "conveyors": 23, "processing_stations": 11}
