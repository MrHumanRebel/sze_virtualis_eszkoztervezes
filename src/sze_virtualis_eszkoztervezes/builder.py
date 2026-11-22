"""Live Siemens Plant Simulation COM builder.

IMPORTANT: This module is executed only on Windows with licensed Siemens
Plant Simulation. The offline model tests do not prove live Siemens compatibility.
The tool never creates a placeholder or fake .spp binary.
"""
from __future__ import annotations

import datetime as dt
import json
import logging
from pathlib import Path
import re
import time

from .model import ASSUMPTIONS, FRAMES, MASTER, Frame, Node, validate

LOG = logging.getLogger("sze_plant")

# Class Library names differ between Siemens versions. All fallbacks are
# attempted explicitly; any unresolved object is reported as a hard failure.
CLASSES = {
    "frame": (".MaterialFlow.Frame", ".Models.Model"),
    "source": (".MaterialFlow.Source",),
    "station": (".MaterialFlow.SingleProc", ".MaterialFlow.Station"),
    "split": (".MaterialFlow.SingleProc", ".MaterialFlow.Station"),
    "assembly": (".MaterialFlow.Assembly", ".MaterialFlow.AssemblyStation"),
    "interface": (".MaterialFlow.Interface",),
    "drain": (".MaterialFlow.Drain",),
    "conveyor": (".MaterialFlow.Line", ".MaterialFlow.Conveyor"),
    "chart": ('str_to_obj(".UserInterface.Chart")',),
    "controller": (".Tools.EventController", ".MaterialFlow.EventController"),
}

def simquote(value: str) -> str:
    # JSON-escaped string literals are suitable for the fixed ASCII object
    # names used in this model. Never interpolate untrusted SimTalk statements.
    return json.dumps(value, ensure_ascii=True)

def connect_code(start: str, target: str) -> str:
    return ".MaterialFlow.Connector.connect(" + start + ", " + target + ")"

def dispatch():
    """Create an isolated Plant Simulation COM instance (never remote hosting)."""
    if __import__("os").name != "nt":
        raise RuntimeError("A Siemens COM automatizáláshoz Windows szükséges.")
    try:
        import pythoncom
        import win32com.client
    except ImportError as exc:
        raise RuntimeError("Hiányzik a pywin32. Telepítés: pip install pywin32") from exc
    pythoncom.CoInitialize()
    progids = ["Tecnomatix.PlantSimulation.RemoteControl"]
    try:
        import winreg
        with winreg.OpenKey(winreg.HKEY_CLASSES_ROOT, "") as registry:
            index = 0
            while True:
                try:
                    key = winreg.EnumKey(registry, index)
                except OSError:
                    break
                index += 1
                if key.startswith("Tecnomatix.PlantSimulation.RemoteControl."):
                    progids.append(key)
    except OSError:
        pass
    def sort_key(name: str) -> tuple[int, ...]:
        return tuple(map(int, re.findall(r"\d+", name))) or (0,)
    errors = []
    for progid in sorted(set(progids), key=sort_key, reverse=True):
        try:
            app = win32com.client.DispatchEx(progid)
            if hasattr(app, "SetNoMessageBox"):
                app.SetNoMessageBox(True)
            if hasattr(app, "SetVisible"):
                app.SetVisible(True)
            LOG.info("Plant Simulation COM kapcsolódás: %s", progid)
            return app
        except Exception as exc:
            errors.append(progid + " => " + str(exc))
    raise RuntimeError("A Plant Simulation COM nem indítható. " + "; ".join(errors))

class LiveBuilder:
    def __init__(self, app, output_dir: Path):
        self.app = app
        self.output_dir = Path(output_dir).resolve()
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.root = ""
        self.folder = ".Models.BeadandoModulok"
        self.templates: dict[str, str] = {}
        self.paths: dict[str, dict[str, str]] = {}
        self.conveyors: list[str] = []
        self.stations: list[tuple[str, int]] = []
        self.splits: list[tuple[str, tuple[int, int]]] = []
        self.event = ""

    def execute(self, code: str, description: str = ""):
        try:
            result = self.app.ExecuteSimTalk(code)
            if description:
                LOG.info("OK %s", description)
            return result
        except Exception as exc:
            LOG.error("SimTalk hiba (%s): %s\n%s", description, exc, code)
            raise RuntimeError("SimTalk hiba: " + description + " / " + code) from exc

    def get(self, expression: str):
        return self.app.GetValue(expression)

    def create_model(self, template: Path | None = None):
        if template:
            path = Path(template).resolve()
            if not path.is_file() or path.suffix.lower() != ".spp":
                raise FileNotFoundError("A Siemens SPP sablon nem található: " + str(path))
            self.app.LoadModel(str(path))
            LOG.info("Modellsablon betöltve: %s", path)
        else:
            self.app.NewModel()
            LOG.info("Új Siemens modell létrehozva")
        for name in ("Model", "Frame", "Model1"):
            path = ".Models." + name
            try:
                if self.get(path + ".Name"):
                    self.root = path
                    break
            except Exception:
                continue
        if not self.root:
            try:
                count = int(self.get(".Models.NumNodes"))
                for number in range(1, count + 1):
                    candidate = str(self.get(".Models.node(" + str(number) + ").Name"))
                    if candidate not in ("Models", "BeadandoModulok"):
                        self.root = ".Models." + candidate
                        break
            except Exception:
                pass
        if not self.root:
            raise RuntimeError(
                "Az új Frame nem elérhető COM-on keresztül. "
                "Próbálj egy üres, Plant Simulationben elmentett "
                "SPP fájlt a --template kapcsolóval."
            )
        LOG.info("Fő 2D Frame: %s", self.root)

    def create(self, kind: str, parent: str, node: Node, class_path: str = "") -> str:
        target = parent + "." + node.name
        choices = (class_path,) if class_path else CLASSES[kind]
        errors = []
        for classname in choices:
            # Some versions support the optional fourth (name) argument.
            code_named = (
                classname + ".createObject(" + parent + ", "
                + str(node.x) + ", " + str(node.y) + ", "
                + simquote(node.name) + ")"
            )
            try:
                self.execute(code_named)
                if self.get(target + ".Name") == node.name:
                    LOG.info("Objektum: %s [%s]", target, classname)
                    return target
                errors.append("A név nem olvasható vissza: " + target)
            except Exception as exc:
                errors.append(str(exc))
            # Compatibility fallback for the 3-argument createObject signature.
            code_three = (
                "var created : object; created := " + classname
                + ".createObject(" + parent + ", " + str(node.x)
                + ", " + str(node.y) + "); created.Name := "
                + simquote(node.name) + ";"
            )
            try:
                self.execute(code_three)
                if self.get(target + ".Name") == node.name:
                    LOG.info("Objektum (kompatibilitás): %s [%s]", target, classname)
                    return target
                errors.append("Névellenőrzés sikertelen: " + target)
            except Exception as exc:
                errors.append(str(exc))
        raise RuntimeError(
            "A Siemens nem tudta létrehozni: " + target
            + " (" + kind + ")\n" + "\n".join(errors)
        )

    def set_attr(self, obj: str, attribute: str, value):
        if isinstance(value, str):
            literal = simquote(value)
        elif isinstance(value, bool):
            literal = "true" if value else "false"
        else:
            literal = str(value)
        self.execute(obj + "." + attribute + " := " + literal, obj + "." + attribute)

    def create_folder(self):
        self.execute(
            'var folder : object; folder := .Models.createFolder; '
            'folder.Name := "BeadandoModulok";',
            "három Frame osztály mappája"
        )
        if str(self.get(self.folder + ".Name")) != "BeadandoModulok":
            raise RuntimeError("Az új class-library mappa nem jött létre.")

    def create_frame(self, frame: Frame, parent: str, classname: str = "") -> str:
        placeholder = Node(frame.name, "module", 100, 100)
        frame_path = self.create("frame", parent, placeholder, classname)
        self.paths[frame.name] = {}
        for node in frame.nodes:
            if node.kind == "module":
                template = self.templates[node.template]
                result = self.create("module", frame_path, node, template)
            else:
                result = self.create(node.kind, frame_path, node)
            self.paths[frame.name][node.name] = result
            if node.kind == "source":
                self.set_attr(result, "Amount", node.amount)
                self.set_attr(result, "Interval", node.interval)
            if node.kind in ("station", "assembly", "split"):
                self.set_attr(result, "ProcTime", node.seconds)
                if node.kind != "split":
                    self.stations.append((result, node.seconds))
        # Every logical edge is expanded to a physical, 2 m conveyor.
        # Preserve declaration order: it determines successor percentages.
        for edge in frame.edges:
            belt_node = Node("CV_" + edge.name, "conveyor", edge.x, edge.y)
            belt = self.create("conveyor", frame_path, belt_node)
            self.set_attr(belt, "Length", edge.length_m)
            self.set_attr(belt, "Speed", ASSUMPTIONS["conveyor_speed_m_s"])
            self.conveyors.append(belt)
            self.execute(connect_code(self.paths[frame.name][edge.source], belt),
                         "szalag be: " + belt)
            self.execute(connect_code(belt, self.paths[frame.name][edge.target]),
                         "szalag ki: " + belt)
        for node in frame.nodes:
            result = self.paths[frame.name][node.name]
            if node.kind == "split":
                self.set_attr(result, "ExitStrategy", "Percentage")
                self.execute(result + ".ExitStrategyPercentageValues := ["
                             + ",".join(map(str, node.percentages)) + "]",
                             "elágazás " + node.name)
                self.set_attr(result, "ExitStrategyBlocking", True)
                self.splits.append((result, node.percentages))
            if node.kind == "assembly":
                # Two incoming connections, one from the PC and one from the box.
                # Main MU is incoming connection #1. Box parts get consumed.
                self.set_attr(result, "AssemblyTableMode", "None")
                self.set_attr(result, "MainMU", 1)
                self.set_attr(result, "AssemblyMode", "Delete MUs")
                self.set_attr(result, "ExitingMU", "Main MU")
        return frame_path

    def build(self, template: Path | None = None):
        validate()
        self.create_model(template)
        self.create_folder()
        for frame in FRAMES[:-1]:
            self.templates[frame.name] = self.create_frame(frame, self.folder)
        # The original main Frame already exists; populate it, do not create
        # an extra nested top-level frame.
        main = MASTER
        self.paths[main.name] = {}
        for node in main.nodes:
            if node.kind == "module":
                result = self.create("module", self.root, node, self.templates[node.template])
            else:
                result = self.create(node.kind, self.root, node)
            self.paths[main.name][node.name] = result
            if node.kind == "source":
                self.set_attr(result, "Amount", node.amount)
                self.set_attr(result, "Interval", node.interval)
        for edge in main.edges:
            belt_node = Node("CV_" + edge.name, "conveyor", edge.x, edge.y)
            belt = self.create("conveyor", self.root, belt_node)
            self.set_attr(belt, "Length", edge.length_m)
            self.set_attr(belt, "Speed", ASSUMPTIONS["conveyor_speed_m_s"])
            self.conveyors.append(belt)
            self.execute(connect_code(self.paths[main.name][edge.source], belt))
            self.execute(connect_code(belt, self.paths[main.name][edge.target]))
        self.configure_controls()
        self.verify()
        LOG.info("Modell kész: 3 modul, 23×2 m szalag, 11 állomás, 2 elágazás")

    def configure_controls(self):
        try:
            if self.get(self.root + ".EventController.Name"):
                self.event = self.root + ".EventController"
        except Exception:
            self.event = self.create(
                "controller", self.root, Node("EventController", "station", 80, 45)
            )
        self.set_attr(self.event, "EndTime", ASSUMPTIONS["end_time_s"])
        self.set_attr(self.event, "StartStat", 0)
        # Chart belongs to the master Frame; includes all actual station objects.
        chart = self.create("chart", self.root,
                            Node("Allomas_Statisztika", "station", 750, 560))
        for frame_name, nodes in self.paths.items():
            if frame_name == "Model":
                continue
            frame = next(f for f in FRAMES if f.name == frame_name)
            instance = next(n for n in MASTER.nodes if n.template == frame_name)
            for node in frame.nodes:
                if node.kind in ("station", "assembly"):
                    target = self.root + "." + instance.name + "." + node.name
                    self.execute(chart + ".addObject(" + target + ")",
                                 "Chart: " + node.name)
        try:
            self.set_attr(chart, "DisplayInFrame", True)
        except Exception:
            LOG.warning("Chart láthatóság: kézzel nyisd meg a grafikon objektumot.")

    def verify(self):
        errors = []
        if len(self.conveyors) != 23:
            errors.append("Nem 23 szalag készült.")
        if len(self.stations) != 11:
            errors.append("Nem 11 feldolgozóállomás készült.")
        if len(self.splits) != 2:
            errors.append("Nem 2 százalékos irányítás készült.")
        for belt in self.conveyors:
            try:
                got = float(self.get(belt + ".Length"))
                if abs(got - 2.0) > 0.0001:
                    errors.append(belt + ": Length=" + str(got))
            except Exception as exc:
                errors.append(belt + ": hossz visszaolvasása: " + str(exc))
        for path, seconds in self.stations:
            try:
                got = self.get(path + ".ProcTime")
                if isinstance(got, (int, float)) and abs(got - seconds) > 0.0001:
                    errors.append(path + ": ProcTime=" + str(got))
            except Exception as exc:
                errors.append(path + ": idő visszaolvasása: " + str(exc))
        for path, percentage in self.splits:
            try:
                if "percentage" not in str(self.get(path + ".ExitStrategy")).lower():
                    errors.append(path + ": Percentage hiányzik")
            except Exception as exc:
                errors.append(path + ": stratégia visszaolvasása: " + str(exc))
        try:
            incoming = int(self.get(self.root + ".PC_Beerkezes_10000.Amount"))
            if incoming != 10000:
                errors.append("PC forrás: " + str(incoming))
        except Exception as exc:
            errors.append("PC forrás visszaolvasása: " + str(exc))
        audit = {
            "created_at": dt.datetime.now().isoformat(),
            "main_frame": self.root,
            "module_folder": self.folder,
            "conveyors": len(self.conveyors),
            "stations": len(self.stations),
            "percentage_splits": len(self.splits),
            "errors": errors,
            "siemens_live_verification": True
        }
        self.write_json("config_validation.json", audit)
        if errors:
            raise RuntimeError("Siemens modellverifikáció sikertelen: "
                               + "; ".join(errors[:8]))

    def write_json(self, name: str, data: dict):
        path = self.output_dir / name
        path.write_text(json.dumps(data, ensure_ascii=False,
                                   indent=2, default=str), encoding="utf-8")
        return path

    def save(self, filename: Path):
        dest = Path(filename).resolve()
        dest.parent.mkdir(parents=True, exist_ok=True)
        if dest.exists():
            backup = dest.with_suffix(".spp.previous")
            import shutil
            shutil.copy2(dest, backup)
        self.app.SaveModel(str(dest))
        if not dest.is_file() or dest.stat().st_size < 1024:
            raise RuntimeError("A Siemens nem készített érvényes méretű SPP-t.")
        LOG.info("SPP mentve: %s (%s byte)", dest, dest.stat().st_size)
        return dest

    def run(self, timeout_s: int = 900) -> dict:
        self.execute(self.event + ".reset", "szimuláció reset")
        self.execute(self.event + ".start", "szimuláció start")
        good_path = self.root + ".Kiszallitott_JO"
        bad_path = self.root + ".Minosegellenorzes.Rossz_Termekek"
        started = time.monotonic()
        good = bad = 0
        last_log = -1
        stop_reason = "timeout"
        while time.monotonic() - started < timeout_s:
            good = int(self.get(good_path + ".NumMU"))
            bad = int(self.get(bad_path + ".NumMU"))
            elapsed = int(time.monotonic() - started)
            if elapsed // 15 != last_log:
                LOG.info("Kimenet %s jó, %s selejt, összesen %s / 10000",
                         good, bad, good + bad)
                last_log = elapsed // 15
            if good + bad >= 10000:
                stop_reason = "complete"
                break
            try:
                running = bool(self.get(self.event + ".isRunning"))
                if not running and elapsed > 10:
                    stop_reason = "event_controller_stopped"
                    break
            except Exception:
                pass
            time.sleep(0.5)
        try:
            self.execute(self.event + ".stop", "szimuláció megállítása")
        except RuntimeError:
            LOG.warning("Az EventController stop nem sikerült.")
        try:
            simtime = self.get(self.event + ".SimTime")
        except Exception:
            simtime = None
        ratio = bad / (good + bad) if good + bad else None
        completed = good + bad == 10000
        report = {
            "input_pc_count": 10000,
            "good": good,
            "bad": bad,
            "processed": good + bad,
            "defect_ratio": ratio,
            "lot_lead_time_seconds": simtime,
            "lot_lead_time_hours": (
                float(simtime) / 3600 if isinstance(simtime, (int, float)) else None
            ),
            "complete": completed,
            "stop_reason": stop_reason,
            "pass_quantity_and_quality_tolerance": (
                completed and ratio is not None and abs(ratio - 0.30) <= 0.02
            ),
            "note": "Batch lead time is not per-unit mean throughput time."
        }
        self.write_json("simulation_result.json", report)
        if not report["pass_quantity_and_quality_tolerance"]:
            raise RuntimeError(
                "A 10 000 darabos Siemens-futtatás nem teljes vagy a selejtarány "
                "eltérése túl nagy. Lásd: output/simulation_result.json"
            )
        LOG.info("Teljes tétel átfutási ideje: %s másodperc", simtime)
        return report
