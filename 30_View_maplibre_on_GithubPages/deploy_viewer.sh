#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SRC_PMTILES="$ROOT/90_output_data/pmtiles/13102.pmtiles"
DEST_DIR="$ROOT/30_View_maplibre_on_GithubPages/data"
TEMPLATE="$ROOT/30_View_maplibre_on_GithubPages/index.template.html"
OUTPUT="$ROOT/30_View_maplibre_on_GithubPages/index.html"
META_FGB="$ROOT/90_output_data/qc/meta_fgb.json"
LOG="$ROOT/90_output_data/logs/deploy_viewer.log"

mkdir -p "$DEST_DIR"

if [[ ! -f "$SRC_PMTILES" ]]; then
  echo "ERROR: PMTiles not found: $SRC_PMTILES" >&2
  exit 1
fi

if [[ ! -f "$TEMPLATE" ]]; then
  echo "ERROR: template not found: $TEMPLATE" >&2
  exit 1
fi

CENTER_LON=139.78
CENTER_LAT=35.675
INITIAL_ZOOM=13

if [[ -f "$META_FGB" ]]; then
  read -r CENTER_LON CENTER_LAT INITIAL_ZOOM < <(
    python3 - "$META_FGB" <<'PY'
import json
import sys
from pathlib import Path

meta = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
center = meta.get("bbox_center", [139.78, 35.675])
extent = meta.get("extent", {})
lon_span = abs(extent.get("maxx", 139.82) - extent.get("minx", 139.74))
lat_span = abs(extent.get("maxy", 35.71) - extent.get("miny", 35.64))
span = max(lon_span, lat_span)
if span < 0.01:
    zoom = 14
elif span < 0.05:
    zoom = 13
else:
    zoom = 12
print(center[0], center[1], zoom)
PY
  )
fi

cp "$SRC_PMTILES" "$DEST_DIR/13102.pmtiles"

sed -e "s/__CENTER_LON__/${CENTER_LON}/g" \
    -e "s/__CENTER_LAT__/${CENTER_LAT}/g" \
    -e "s/__INITIAL_ZOOM__/${INITIAL_ZOOM}/g" \
    "$TEMPLATE" > "$OUTPUT"

{
  echo "=== deploy_viewer.sh $(date -u +%Y-%m-%dT%H:%M:%SZ) ==="
  echo "copied $SRC_PMTILES -> $DEST_DIR/13102.pmtiles"
  echo "center=[$CENTER_LON, $CENTER_LAT] zoom=$INITIAL_ZOOM"
  echo "wrote $OUTPUT"
} | tee -a "$LOG"
