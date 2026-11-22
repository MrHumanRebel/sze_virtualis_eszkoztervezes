"""Export only genuine screenshots rendered by a live Siemens Plant Simulation."""
from datetime import datetime, timezone
from pathlib import Path
import hashlib
import json
import logging

LOG=logging.getLogger("sze_plant")

def sha256(path: Path) -> str:
    h=hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024*1024),b""):
            h.update(chunk)
    return h.hexdigest()

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
    for filename,obj,width,height in sources:
        output=(screenshots/filename).resolve()
        args = (
            [json.dumps(str(output), ensure_ascii=True), str(width), str(height)]
            if filename == "05_allomasstatisztika.png"
            else [json.dumps(str(output), ensure_ascii=True), "0", "0",
                  str(width), str(height)]
        )
        cmd = obj + ".copyBitmapToFile(" + ",".join(args) + ")"
        try:
            builder.execute(cmd,"Siemens screenshot: "+filename)
            if not output.is_file() or output.stat().st_size<1000:
                raise RuntimeError("A fájl hiányzik vagy üres.")
            if output.read_bytes()[:8]!=b"\x89PNG\r\n\x1a\n":
                raise RuntimeError("Nem valódi PNG.")
        except Exception as exc:
            output.unlink(missing_ok=True)
            raise RuntimeError("Nem sikerült az eredeti Siemens-képernyőkép: "+filename) from exc
        images[filename]={"sha256":sha256(output),"bytes":output.stat().st_size,"source":obj}
        LOG.info("Rögzített valódi screenshot: %s",output)
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
