#!/usr/bin/env python3
"""QC input GPKG: layer metadata, extent, coordinate unit detection."""

from __future__ import annotations

import json
import re
import sqlite3
import subprocess
import sys
from pathlib import Path

import pyogrio

ROOT = Path(__file__).resolve().parents[1]
GPKG = ROOT / "05_input_data" / "13102-0100-2026.gpkg"
OUT = ROOT / "90_output_data" / "qc" / "meta_in.json"

SAMPLE_SIZE = 100


def run_ogrinfo_summary(gpkg: Path, layer: str) -> dict:
    result = subprocess.run(
        ["ogrinfo", "-so", str(gpkg), layer],
        capture_output=True,
        text=True,
        check=True,
    )
    text = result.stdout
    extent_match = re.search(
        r"Extent:\s*\(([-\d.]+),\s*([-\d.]+)\)\s*-\s*\(([-\d.]+),\s*([-\d.]+)\)",
        text,
    )
    extent = None
    if extent_match:
        extent = {
            "minx": float(extent_match.group(1)),
            "miny": float(extent_match.group(2)),
            "maxx": float(extent_match.group(3)),
            "maxy": float(extent_match.group(4)),
        }

    crs_match = re.search(r'ID\["EPSG",(\d+)\]', text)
    declared_crs = f"EPSG:{crs_match.group(1)}" if crs_match else None

    count_match = re.search(r"Feature Count:\s*(\d+)", text)
    feature_count = int(count_match.group(1)) if count_match else None

    return {
        "declared_crs": declared_crs,
        "extent": extent,
        "feature_count": feature_count,
        "geometry_type": "Multi Polygon" if "Multi Polygon" in text else "Unknown",
    }


def coord_system_counts(gpkg: Path, layer: str) -> dict[str, int]:
    conn = sqlite3.connect(gpkg)
    try:
        rows = conn.execute(
            f'SELECT "座標系", COUNT(*) FROM "{layer}" GROUP BY "座標系"'
        ).fetchall()
    finally:
        conn.close()
    return {row[0] or "(null)": row[1] for row in rows}


def sample_coordinates(gpkg: Path, layer: str, limit: int) -> list[tuple[float, float]]:
    result = subprocess.run(
        [
            "ogrinfo",
            "-q",
            "-al",
            "-geom=AS_XY",
            str(gpkg),
            layer,
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    coords: list[tuple[float, float]] = []
    for line in result.stdout.splitlines():
        line = line.strip()
        if re.match(r"^[-\d.]+\s+[-\d.]+$", line):
            parts = line.split()
            if len(parts) >= 2:
                coords.append((float(parts[0]), float(parts[1])))
                if len(coords) >= limit:
                    break
    return coords


def layer_extent_from_bounds(bounds) -> dict:
    """Compute layer-wide extent from pyogrio.read_bounds() output."""
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


def detect_coord_unit(extent: dict | None, samples: list[tuple[float, float]]) -> str:
    points = list(samples)
    if extent:
        for x, y in [
            (extent["minx"], extent["miny"]),
            (extent["maxx"], extent["maxy"]),
        ]:
            points.append((x, y))

    if not points:
        return "metre_suspect"

    degree_like = sum(1 for x, y in points if abs(x) <= 180 and abs(y) <= 90)
    if degree_like >= len(points) * 0.8:
        return "degree"
    return "metre_suspect"


def main() -> int:
    if not GPKG.exists():
        print(f"ERROR: input not found: {GPKG}", file=sys.stderr)
        return 1

    layers = pyogrio.list_layers(GPKG)
    layer_names = [row[0] for row in layers]
    primary_layer = layer_names[0] if layer_names else None

    if not primary_layer:
        print("ERROR: no layers found in GPKG", file=sys.stderr)
        return 1

    info = pyogrio.read_info(GPKG, layer=primary_layer)
    summary = run_ogrinfo_summary(GPKG, primary_layer)
    bounds = pyogrio.read_bounds(GPKG, layer=primary_layer)
    extent = summary.get("extent") or layer_extent_from_bounds(bounds)
    coord_system_attr = coord_system_counts(GPKG, primary_layer)
    samples = sample_coordinates(GPKG, primary_layer, SAMPLE_SIZE)
    coord_unit = detect_coord_unit(extent, samples)

    meta = {
        "input": str(GPKG.relative_to(ROOT)),
        "layers": layer_names,
        "primary_layer": primary_layer,
        "feature_count": summary["feature_count"] or info.get("features"),
        "declared_crs": summary["declared_crs"] or str(info.get("crs")),
        "geometry_type": summary["geometry_type"],
        "extent": extent,
        "coord_unit": coord_unit,
        "coord_system_attr": coord_system_attr,
        "sample_coord_count": len(samples),
    }

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(meta, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {OUT}")
    print(f"coord_unit={coord_unit}, features={meta['feature_count']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
