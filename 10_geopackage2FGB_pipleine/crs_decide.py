#!/usr/bin/env python3
"""Decide CRS conversion strategy from QC input metadata."""

from __future__ import annotations

import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GPKG = ROOT / "05_input_data" / "13102-0100-2026.gpkg"
META_IN = ROOT / "90_output_data" / "qc" / "meta_in.json"
OUT = ROOT / "90_output_data" / "qc" / "crs_decision.json"

ARBITRARY_LABELS = ("任意座標系",)
PUBLIC_9_LABELS = ("公共座標9系",)


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


def probe_subset_extent(layer: str, sql_where: str) -> dict | None:
    """Measure extent of a filtered subset via temporary GPKG."""
    with tempfile.TemporaryDirectory() as tmp:
        tmp_gpkg = Path(tmp) / "subset.gpkg"
        sql = f'SELECT * FROM "{layer}" WHERE {sql_where}'
        subprocess.run(
            [
                "ogr2ogr",
                str(tmp_gpkg),
                str(GPKG),
                "-sql",
                sql,
                "-nln",
                "subset",
            ],
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


def main() -> int:
    if not META_IN.exists():
        print(f"ERROR: missing {META_IN}", file=sys.stderr)
        return 1

    meta = json.loads(META_IN.read_text(encoding="utf-8"))
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
        sql_where = "座標系 LIKE '%公共%9%' OR 座標系 LIKE '%公共座標9系%'"
        expected_output_count = public_9_count
        excluded_count = feature_count - public_9_count

        subset_extent = probe_subset_extent(primary_layer, sql_where)
        if subset_extent and extent_looks_like_degrees(subset_extent):
            source_srs = None
            rationale = (
                "Mixed coordinate systems detected; public 9系 subset is already "
                "in degree coordinates — extract and keep EPSG:4326 without forced "
                "plane-rectangular reprojection."
            )
        else:
            source_srs = "EPSG:6677"
            rationale = (
                "Mixed coordinate systems detected; extract public plane-rectangular "
                "(9系) features and reproject EPSG:6677 -> EPSG:4326."
            )
    elif coord_unit == "degree":
        strategy = "as_declared_4326"
        source_srs = None
        target_srs = "EPSG:4326"
        sql_where = None
        expected_output_count = feature_count
        excluded_count = 0
        rationale = "Coordinates appear to be in degrees; trust declared EPSG:4326."
    else:
        strategy = "force_6677_to_4326"
        source_srs = "EPSG:6677"
        target_srs = "EPSG:4326"
        sql_where = None
        expected_output_count = feature_count
        excluded_count = 0
        rationale = (
            "Extent/coordinates look like plane rectangular metres despite "
            "declared EPSG:4326; force EPSG:6677 -> EPSG:4326."
        )

    decision = {
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

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(decision, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {OUT}")
    print(f"strategy={strategy}, source_srs={source_srs}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
