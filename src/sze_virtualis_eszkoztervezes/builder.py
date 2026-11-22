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
    # Observed in the user's genuine Plant Simulation 2404 COM log.
    "station": (".MaterialFlow.Station", ".MaterialFlow.SingleProc"),
    "split": (".MaterialFlow.Station", ".MaterialFlow.SingleProc"),
    "assembly": (".MaterialFlow.AssemblyStation", ".MaterialFlow.Assembly"),
    "interface": (".MaterialFlow.Interface",),
    "drain": (".MaterialFlow.Drain",),
    "conveyor": (".MaterialFlow.Conveyor", ".MaterialFlow.Line"),
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
        self.assembly_table_attribute = ""
        self.event_end_attribute = ""

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

    def configure_assembly(self, obj: str) -> None:
        """Set one main MU + one part without relying on a single PS version.

        The Plant Simulation 2404 COM log rejects AssemblyTableMode. Older
        Plant Simulation versions expose the same selection as PartListMode.
        Both names must be validated by Siemens read-back, not just a mock.
        """
        errors = []
        for attr in ("PartListMode", "AssemblyTableMode"):
            try:
                self.set_attr(obj, attr, "None")
                actual = str(self.get(obj + "." + attr)).strip()
                if actual.casefold() != "none":
                    raise RuntimeError("unexpected read-back: " + repr(actual))
                self.assembly_table_attribute = attr
                LOG.info("Assembly table mode: %s.None (read-back OK)", attr)
                break
            except Exception as exc:
                errors.append(attr + ": " + str(exc))
        else:
            raise RuntimeError(
                "Az AssemblyStation None/1:1 módját nem sikerült beállítani "
                "a Plant Simulation verzióban: " + " | ".join(errors)
            )
        # Connection 1 supplies the PC, connection 2 the packaging material.
        self.set_attr(obj, "MainMU", 1)
        self.set_attr(obj, "AssemblyMode", "Delete MUs")
        self.set_attr(obj, "ExitingMU", "Main MU")

    def configure_source(self, obj: str, node: Node):
        """Source quantity is Number, NOT the GUI-labelled Amount (2404)."""
        self.set_attr(obj, "TimeOfGeneration", "Interval Adjustable")
        self.set_attr(obj, "Start", 0)
        self.set_attr(obj, "Stop", 0)
        self.set_attr(obj, "Interval", node.interval)
        self.set_attr(obj, "Number", node.amount)
        LOG.info("Forras: %s / %s darab / %s mp", obj, node.amount, node.interval)

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
                self.configure_source(result, node)
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
                self.configure_assembly(result)
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
                self.configure_source(result, node)
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

    def configure_event_end(self, duration_s: int) -> None:
        """Set the end-of-run limit with version-specific SimTalk attributes.

        Plant Simulation 2404 exposes EventController.End. Later versions
        describe EndTime. A successful COM write MUST be read back.
        """
        errors = []
        for attr in ("End", "EndTime"):
            try:
                self.set_attr(self.event, attr, duration_s)
                actual = self.get(self.event + "." + attr)
                if abs(float(actual) - duration_s) > 0.0001:
                    raise RuntimeError(
                        "End-time read-back mismatch: " + repr(actual)
                    )
                self.event_end_attribute = attr
                LOG.info("EventController.%s = %s s (read-back OK)",
                         attr, duration_s)
                return
            except Exception as exc:
                errors.append(attr + ": " + str(exc))
        raise RuntimeError(
            "Nem lehet beállítani a Plant Simulation végidejét: "
            + " | ".join(errors)
        )

    def configure_controls(self):
        try:
            if self.get(self.root + ".EventController.Name"):
                self.event = self.root + ".EventController"
        except Exception:
            self.event = self.create(
                "controller", self.root, Node("EventController", "station", 80, 45)
            )
        self.configure_event_end(ASSUMPTIONS["end_time_s"])
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
        if not self.event_end_attribute:
            errors.append("EventController end-time attribute not selected")
        else:
            try:
                stop_time = float(self.get(self.event + "." + self.event_end_attribute))
                if abs(stop_time - ASSUMPTIONS["end_time_s"]) > 0.0001:
                    errors.append("EventController stop time mismatch: " + str(stop_time))
            except Exception as exc:
                errors.append("EventController end-time read-back: " + str(exc))
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
                predecessor_count = int(self.get(belt + ".NumPred"))
                successor_count = int(self.get(belt + ".NumSucc"))
                if predecessor_count != 1 or successor_count != 1:
                    errors.append(belt + ": NumPred=" + str(predecessor_count)
                                  + " NumSucc=" + str(successor_count)
                                  + " (expected 1/1)")
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
                if int(self.get(path + ".NumSucc")) != 2:
                    errors.append(path + ": expected exactly 2 exits")
                if "percentage" not in str(self.get(path + ".ExitStrategy")).lower():
                    errors.append(path + ": Percentage hiányzik")
            except Exception as exc:
                errors.append(path + ": stratégia visszaolvasása: " + str(exc))
        assembly_path = self.folder + ".PACK_Template.Csomagolas_10perc"
        try:
            if int(self.get(assembly_path + ".NumPred")) != 2:
                errors.append(assembly_path + ": 2 inputs required")
            if not self.assembly_table_attribute:
                errors.append(assembly_path + ": assembly table mode unknown")
            elif str(self.get(assembly_path + "." + self.assembly_table_attribute)).strip().casefold() != "none":
                errors.append(assembly_path + ": assembly table mode is not None")
            for attr, expected in (("MainMU", 1),
                                   ("AssemblyMode", "Delete MUs"),
                                   ("ExitingMU", "Main MU")):
                actual = self.get(assembly_path + "." + attr)
                matches = (int(actual) == expected if isinstance(expected, int)
                           else str(actual).strip().casefold() == str(expected).casefold())
                if not matches:
                    errors.append(assembly_path + "." + attr + ": " + str(actual)
                                  + " (expected " + str(expected) + ")")
        except Exception as exc:
            errors.append(assembly_path + ": assembly readback failed: " + str(exc))
        try:
            for source in (
                self.root + ".PC_Beerkezes_10000",
                self.folder + ".PACK_Template.Csomagoloanyag_Forras",
            ):
                incoming = int(self.get(source + ".Number"))
                if incoming != 10000:
                    errors.append(source + ": Number=" + str(incoming))
                mode = str(self.get(source + ".TimeOfGeneration")).lower()
                if "interval" not in mode:
                    errors.append(source + ": Interval Adjustable hiányzik")
        except Exception as exc:
            errors.append("PC forrás visszaolvasása: " + str(exc))
        audit = {
            "created_at": dt.datetime.now().isoformat(),
            "main_frame": self.root,
            "module_folder": self.folder,
            "conveyors": len(self.conveyors),
            "stations": len(self.stations),
            "percentage_splits": len(self.splits),
            "assembly_mode_attribute": self.assembly_table_attribute,
            "event_end_attribute": self.event_end_attribute,
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

    def progress_snapshot(self) -> dict:
        """Read a few real Siemens counters to distinguish progress from blockage.

        This diagnostic does not change the simulation or claim completion.
        Missing statistics are explicitly recorded as null, not invented as 0.
        """
        def optional(path: str):
            try:
                return self.get(path)
            except Exception as exc:
                LOG.debug("Progress probe unavailable %s: %s", path, exc)
                return None

        return {
            "sim_time_seconds": optional(self.event + ".SimTime"),
            "controller_running": optional(self.event + ".IsRunning"),
            "source_output": optional(self.root + ".PC_Beerkezes_10000.StatNumOut"),
            "qa_processed": optional(
                self.root + ".Minosegellenorzes.Ellenorzes_3perc.StatNumOut"
            ),
            "good_labels": optional(
                self.root + ".Minosegellenorzes.Cimke_JO_20mp.StatNumOut"
            ),
            "defective_drain": optional(
                self.root + ".Minosegellenorzes.Rossz_Termekek.StatDeleted"
            ),
            "packaged": optional(
                self.root + ".Csomagolas.Csomagolas_10perc.StatNumOut"
            ),
            "delivered": optional(self.root + ".Kiszallitott_JO.StatDeleted"),
        }

    def run(self, timeout_s: int = 900) -> dict:
        self.execute(self.event + ".reset", "szimuláció reset")
        # Explicit Siemens API: start(WithAnimation=false, RealTime=false).
        # Without this, 4.2 million simulated seconds would take days in
        # real-time mode; the first QA decision alone takes 180 seconds.
        self.execute(self.event + ".start(false,false)",
                     "szimuláció maximum sebességgel, animáció nélkül")
        good_path = self.root + ".Kiszallitott_JO"
        bad_path = self.root + ".Minosegellenorzes.Rossz_Termekek"
        started = time.monotonic()
        good = bad = 0
        last_log = -1
        stop_reason = "timeout"
        while time.monotonic() - started < timeout_s:
            good = int(self.get(good_path + ".StatDeleted"))
            bad = int(self.get(bad_path + ".StatDeleted"))
            elapsed = int(time.monotonic() - started)
            if elapsed // 15 != last_log:
                snapshot = self.progress_snapshot()
                snapshot.update({
                    "wall_time_elapsed_seconds": elapsed,
                    "good_at_drain": good,
                    "bad_at_drain": bad,
                    "processed_total": good + bad,
                })
                self.write_json("progress.json", snapshot)
                LOG.info(
                    "Szimuláció t=%s s; forrás=%s; QC=%s; címkézett jó=%s; "
                    "csomagolt=%s; kimenet=%s jó + %s selejt / 10000",
                    snapshot["sim_time_seconds"], snapshot["source_output"],
                    snapshot["qa_processed"], snapshot["good_labels"],
                    snapshot["packaged"], good, bad
                )
                # First outgoing defective products take >200 simulated
                # seconds. No output at t=117 s is NOT a deadlock.
                # At >7200 simulated seconds there must have been progress.
                simtime = snapshot["sim_time_seconds"]
                src_count = snapshot["source_output"]
                qa_count = snapshot["qa_processed"]
                if (
                    good + bad == 0 and isinstance(simtime, (int, float))
                    and simtime >= 7200
                ):
                    self.execute(self.event + ".stop", "elakadás miatt leállítás")
                    stage = (
                        "forrás" if src_count == 0 else
                        "minőségellenőrzés" if qa_count == 0 else
                        "részmodellek közötti anyagáram / további állomások"
                    )
                    raise RuntimeError(
                        "Anyagáram-elakadás gyanúja: 7200 szimulációs másodperc "
                        "után még nincs kész vagy selejt kimenet. "
                        "Utoljára ellenőrizendő: " + stage
                        + ". Részletes számlálók: output/progress.json"
                    )
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
        try:
            packed = int(self.get(self.root + ".Csomagolas.Csomagolas_10perc.StatNumOut"))
            loader1 = int(self.get(self.root + ".Szallitas_Elokeszites.Rakodo1_5perc.StatNumOut"))
            loader2 = int(self.get(self.root + ".Szallitas_Elokeszites.Rakodo2_10perc.StatNumOut"))
        except Exception as exc:
            LOG.error("Állomás-kimeneti statisztika nem olvasható: %s", exc)
            packed = loader1 = loader2 = None
        actual_loader_share = (loader1 / (loader1 + loader2)
                               if loader1 is not None and loader2 is not None
                               and loader1 + loader2 else None)
        completed = good + bad == 10000
        lot_time_valid = (isinstance(simtime, (int, float))
                          and packed is not None and simtime >= packed * 600)
        try:
            created_input = int(self.get(self.root + ".PC_Beerkezes_10000.StatNumOut"))
        except Exception:
            created_input = None
        report = {
            "input_pc_count": 10000,
            "good": good,
            "bad": bad,
            "processed": good + bad,
            "source_output_count": created_input,
            "packed": packed,
            "loaded_at_station_1": loader1,
            "loaded_at_station_2": loader2,
            "station_1_actual_share": actual_loader_share,
            "theoretical_minimum_pack_time_seconds": (
                packed * 600 if packed is not None else None),
            "lot_time_at_least_pack_time": lot_time_valid,
            "defect_ratio": ratio,
            "lot_lead_time_seconds": simtime,
            "lot_lead_time_hours": (
                float(simtime) / 3600 if isinstance(simtime, (int, float)) else None
            ),
            "complete": completed,
            "stop_reason": stop_reason,
            "pass_quantity_and_quality_tolerance": (
                completed and created_input == 10000 and ratio is not None
                and abs(ratio - 0.30) <= 0.02
                and packed == good and loader1 is not None and loader2 is not None
                and loader1 + loader2 == good
                and actual_loader_share is not None
                and abs(actual_loader_share - 0.66) <= 0.03
                and lot_time_valid
            ),
            "note": "Batch lead time is not per-unit mean throughput time."
        }
        self.write_json("simulation_result.json", report)
        if not report["pass_quantity_and_quality_tolerance"]:
            raise RuntimeError(
                "Szimulációs ellenőrzés sikertelen: input, kimenet, csomagolás, "
                "rakodóelosztás vagy átfutási idő eltérése. "
                "Részletek: output/simulation_result.json"
            )
        LOG.info("Teljes tétel átfutási ideje: %s másodperc", simtime)
        return report
