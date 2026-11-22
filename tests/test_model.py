"""Offline invariant tests: do not claim a live Plant Simulation run."""
import pytest
from sze_virtualis_eszkoztervezes.model import (
    ASSUMPTIONS, FRAMES, QA, PACK, SHIP, MASTER, export_plan, validate
)
from sze_virtualis_eszkoztervezes.cli import valid_neptun

def test_plan():
    validate()
    assert len(FRAMES) == 4
    assert export_plan()["conveyors"] == 23
    assert export_plan()["processing_stations"] == 11

def test_every_connection_has_two_meter_belt():
    assert all(edge.length_m == 2 for frame in FRAMES for edge in frame.edges)
    assert sum(len(frame.edges) for frame in FRAMES) == 23

def test_quality_and_labeling():
    assert next(n.percentages for n in QA.nodes if n.kind == "split") == (70, 30)
    assert sorted(n.seconds for n in QA.nodes if n.kind == "station") == [20, 20, 180]
    assert [e.target for e in QA.edges if e.source == "Jo70_Rossz30"] == [
        "Cimke_JO_20mp", "Cimke_ROSSZ_20mp"
    ]

def test_two_material_assembly():
    assembly = next(n for n in PACK.nodes if n.kind == "assembly")
    assert assembly.seconds == 600
    assert [e.source for e in PACK.edges if e.target == assembly.name] == [
        "PC_Elokeszites_20mp", "Anyag_Elokeszites_20mp"
    ]
    assert sorted(n.seconds for n in PACK.nodes if n.kind == "station") == [20, 20, 60]

def test_shipping():
    assert next(n.percentages for n in SHIP.nodes if n.kind == "split") == (66, 34)
    assert sorted(n.seconds for n in SHIP.nodes if n.kind == "station") == [60, 60, 300, 600]

def test_master_and_assumptions():
    assert [n.template for n in MASTER.nodes if n.kind == "module"] == [
        "QA_Template", "PACK_Template", "SHIP_Template"
    ]
    assert next(n.amount for n in MASTER.nodes if n.kind == "source") == 10000
    assert ASSUMPTIONS["conveyor_speed_m_s"] == 1

@pytest.mark.parametrize("value,valid", [
    ("ABC123", True), ("abc123", True), ("123456", True),
    ("ABCDE", False), ("ABCDEFG", False), ("BAD_23", False)
])
def test_neptun(value, valid):
    assert valid_neptun(value) == valid

def test_simtalk_generation():
    from sze_virtualis_eszkoztervezes.builder import connect_code, simquote
    assert connect_code(".Models.Model.A", ".Models.Model.B") == (
        ".MaterialFlow.Connector.connect(.Models.Model.A, .Models.Model.B)"
    )
    assert simquote("ABC123") == '"ABC123"'
