"""CLI for the real Windows model builder and the platform-neutral model plan."""
from __future__ import annotations
import argparse
import json
import logging
import os
from pathlib import Path
import re
import sys
import traceback

from .model import export_plan, validate

def valid_neptun(value: str) -> bool:
    return bool(re.fullmatch(r"[A-Z0-9]{6}", value.strip().upper()))

def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        description="SzE Plant Simulation — 2D PC beadandó automatizált modellépítő"
    )
    parser.add_argument("--plan", action="store_true",
                        help="Offline szerkezeti terv JSON-ként, Siemens nélkül")
    parser.add_argument("--neptun", help="Saját, 6 karakteres Neptun-kód")
    parser.add_argument("--build-only", action="store_true",
                        help="Ne indítsa a 10000 darabos futást")
    parser.add_argument("--template", type=Path,
                        help="Régebbi verziónál használható üres .spp sablon")
    parser.add_argument("--output-dir", type=Path, default=Path("output"))
    parser.add_argument("--timeout", type=int, default=900,
                        help="Maximális valós futási idő másodpercben (alap: 900)")
    args = parser.parse_args(argv)
    validate()
    if args.plan:
        print(json.dumps(export_plan(), indent=2, ensure_ascii=False))
        return 0
    if os.name != "nt":
        parser.error("Valódi .spp generálásához Windows + Siemens Plant Simulation kell.")
    neptun = (args.neptun or input("Neptun-kód (6 karakter): ")).strip().upper()
    if not valid_neptun(neptun):
        parser.error("Pontosan 6 betűt/számot adj meg (pl. ABC123).")
    if args.timeout < 1:
        parser.error("A --timeout értéke legyen pozitív.")
    out = args.output_dir.resolve()
    out.mkdir(parents=True, exist_ok=True)
    log_path = out / "run.log"
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(message)s",
        handlers=[logging.StreamHandler(sys.stdout),
                  logging.FileHandler(log_path, encoding="utf-8")],
    )
    log = logging.getLogger("sze_plant")
    try:
        from .builder import LiveBuilder, dispatch
        ps = dispatch()
        builder = LiveBuilder(ps, out)
        builder.build(args.template)
        dest = out / (neptun + ".spp")
        builder.save(dest)
        if args.build_only:
            log.warning("Csak építés; a 10 000 PC-s eredmény NINCS igazolva.")
        else:
            builder.run(args.timeout)
            builder.save(dest)
            from .evidence import capture
            manifest = capture(builder, dest)
            log.info("Valódi Siemens képek: %s", len(manifest["screenshots"]))
            from .result_report import generate
            pdf_path = generate(out)
            log.info("Eredményjegyzőkönyv: %s", pdf_path)
        log.info("Fájl: %s", dest)
        return 0
    except Exception:
        log.error("Sikertelen generálás / validáció:\n%s", traceback.format_exc())
        log.error("A részlegesen előállított SPP nem tekinthető beadásra késznek.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
