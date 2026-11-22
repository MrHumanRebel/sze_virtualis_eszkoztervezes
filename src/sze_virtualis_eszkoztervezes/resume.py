"""Re-open an already simulated Siemens .spp for evidence export without rerunning.

This explicitly cross-checks the saved Plant Simulation counters with the
recorded result. If Plant Simulation did not persist the state, it fails
rather than attaching an old report to an unrelated model.
"""
from __future__ import annotations

import json
from pathlib import Path


def verify_saved_run(builder, spp_path: Path) -> None:
    output = builder.output_dir.resolve()
    result_file = output / "simulation_result.json"
    validation_file = output / "config_validation.json"
    if not result_file.is_file() or not validation_file.is_file():
        raise RuntimeError(
            "Nem talalhato a korabbi sikeres futas eredmenye. "
            "Az INDITAS.bat teljes futtatasa szukseges."
        )
    report = json.loads(result_file.read_text(encoding="utf-8"))
    validation = json.loads(validation_file.read_text(encoding="utf-8"))
    if not (
        report.get("complete") is True
        and report.get("processed") == 10000
        and report.get("pass_quantity_and_quality_tolerance") is True
        and validation.get("siemens_live_verification") is True
        and not validation.get("errors")
    ):
        raise RuntimeError("A korabbi futtatas eredmenye nem igazolt.")

    root = builder.root
    comparisons = (
        ("jo termek", root + ".Kiszallitott_JO.StatDeleted", "good"),
        ("selejt", root + ".Minosegellenorzes.Rossz_Termekek.StatDeleted", "bad"),
        ("bemenet", root + ".PC_Beerkezes_10000.StatNumOut", "source_output_count"),
        ("csomagolas", root + ".Csomagolas.Csomagolas_10perc.StatNumOut", "packed"),
        ("rakodo 1", root + ".Szallitas_Elokeszites.Rakodo1_5perc.StatNumOut",
         "loaded_at_station_1"),
        ("rakodo 2", root + ".Szallitas_Elokeszites.Rakodo2_10perc.StatNumOut",
         "loaded_at_station_2"),
    )
    for label, expression, field in comparisons:
        try:
            actual = int(builder.get(expression))
        except Exception as exc:
            raise RuntimeError(
                "A betoltott SPP nem tartalmaz kiolvashato "
                + label + " statisztikat; teljes ujrafuttatas szukseges."
            ) from exc
        expected = report.get(field)
        if actual != expected:
            raise RuntimeError(
                "A betoltott SPP es a mentett meres elter: "
                + label + " (" + str(actual) + " != " + str(expected) + "). "
                "A kepek nem hitelesithetoek ujrafuttatas nelkul."
            )
    try:
        actual_time = float(builder.get(root + ".EventController.SimTime"))
        expected_time = float(report["lot_lead_time_seconds"])
    except Exception as exc:
        raise RuntimeError("A mentett szimulacios ido nem olvashato.") from exc
    if abs(actual_time - expected_time) > 0.01:
        raise RuntimeError(
            "A mentett SPP idobelyege nem egyezik a meressel: "
            + str(actual_time) + " != " + str(expected_time)
        )
