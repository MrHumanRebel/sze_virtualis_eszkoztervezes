"""Forensic, file-level check of the uploaded GKLM_AUTM029 Siemens submission.

Run on the checked-out GitHub repository. It checks what is objectively
verifiable *without* the proprietary Plant Simulation executable:
- original brief, OLE/CFB .spp structure, SHA-256 chain of custody;
- model/measurement arithmetic and simulation output invariants;
- screenshot PNG validity, real dimensions and pixel diversity;
- embedded evidence in the three-page results PDF.
It cannot establish that a proprietary .spp opens/runs correctly; that
requires Plant Simulation 2404 on Windows.
"""
from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import re
import struct
import sys

from PIL import Image, ImageStat, ImageChops
from pypdf import PdfReader
import olefile

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "output"
DOC = ROOT / "docs" / "assignment" / "PS_beadando_original.pdf"
BRIEF_SHA = "167c81993741f6a333a08109e595cc12b98ed03aa1973d562886030f0aed06f1"
PNG_NAMES = [
    "01_fomodell.png",
    "02_minosegellenorzes.png",
    "03_csomagolas.png",
    "04_szallitas_elokeszites.png",
    "05_allomasstatisztika.png",
]
PDF = OUT / "Siemens_meresi_jegyzokonyv.pdf"
STATEMENTS = [
    ("01", "2D, külön részmodellek", "A három Frame és a főmodell a tervben szerepel"),
    ("02", "Három vázlat egy mappában", "BeadandoModulok / QA / PACK / SHIP"),
    ("03", "Minőségellenőrzés", "180 másodperc"),
    ("04", "Selejtarány", "30%"),
    ("05", "Két címkézés", "20–20 másodperc"),
    ("06", "Két előkészítés", "20–20 másodperc"),
    ("07", "1:1 csomagolás", "600 másodperc / két bemenet"),
    ("08", "Két adminisztráció", "60–60 másodperc"),
    ("09", "Két rakodó", "300/600 s, 66/34%"),
    ("10", "Kiszállítás", "60 másodperc"),
    ("11", "Statisztika grafikon", "Siemens Chart + PNG + PDF"),
    ("12", "10000 PC átfutása", "Mért szimulációs idő és darabszámok"),
]
checks = []
warnings = []
measurements = {}

def check(label: str, condition: bool, detail: str = "") -> None:
    checks.append({"label": label, "ok": bool(condition), "detail": detail})
    print(("PASS" if condition else "FAIL") + " | " + label
          + (": " + detail if detail else ""))

def warning(message: str):
    warnings.append(message)
    print("NOTE | " + message)

def h(file: Path) -> str:
    return sha256(file.read_bytes()).hexdigest()

def load(file: Path):
    return json.loads(file.read_text(encoding="utf-8"))

def png_metrics(path: Path, expected_width: int, expected_height: int) -> dict:
    with path.open("rb") as stream:
        signature = stream.read(24)
    check(path.name + ": PNG signature", signature[:8] == b"\x89PNG\r\n\x1a\n")
    width, height = struct.unpack(">II", signature[16:24])
    check(path.name + ": felbontás", (width, height) == (expected_width, expected_height),
          str(width) + "×" + str(height))
    with Image.open(path) as image:
        image.verify()
    with Image.open(path) as image:
        im = image.convert("RGB")
        # Identical to what reviewers would see in an ordinary PNG viewer.
        pixels = im.resize((200, 125), resample=Image.Resampling.BILINEAR)
        values = list(pixels.getdata())
        colors = len(set(values))
        most = Counter(values).most_common(1)[0][1] / len(values)
        stat = ImageStat.Stat(pixels)
        variations = [round(x, 2) for x in stat.stddev]
        # Detect non-empty visual content without requiring artificial contrast.
        nonblank = colors > 8 and max(variations) > 5
        check(path.name + ": nem üres kép", nonblank,
              f"{colors} különböző mintaszín, szórás {variations}")
        if most >= 0.98:
            warning(path.name + " nagyon kevés részletet tartalmaz; vizuális szemle szükséges")
        return {"width": width, "height": height, "pixel_colors_sample": colors,
                "dominant_color_share": round(most, 5),
                "channel_stddev": variations, "appears_nonblank": nonblank}

def inspect_spp(path: Path) -> dict:
    size = path.stat().st_size
    sig = path.read_bytes()[:8]
    ole_sig = bytes.fromhex("d0cf11e0a1b11ae1")
    check("SPP nem üres", size >= 100_000, f"{size:,} bájt")
    check("SPP: OLE Compound File fejléc", sig == ole_sig, sig.hex())
    names = []
    if sig == ole_sig:
        try:
            with olefile.OleFileIO(str(path)) as doc:
                names = ["/".join(parts) for parts in doc.listdir()]
            check("SPP: OLE struktúra olvasható", bool(names),
                  f"{len(names)} stream/storage bejegyzés")
        except Exception as exc:
            check("SPP: OLE struktúra olvasható", False, str(exc))
    return {"bytes": size, "sha256": h(path),
            "ole_magic": sig == ole_sig, "ole_entries": names[:35]}

def main() -> int:
    check("Eredeti 2 oldalas feladatlap elérhető", DOC.is_file())
    if DOC.is_file():
        check("Eredeti PDF SHA256 változatlan", h(DOC) == BRIEF_SHA, h(DOC))
        reader = PdfReader(str(DOC))
        check("Eredeti PDF: 2 oldal", len(reader.pages) == 2)
        text = "\n".join(page.extract_text() or "" for page in reader.pages)
        check("Feladat szövegében 10 000 számítógép és SPP követelmény",
              bool(re.search(r"10\s?000", text)) and ".spp" in text.lower())
    paths = [
        OUT / "simulation_result.json",
        OUT / "config_validation.json",
        OUT / "evidence_manifest.json",
        PDF,
    ]
    for path in paths:
        check("Kötelező fájl " + path.name, path.is_file())
    if any(not path.is_file() for path in paths):
        return finish()

    result = load(paths[0])
    cfg = load(paths[1])
    manifest = load(paths[2])
    model_name = manifest.get("model", "")
    spp = OUT / model_name
    check("Neptun-kód az SPP fájlnév", bool(re.fullmatch(r"[A-Z0-9]{6}\.spp", model_name)),
          model_name)
    check("Beadandó SPP létezik", spp.is_file())
    if not spp.is_file():
        return finish()
    measurements["spp"] = inspect_spp(spp)
    check("Manifest és tényleges SPP SHA256 egyezik",
          h(spp) == manifest.get("spp_sha256"), h(spp))
    check("Nincs modellgenerálási ellenőrzési hiba",
          cfg.get("siemens_live_verification") is True and cfg.get("errors") == [])
    check("Három Frame + 23 szalag + 11 állomás + két elágazás",
          cfg.get("conveyors") == 23 and cfg.get("stations") == 11
          and cfg.get("percentage_splits") == 2)
    check("Plant Simulation 2404 Assembly/End kompatibilitás",
          cfg.get("assembly_mode_attribute") == "PartListMode"
          and cfg.get("event_end_attribute") == "End")
    good = result.get("good")
    bad = result.get("bad")
    source = result.get("source_output_count")
    packed = result.get("packed")
    l1 = result.get("loaded_at_station_1")
    l2 = result.get("loaded_at_station_2")
    duration = result.get("lot_lead_time_seconds")
    check("10000 bemenet, 10000 teljes kimenet",
          source == 10000 and good + bad == result.get("processed") == 10000)
    check("30% hibás: 3000 / 10000",
          bad == 3000 and result.get("defect_ratio") == 0.3)
    check("Csomagolás: jó darabszám egyezik",
          packed == good == l1 + l2, f"{packed} = {good} = {l1}+{l2}")
    check("66/34 rakodóelosztás",
          (l1, l2) == (4620, 2380) and abs(l1 / good - 0.66) < 1e-10)
    check("Átfutás legalább a 600 s × csomagolt darabszám",
          duration >= 600 * packed,
          f"{duration:,.0f} s >= {600*packed:,} s")
    check("A jelentés szerint a futás befejeződött",
          result.get("complete") is True
          and result.get("stop_reason") == "complete"
          and result.get("pass_quantity_and_quality_tolerance") is True)
    check("Manifest darabszámai/ideje egyeznek",
          manifest.get("processed") == result["processed"]
          and manifest.get("good") == good and manifest.get("bad") == bad
          and manifest.get("lot_lead_time_seconds") == duration)
    check("Képek nem szintetikusnak jelöltek",
          manifest.get("source") == "Siemens Plant Simulation copyBitmapToFile"
          and manifest.get("synthetic_images") is False)
    measurements["result"] = result

    images = manifest.get("screenshots", {})
    check("Pontosan az 5 elvárt képernyőkép", set(images) == set(PNG_NAMES))
    metrics = {}
    for name in PNG_NAMES:
        path = OUT / "screenshots" / name
        check("PNG fájl elérhető: " + name, path.is_file())
        if not path.is_file():
            continue
        check("PNG SHA256: " + name, h(path) == images.get(name, {}).get("sha256"))
        check("PNG méret manifest: " + name,
              path.stat().st_size == images.get(name, {}).get("bytes"))
        metrics[name] = png_metrics(path, 1800 if name == PNG_NAMES[0] else 1500,
                                    1000 if name == PNG_NAMES[0] else 900)
    measurements["screenshots"] = metrics

    pdf = PdfReader(str(PDF))
    check("Mérési jegyzőkönyv: 3 oldal", len(pdf.pages) == 3)
    full_text = "\n".join(p.extract_text() or "" for p in pdf.pages)
    check("Mérési PDF tartalmazza az SPP fájlnevet",
          model_name in full_text)
    check("Mérési PDF tartalmazza a teljes SimTime-ot",
          str(duration) in full_text, str(duration))
    check("Mérési PDF tartalmazza a jó/selejt darabszámokat",
          str(good) in full_text and str(bad) in full_text)
    images_in_pdf = []
    for i, page in enumerate(pdf.pages, 1):
        try:
            images_in_pdf.append(len(page.images))
        except Exception as exc:
            warning(f"PDF {i}. oldal: beágyazott képek nem olvashatók: {exc}")
            images_in_pdf.append(None)
    check("Mérési PDF-ben legalább 5 beágyazott Siemens-kép",
          all(v is not None for v in images_in_pdf)
          and sum(images_in_pdf) >= 5, str(images_in_pdf))
    measurements["pdf"] = {"pages": len(pdf.pages), "image_counts": images_in_pdf,
                           "text_preview": full_text[:1000]}
    if (OUT / (model_name + ".previous")).exists():
        warning("A korábbi *.spp.previous biztonsági mentés fent van a nyilvános repóban; "
                "a beadandó egyetlen végleges SPP legyen.")
    warning("A köztes progress.json futás közben egymás után kiolvasott, nem atomi minta; "
            "nem helyettesíti a végső simulation_result.json állományt.")
    warning("A Plant Simulation nélküli fájlaudit nem bizonyítja, hogy az SPP "
            "újranyitáskor is hibamentesen működik. Ezt Windows + PS2404 alatt "
            "külön ellenőrizni kell.")
    return finish()

def finish() -> int:
    failures = [row for row in checks if not row["ok"]]
    summary = {
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "passed": len(checks) - len(failures),
        "failed": len(failures),
        "checks": checks,
        "notes": warnings,
        "measurements": measurements,
        "siemens_reopen_verified": False,
    }
    destination = ROOT / "output_audit.json"
    destination.write_text(json.dumps(summary, indent=2, ensure_ascii=False),
                           encoding="utf-8")
    md = ["# Feltöltött Siemens-beadandó — fájlaudit",
          "", f"**{summary['passed']} sikeres / {summary['failed']} sikertelen ellenőrzés**",
          "", "| Vizsgálat | Eredmény |", "|---|---|"]
    for item in checks:
        md.append("| " + item["label"].replace("|", "/") + " | "
                  + ("OK" if item["ok"] else "**HIBA**") + " |")
    md.extend(["", "## Megjegyzések"])
    md.extend("- " + note for note in warnings)
    md.extend(["", "A valódi Windowsos Siemens újranyitási teszt külön szükséges."])
    (ROOT / "output_audit.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    print(f"\nAUDIT RESULT: {summary['passed']} PASS; {summary['failed']} FAIL.")
    return int(bool(failures))

if __name__ == "__main__":
    sys.exit(main())
