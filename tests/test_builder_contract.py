"""Offline COM contract smoke test. This is a simulator mock, NOT real Siemens."""
from __future__ import annotations
import re
from pathlib import Path

from sze_virtualis_eszkoztervezes.builder import LiveBuilder


class FakePlantSimulation:
    def __init__(self):
        self.objects = {}
        self.connections = []
        self.chart_sources = []

    def NewModel(self):
        self.objects[".Models.Model"] = {"Name": "Model"}

    def GetValue(self, expression: str):
        match = re.fullmatch(r"(.+)\.(\w+)", expression)
        if not match:
            raise KeyError(expression)
        parent, key = match.groups()
        if key == "NumPred":
            return sum(dst == parent for src, dst in self.connections)
        if key == "NumSucc":
            return sum(src == parent for src, dst in self.connections)
        return self.objects[parent][key]

    def ExecuteSimTalk(self, code: str):
        if ".Models.createFolder" in code:
            self.objects[".Models.BeadandoModulok"] = {"Name": "BeadandoModulok"}
            return

        create = re.search(
            r"\.createObject\(([^,]+),\s*(-?\d+),\s*(-?\d+),\s*\"([A-Za-z0-9_]+)\"\)",
            code,
        )
        if create:
            parent, _x, _y, name = create.groups()
            assert parent in self.objects, f"Parent does not exist: {parent}"
            dest = parent + "." + name
            assert dest not in self.objects, f"Duplicate object: {dest}"
            self.objects[dest] = {"Name": name}
            if parent == ".Models.Model" and code.startswith(".Models.BeadandoModulok."):
                # Simulate an instance of a prebuilt class Frame.
                classname = code.split(".createObject(", 1)[0]
                for old_path, attrs in list(self.objects.items()):
                    if old_path.startswith(classname + "."):
                        self.objects[dest + old_path[len(classname):]] = dict(attrs)
            return

        link = re.fullmatch(
            r"\.MaterialFlow\.Connector\.connect\(([^,]+),\s*([^\)]+)\)", code
        )
        if link:
            src, dst = link.groups()
            assert src in self.objects, src
            assert dst in self.objects, dst
            self.connections.append((src, dst))
            return

        assignment = re.fullmatch(r"([^\s;]+)\.(\w+)\s*:=\s*(.+)", code)
        if assignment:
            path, key, value = assignment.groups()
            assert path in self.objects, f"Unknown object: {path}"
            if key == "Amount":
                raise AssertionError("Plant Simulation 2404: Source.Amount is not a valid attribute")
            raw = value.rstrip(";")
            if raw.startswith('"') and raw.endswith('"'):
                parsed = raw[1:-1]
            elif raw == "true":
                parsed = True
            elif raw == "false":
                parsed = False
            else:
                try:
                    parsed = float(raw)
                except ValueError:
                    parsed = raw
            self.objects[path][key] = parsed
            return

        chart = re.fullmatch(r"([^\s]+)\.addObject\(([^\)]+)\)", code)
        if chart:
            obj, target = chart.groups()
            assert obj in self.objects, obj
            assert target in self.objects, target
            self.chart_sources.append(target)
            return

        if code.endswith((".reset", ".start", ".stop")):
            return
        raise AssertionError("Unexpected SimTalk statement: " + code)


def test_full_model_builds_on_fake_com(tmp_path: Path):
    fake = FakePlantSimulation()
    builder = LiveBuilder(fake, tmp_path)
    builder.build()
    assert builder.root == ".Models.Model"
    assert len(builder.templates) == 3
    assert len(builder.conveyors) == 23
    assert len(builder.stations) == 11
    assert len(builder.splits) == 2
    assert len(fake.connections) == 46
    assert len(fake.chart_sources) == 11
    assert all(fake.objects[path]["Length"] == 2.0 for path in builder.conveyors)
    assert fake.objects[".Models.BeadandoModulok.QA_Template.Jo70_Rossz30"][
        "ExitStrategyPercentageValues"
    ] == "[70,30]"
    assert fake.objects[".Models.BeadandoModulok.SHIP_Template.Rakodo_66_34"][
        "ExitStrategyPercentageValues"
    ] == "[66,34]"
    assert fake.objects[".Models.BeadandoModulok.PACK_Template.Csomagolas_10perc"][
        "AssemblyMode"
    ] == "Delete MUs"
    assert (tmp_path / "config_validation.json").is_file()
    for belt in builder.conveyors:
        assert fake.GetValue(belt + ".NumPred") == 1
        assert fake.GetValue(belt + ".NumSucc") == 1
    for source in (
        ".Models.Model.PC_Beerkezes_10000",
        ".Models.BeadandoModulok.PACK_Template.Csomagoloanyag_Forras",
    ):
        assert fake.objects[source]["Number"] == 10000
        assert fake.objects[source]["TimeOfGeneration"] == "Interval Adjustable"
        assert fake.objects[source]["Stop"] == 0
        assert fake.objects[source]["Interval"] == 1


def test_lot_uses_cumulative_drain_deleted_statistic(tmp_path: Path):
    fake = FakePlantSimulation()
    builder = LiveBuilder(fake, tmp_path)
    builder.build()
    good = ".Models.Model.Kiszallitott_JO"
    bad = ".Models.Model.Minosegellenorzes.Rossz_Termekek"
    fake.objects[good]["NumMU"] = 0
    fake.objects[bad]["NumMU"] = 0
    fake.objects[good]["StatDeleted"] = 7010
    fake.objects[bad]["StatDeleted"] = 2990
    fake.objects[builder.event]["SimTime"] = 4212000
    fake.objects[".Models.Model.PC_Beerkezes_10000"]["StatNumOut"] = 10000
    fake.objects[".Models.Model.Csomagolas.Csomagolas_10perc"]["StatNumOut"] = 7010
    fake.objects[".Models.Model.Szallitas_Elokeszites.Rakodo1_5perc"]["StatNumOut"] = 4627
    fake.objects[".Models.Model.Szallitas_Elokeszites.Rakodo2_10perc"]["StatNumOut"] = 2383
    result = builder.run(timeout_s=2)
    assert result["processed"] == 10000
    assert result["good"] == 7010 and result["bad"] == 2990
    assert result["complete"] is True
    assert result["lot_lead_time_seconds"] == 4212000


def test_unconnected_line_fails_strict_validation(tmp_path: Path):
    import pytest
    fake = FakePlantSimulation()
    builder = LiveBuilder(fake, tmp_path)
    builder.build()
    fake.connections.pop()
    with pytest.raises(RuntimeError, match="NumSucc"):
        builder.verify()


def test_assembly_requires_both_predecessors(tmp_path: Path):
    import pytest
    fake = FakePlantSimulation()
    builder = LiveBuilder(fake, tmp_path)
    builder.build()
    assembly = ".Models.BeadandoModulok.PACK_Template.Csomagolas_10perc"
    fake.connections = [(a, b) for a, b in fake.connections
                        if not (b == assembly and a.endswith("CV_P04_ANYAG"))]
    with pytest.raises(RuntimeError, match="2 inputs"):
        builder.verify()


def test_wrong_assembly_mode_is_rejected(tmp_path: Path):
    import pytest
    fake = FakePlantSimulation()
    builder = LiveBuilder(fake, tmp_path)
    builder.build()
    assembly = ".Models.BeadandoModulok.PACK_Template.Csomagolas_10perc"
    fake.objects[assembly]["AssemblyMode"] = "Attach MUs"
    with pytest.raises(RuntimeError, match="AssemblyMode"):
        builder.verify()


def test_all_drains_complete_but_source_short_fails(tmp_path: Path):
    import pytest
    fake = FakePlantSimulation()
    builder = LiveBuilder(fake, tmp_path)
    builder.build()
    fake.objects[".Models.Model.Kiszallitott_JO"]["StatDeleted"] = 7000
    fake.objects[".Models.Model.Minosegellenorzes.Rossz_Termekek"]["StatDeleted"] = 3000
    fake.objects[".Models.Model.PC_Beerkezes_10000"]["StatNumOut"] = 9999
    fake.objects[builder.event]["SimTime"] = 4230000
    with pytest.raises(RuntimeError, match="ellenőrzés"):
        builder.run(timeout_s=0.1)


def test_unrealistic_simulation_time_is_rejected(tmp_path: Path):
    import pytest
    fake = FakePlantSimulation()
    builder = LiveBuilder(fake, tmp_path)
    builder.build()
    fake.objects[".Models.Model.Kiszallitott_JO"]["StatDeleted"] = 7000
    fake.objects[".Models.Model.Minosegellenorzes.Rossz_Termekek"]["StatDeleted"] = 3000
    fake.objects[".Models.Model.PC_Beerkezes_10000"]["StatNumOut"] = 10000
    fake.objects[".Models.Model.Csomagolas.Csomagolas_10perc"]["StatNumOut"] = 7000
    fake.objects[".Models.Model.Szallitas_Elokeszites.Rakodo1_5perc"]["StatNumOut"] = 4620
    fake.objects[".Models.Model.Szallitas_Elokeszites.Rakodo2_10perc"]["StatNumOut"] = 2380
    fake.objects[builder.event]["SimTime"] = 1000  # 7000 * 600 s impossible
    with pytest.raises(RuntimeError, match="ellenőrzés"):
        builder.run(timeout_s=0.1)


def test_loader_counters_are_checked(tmp_path: Path):
    import pytest
    fake = FakePlantSimulation()
    builder = LiveBuilder(fake, tmp_path)
    builder.build()
    fake.objects[".Models.Model.Kiszallitott_JO"]["StatDeleted"] = 7000
    fake.objects[".Models.Model.Minosegellenorzes.Rossz_Termekek"]["StatDeleted"] = 3000
    fake.objects[".Models.Model.PC_Beerkezes_10000"]["StatNumOut"] = 10000
    fake.objects[".Models.Model.Csomagolas.Csomagolas_10perc"]["StatNumOut"] = 7000
    fake.objects[".Models.Model.Szallitas_Elokeszites.Rakodo1_5perc"]["StatNumOut"] = 6000
    fake.objects[".Models.Model.Szallitas_Elokeszites.Rakodo2_10perc"]["StatNumOut"] = 1000
    fake.objects[builder.event]["SimTime"] = 4300000
    with pytest.raises(RuntimeError, match="ellenőrzés"):
        builder.run(timeout_s=0.1)
