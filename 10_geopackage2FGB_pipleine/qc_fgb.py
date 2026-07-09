#!/usr/bin/env python3
"""QC converted FGB: feature count, EPSG:4326 bbox validation."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pyogrio

ROOT = Path(__file__).resolve().parents[1]
FGB = ROOT / "90_output_data" / "fgb" / "13102.fgb"
META_IN = ROOT / "90_output_data" / "qc" / "meta_in.json"
OUT = ROOT / "90_output_data" / "qc" / "meta_fgb.json"
LOG = ROOT / "90_output_data" / "logs" / "qc_fgb.log"

LON_MIN, LON_MAX = 139.74, 139.82
LAT_MIN, LAT_MAX = 35.64, 35.71


def layer_extent_from_bounds(bounds) -> dict:
    if isinstance(bounds, tuple) and len(bounds) == 2:
        _, arr = bounds
        return {
            "minx": float(arr[0].min()),
            "miny": float(arr[1].min()),
            "maxx": float(arr[2].max()),
            "maxy": float(arr[3].max()),
        }
    return {
        "minx": float(bounds[0]),
        "miny": float(bounds[1]),
        "maxx": float(bounds[2]),
        "maxy": float(bounds[3]),
    }


def bbox_within_chuo(extent: dict) -> tuple[bool, list[str]]:
    errors: list[str] = []
    if extent["minx"] < LON_MIN or extent["maxx"] > LON_MAX:
        errors.append(
            f"longitude out of range: [{extent['minx']}, {extent['maxx']}] "
            f"expected [{LON_MIN}, {LON_MAX}]"
        )
    if extent["miny"] < LAT_MIN or extent["maxy"] > LAT_MAX:
        errors.append(
            f"latitude out of range: [{extent['miny']}, {extent['maxy']}] "
            f"expected [{LAT_MIN}, {LAT_MAX}]"
        )
    return len(errors) == 0, errors


def main() -> int:
    if not FGB.exists():
        print(f"ERROR: FGB not found: {FGB}", file=sys.stderr)
        return 1

    info = pyogrio.read_info(FGB, layer="parcels")
    bounds = pyogrio.read_bounds(FGB, layer="parcels")
    extent = layer_extent_from_bounds(bounds)

    feature_count = int(info.get("features", 0))
    input_count = 0
    if META_IN.exists():
        input_count = json.loads(META_IN.read_text(encoding="utf-8")).get("feature_count", 0)

    bbox_center = [
        round((extent["minx"] + extent["maxx"]) / 2, 6),
        round((extent["miny"] + extent["maxy"]) / 2, 6),
    ]

    ok_extent, extent_errors = bbox_within_chuo(extent)
    passed = feature_count > 0 and ok_extent

    meta = {
        "output": str(FGB.relative_to(ROOT)),
        "layer": "parcels",
        "crs": str(info.get("crs")),
        "feature_count": feature_count,
        "input_feature_count": input_count,
        "excluded_count": max(0, input_count - feature_count),
        "extent": extent,
        "bbox_center": bbox_center,
        "bbox_valid": ok_extent,
        "bbox_expected": {
            "lon": [LON_MIN, LON_MAX],
            "lat": [LAT_MIN, LAT_MAX],
        },
        "passed": passed,
        "errors": extent_errors,
    }

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(meta, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    LOG.parent.mkdir(parents=True, exist_ok=True)
    LOG.write_text(json.dumps(meta, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(f"Wrote {OUT}")
    print(f"features={feature_count}, passed={passed}")

    if not passed:
        for err in extent_errors:
            print(f"ERROR: {err}", file=sys.stderr)
        if feature_count <= 0:
            print("ERROR: feature_count must be > 0", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
