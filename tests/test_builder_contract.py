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
