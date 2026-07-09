#!/usr/bin/env python3
"""Decide CRS conversion strategy for each input GPKG."""

from __future__ import annotations

import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
META_IN = ROOT / "90_output_data" / "qc" / "meta_in.json"
OUT = ROOT / "90_output_data" / "qc" / "crs_decision.json"

ARBITRARY_LABELS = ("任意座標系",)
PUBLIC_9_LABELS = ("公共座標9系",)
SQL_WHERE = "座標系 LIKE '%公共%9%' OR 座標系 LIKE '%公共座標9系%'"


def has_arbitrary(attrs: dict[str, int]) -> bool:
    for label, count in attrs.items():
        if count <= 0:
            continue
        if any(token in label for token in ARBITRARY_LABELS):
            return True
    return False


def count_public_9(attrs: dict[str, int]) -> int:
    total = 0
    for label, count in attrs.items():
        if any(token in label for token in PUBLIC_9_LABELS) or (
            "公共" in label and "9" in label
        ):
            total += count
    return total


def count_arbitrary(attrs: dict[str, int]) -> int:
    total = 0
    for label, count in attrs.items():
        if any(token in label for token in ARBITRARY_LABELS):
            total += count
    return total


def probe_subset_extent(gpkg: Path, layer: str, sql_where: str) -> dict | None:
    with tempfile.TemporaryDirectory() as tmp:
        tmp_gpkg = Path(tmp) / "subset.gpkg"
        sql = f'SELECT * FROM "{layer}" WHERE {sql_where}'
        subprocess.run(
            ["ogr2ogr", str(tmp_gpkg), str(gpkg), "-sql", sql, "-nln", "subset"],
            check=True,
            capture_output=True,
            text=True,
        )
        result = subprocess.run(
            ["ogrinfo", "-so", str(tmp_gpkg), "subset"],
            check=True,
            capture_output=True,
            text=True,
        )
        match = re.search(
            r"Extent:\s*\(([-\d.]+),\s*([-\d.]+)\)\s*-\s*\(([-\d.]+),\s*([-\d.]+)\)",
            result.stdout,
        )
        if not match:
            return None
        return {
            "minx": float(match.group(1)),
            "miny": float(match.group(2)),
            "maxx": float(match.group(3)),
            "maxy": float(match.group(4)),
        }


def extent_looks_like_degrees(extent: dict) -> bool:
    return (
        abs(extent["minx"]) <= 180
        and abs(extent["maxx"]) <= 180
        and abs(extent["miny"]) <= 90
        and abs(extent["maxy"]) <= 90
    )


def decide_for_file(meta: dict) -> dict:
    gpkg = ROOT / meta["input"]
    coord_unit = meta.get("coord_unit")
    attrs = meta.get("coord_system_attr", {})
    feature_count = meta.get("feature_count", 0)
    primary_layer = meta.get("primary_layer")

    arbitrary_count = count_arbitrary(attrs)
    public_9_count = count_public_9(attrs)
    mixed = has_arbitrary(attrs) and public_9_count > 0
    subset_extent = None

    if mixed:
        strategy = "filter_9系_only"
        target_srs = "EPSG:4326"
        sql_where = SQL_WHERE
        expected_output_count = public_9_count
        excluded_count = feature_count - public_9_count
        subset_extent = probe_subset_extent(gpkg, primary_layer, sql_where)
        if subset_extent and extent_looks_like_degrees(subset_extent):
            source_srs = None
            rationale = (
                "Mixed coordinate systems; public 9系 subset already in degrees."
            )
        else:
            source_srs = "EPSG:6677"
            rationale = (
                "Mixed coordinate systems; extract public 9系 and reproject 6677->4326."
            )
    elif has_arbitrary(attrs) and public_9_count == 0:
        strategy = "skip_arbitrary_only"
        source_srs = None
        target_srs = "EPSG:4326"
        sql_where = None
        expected_output_count = 0
        excluded_count = feature_count
        rationale = (
            "Only arbitrary coordinates present; skip per POC (no public 9系 features)."
        )
    elif coord_unit == "degree":
        strategy = "as_declared_4326"
        source_srs = None
        target_srs = "EPSG:4326"
        sql_where = None
        expected_output_count = feature_count
        excluded_count = 0
        rationale = "Coordinates appear to be in degrees."
    else:
        strategy = "force_6677_to_4326"
        source_srs = "EPSG:6677"
        target_srs = "EPSG:4326"
        sql_where = None
        expected_output_count = feature_count
        excluded_count = 0
        rationale = "Plane rectangular metres suspected; force 6677->4326."

    return {
        "input": meta["input"],
        "ward_code": meta.get("ward_code"),
        "input_layer": primary_layer,
        "declared_crs": meta.get("declared_crs"),
        "coord_unit": coord_unit,
        "coord_system_attr": attrs,
        "strategy": strategy,
        "source_srs": source_srs,
        "target_srs": target_srs,
        "sql_where": sql_where,
        "expected_output_count": expected_output_count,
        "excluded_count": excluded_count,
        "arbitrary_count": arbitrary_count,
        "public_9_count": public_9_count,
        "subset_extent": subset_extent,
        "rationale": rationale,
        "output_layer": "parcels",
    }


def main() -> int:
    if not META_IN.exists():
        print(f"ERROR: missing {META_IN}", file=sys.stderr)
        return 1

    meta_in = json.loads(META_IN.read_text(encoding="utf-8"))
    file_decisions = [decide_for_file(f) for f in meta_in.get("files", [])]

    decision = {
        "file_count": len(file_decisions),
        "output_fgb": meta_in.get("output_fgb", "90_output_data/fgb/tokyo23.fgb"),
        "output_pmtiles": meta_in.get("output_pmtiles", "90_output_data/pmtiles/tokyo23.pmtiles"),
        "total_expected_output": sum(d["expected_output_count"] for d in file_decisions),
        "total_excluded": sum(d["excluded_count"] for d in file_decisions),
        "files": file_decisions,
    }

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(decision, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {OUT}")
    print(f"files={len(file_decisions)}, expected_output={decision['total_expected_output']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
