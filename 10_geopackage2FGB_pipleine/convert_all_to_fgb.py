#!/usr/bin/env python3
"""Convert all GPKG files to a single merged FGB (EPSG:4326)."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DECISION = ROOT / "90_output_data" / "qc" / "crs_decision.json"
PARTS_DIR = ROOT / "90_output_data" / "fgb" / "parts"
LOG = ROOT / "90_output_data" / "logs" / "convert.log"


def run_cmd(cmd: list[str]) -> None:
    subprocess.run(cmd, check=True)


def convert_one(file_decision: dict, part_fgb: Path) -> None:
    gpkg = ROOT / file_decision["input"]
    layer = file_decision["input_layer"]
    strategy = file_decision["strategy"]
    source_srs = file_decision.get("source_srs")
    target_srs = file_decision["target_srs"]
    sql_where = file_decision.get("sql_where")

    part_fgb.parent.mkdir(parents=True, exist_ok=True)
    if part_fgb.exists():
        part_fgb.unlink()

    if strategy == "filter_9系_only":
        sql = f'SELECT * FROM "{layer}" WHERE {sql_where}'
        cmd = ["ogr2ogr", "-f", "FlatGeobuf", str(part_fgb), str(gpkg), "-sql", sql]
        if source_srs:
            cmd += ["-s_srs", source_srs]
        cmd += ["-t_srs", target_srs, "-nln", "parcels"]
    elif strategy == "force_6677_to_4326":
        cmd = [
            "ogr2ogr", "-f", "FlatGeobuf", str(part_fgb), str(gpkg), layer,
            "-s_srs", source_srs, "-t_srs", target_srs, "-nln", "parcels",
        ]
    else:
        cmd = ["ogr2ogr", "-f", "FlatGeobuf", str(part_fgb), str(gpkg), layer, "-t_srs", target_srs, "-nln", "parcels"]

    print(f"CMD: {' '.join(cmd)}")
    run_cmd(cmd)


def merge_parts(part_files: list[Path], merged_fgb: Path) -> None:
    if not part_files:
        raise RuntimeError("no part FGB files to merge")

    merged_fgb.parent.mkdir(parents=True, exist_ok=True)
    if merged_fgb.exists():
        merged_fgb.unlink()

    run_cmd(["ogr2ogr", "-f", "FlatGeobuf", str(merged_fgb), str(part_files[0]), "-nln", "parcels"])
    for part in part_files[1:]:
        run_cmd([
            "ogr2ogr", "-f", "FlatGeobuf", "-update", "-append",
            str(merged_fgb), str(part), "-nln", "parcels",
        ])


def main() -> int:
    if not DECISION.exists():
        print(f"ERROR: missing {DECISION}", file=sys.stderr)
        return 1

    decision = json.loads(DECISION.read_text(encoding="utf-8"))
    merged_fgb = ROOT / decision["output_fgb"]
    part_files: list[Path] = []

    LOG.parent.mkdir(parents=True, exist_ok=True)
    with LOG.open("a", encoding="utf-8") as log:
        log.write("=== convert_all_to_fgb.py ===\n")

        for file_decision in decision.get("files", []):
            ward = file_decision.get("ward_code") or Path(file_decision["input"]).stem
            expected = file_decision.get("expected_output_count", 0)
            if expected <= 0 or file_decision.get("strategy") == "skip_arbitrary_only":
                log.write(f"skip {file_decision['input']} (no public 9系 features)\n")
                print(f"Skipping {file_decision['input']} (expected_output=0)")
                continue
            part_fgb = PARTS_DIR / f"{ward}.fgb"
            log.write(f"convert {file_decision['input']} -> {part_fgb}\n")
            print(f"Converting {file_decision['input']} ...")
            convert_one(file_decision, part_fgb)
            part_files.append(part_fgb)

        log.write(f"merge {len(part_files)} parts -> {merged_fgb}\n")
        print(f"Merging {len(part_files)} parts into {merged_fgb} ...")
        merge_parts(part_files, merged_fgb)
        log.write(f"OK: {merged_fgb}\n")

    print(f"OK: {merged_fgb}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
