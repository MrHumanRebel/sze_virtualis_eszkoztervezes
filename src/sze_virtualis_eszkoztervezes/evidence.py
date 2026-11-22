"""Export only genuine screenshots rendered by a live Siemens Plant Simulation."""
from datetime import datetime, timezone
from pathlib import Path
import hashlib
import json
import logging
import time

LOG=logging.getLogger("sze_plant")

def sha256(path: Path) -> str:
    h=hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024*1024),b""):
            h.update(chunk)
    return h.hexdigest()

def export_png(builder, obj: str, output: Path, width: int,
               height: int, *, chart: bool = False) -> str:
    """Write a genuine Plant Simulation PNG, verifying the output on disk.

    On Plant Simulation 2404, successful COM execution does not guarantee
    that copyBitmapToFile actually created a picture. The Siemens examples
    omit .png, and Windows paths should use forward slashes in SimTalk.
    """
    output = Path(output).resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    if output.suffix.lower() != ".png":
        raise ValueError("Only PNG output is supported.")
    failures = []
    for target in (output.with_suffix(""), output):
        possible = list(dict.fromkeys((
            target, Path(str(target) + ".png"), output,
            Path(str(output) + ".png")
        )))
        for candidate in possible:
            candidate.unlink(missing_ok=True)
        filename = json.dumps(str(target).replace("\\", "/"),
                              ensure_ascii=True)
        args = ([filename, str(width), str(height)] if chart else
                [filename, "0", "0", str(width), str(height)])
        cmd = obj + ".copyBitmapToFile(" + ",".join(args) + ")"
        try:
            result = builder.execute(cmd, "Siemens PNG: " + output.name)
        except Exception as exc:
            failures.append(cmd + " -> " + str(exc))
            continue
        for _ in range(8):
            for candidate in possible:
                if not candidate.is_file() or candidate.stat().st_size < 1000:
                    continue
                with candidate.open("rb") as f:
                    signature = f.read(8)
                if signature != b"\x89PNG\r\n\x1a\n":
                    continue
                if candidate != output:
                    candidate.replace(output)
                LOG.info("Siemens PNG elkészült: %s (%s byte)",
                         output, output.stat().st_size)
                return cmd
            time.sleep(0.1)
        failures.append(
            "A SimTalk lefutott, de nincs PNG. return=" + repr(result)
            + "; command=" + cmd + "; paths=" + ", ".join(map(str, possible))
        )
    raise RuntimeError("A Siemens nem írt ki PNG fájlt. " + " | ".join(failures))


def capture(builder, spp_path: Path) -> dict:
    out=builder.output_dir.resolve()
    result_path=out/"simulation_result.json"
    validation_path=out/"config_validation.json"
    if not result_path.is_file() or not validation_path.is_file():
        raise RuntimeError("Nincs teljes élő Siemens-futtatási jelentés.")
    result=json.loads(result_path.read_text(encoding="utf-8"))
    validation=json.loads(validation_path.read_text(encoding="utf-8"))
    if not (result.get("complete") and
            result.get("pass_quantity_and_quality_tolerance") and
            result.get("processed")==10000 and
            validation.get("siemens_live_verification") and
            not validation.get("errors")):
        raise RuntimeError("Nem igazolt a 10000 darabos Plant Simulation futtatás.")
    spp_path=Path(spp_path).resolve()
    if not spp_path.is_file() or spp_path.stat().st_size<1024:
        raise RuntimeError("Nincs ellenőrzött SPP fájl.")
    screenshots=out/"screenshots"
    screenshots.mkdir(parents=True,exist_ok=True)
    sources=[
        ("01_fomodell.png", builder.root, 1800, 1000),
        ("02_minosegellenorzes.png", builder.root+".Minosegellenorzes", 1500, 900),
        ("03_csomagolas.png", builder.root+".Csomagolas", 1500, 900),
        ("04_szallitas_elokeszites.png", builder.root+".Szallitas_Elokeszites", 1500, 900),
        ("05_allomasstatisztika.png", builder.root+".Allomas_Statisztika", 1500, 900),
    ]
    images={}
    for filename, obj, width, height in sources:
        output = (screenshots / filename).resolve()
        try:
            cmd = export_png(builder, obj, output, width, height,
                             chart=filename == "05_allomasstatisztika.png")
        except Exception as exc:
            raise RuntimeError(
                "Nem sikerült az eredeti Siemens-képernyőkép: " + filename
            ) from exc
        images[filename] = {
            "sha256": sha256(output),
            "bytes": output.stat().st_size,
            "source": obj,
            "command": cmd,
        }
        LOG.info("Valódi Siemens-kép: %s", output)
    manifest={
        "created_utc":datetime.now(timezone.utc).isoformat(),
        "source":"Siemens Plant Simulation copyBitmapToFile",
        "synthetic_images":False,
        "model":spp_path.name,
        "spp_sha256":sha256(spp_path),
        "processed":result["processed"],
        "good":result["good"],
        "bad":result["bad"],
        "lot_lead_time_seconds":result["lot_lead_time_seconds"],
        "screenshots":images,
    }
    (out/"evidence_manifest.json").write_text(
        json.dumps(manifest,indent=2,ensure_ascii=False),encoding="utf-8"
    )
    return manifest
