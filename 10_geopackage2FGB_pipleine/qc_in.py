#!/usr/bin/env python3
"""QC all input GPKG files in 05_input_data/."""

from __future__ import annotations

import json
import re
import sqlite3
import subprocess
import sys
from pathlib import Path

import pyogrio

ROOT = Path(__file__).resolve().parents[1]
INPUT_DIR = ROOT / "05_input_data"
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
        ["ogrinfo", "-q", "-al", "-geom=AS_XY", str(gpkg), layer],
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


def ward_code_from_name(filename: str) -> str:
    return filename.split("-")[0]


def analyze_gpkg(gpkg: Path) -> dict:
    layers = pyogrio.list_layers(gpkg)
    layer_names = [row[0] for row in layers]
    primary_layer = layer_names[0] if layer_names else None
    if not primary_layer:
        raise RuntimeError(f"no layers in {gpkg}")

    info = pyogrio.read_info(gpkg, layer=primary_layer)
    summary = run_ogrinfo_summary(gpkg, primary_layer)
    bounds = pyogrio.read_bounds(gpkg, layer=primary_layer)
    extent = summary.get("extent") or layer_extent_from_bounds(bounds)
    coord_system_attr = coord_system_counts(gpkg, primary_layer)
    samples = sample_coordinates(gpkg, primary_layer, SAMPLE_SIZE)
    coord_unit = detect_coord_unit(extent, samples)

    return {
        "input": str(gpkg.relative_to(ROOT)),
        "ward_code": ward_code_from_name(gpkg.name),
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


def merge_extents(extents: list[dict]) -> dict:
    return {
        "minx": min(e["minx"] for e in extents),
        "miny": min(e["miny"] for e in extents),
        "maxx": max(e["maxx"] for e in extents),
        "maxy": max(e["maxy"] for e in extents),
    }


def main() -> int:
    gpkg_files = sorted(INPUT_DIR.glob("*.gpkg"))
    if not gpkg_files:
        print(f"ERROR: no GPKG files in {INPUT_DIR}", file=sys.stderr)
        return 1

    files_meta = []
    for gpkg in gpkg_files:
        print(f"QC in: {gpkg.name}")
        files_meta.append(analyze_gpkg(gpkg))

    total_features = sum(int(f["feature_count"] or 0) for f in files_meta)
    meta = {
        "input_dir": str(INPUT_DIR.relative_to(ROOT)),
        "file_count": len(files_meta),
        "feature_count": total_features,
        "files": files_meta,
        "combined_extent": merge_extents([f["extent"] for f in files_meta]),
        "output_fgb": "90_output_data/fgb/tokyo23.fgb",
        "output_pmtiles": "90_output_data/pmtiles/tokyo23.pmtiles",
    }

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(meta, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {OUT}")
    print(f"files={len(files_meta)}, total_features={total_features}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
