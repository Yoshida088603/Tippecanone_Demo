#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
DECISION="$ROOT/90_output_data/qc/crs_decision.json"
SRC_PMTILES="$ROOT/90_output_data/pmtiles/tokyo23.pmtiles"
PMTILES_FILE="tokyo23.pmtiles"
DEST_DIR="$ROOT/30_View_maplibre_on_GithubPages/data"
TEMPLATE="$ROOT/30_View_maplibre_on_GithubPages/index.template.html"
OUTPUT="$ROOT/30_View_maplibre_on_GithubPages/index.html"
META_FGB="$ROOT/90_output_data/qc/meta_fgb.json"
META_IN="$ROOT/90_output_data/qc/meta_in.json"
LOG="$ROOT/90_output_data/logs/deploy_viewer.log"

if [[ -f "$DECISION" ]]; then
  SRC_PMTILES="$ROOT/$(python3 -c "import json; print(json.load(open('$DECISION'))['output_pmtiles'])")"
  PMTILES_FILE="$(basename "$SRC_PMTILES")"
fi

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
INITIAL_ZOOM=11
TOTAL_FEATURES=0
WARD_COUNT=23
PMTILES_MAX_ZOOM=14

if [[ -f "$META_FGB" ]]; then
  read -r CENTER_LON CENTER_LAT INITIAL_ZOOM TOTAL_FEATURES PMTILES_MAX_ZOOM < <(
    python3 - "$META_FGB" "$SRC_PMTILES" <<'PY'
import json
import sys
from pathlib import Path

meta = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
pmtiles_path = Path(sys.argv[2])
center = meta.get("bbox_center", [139.78, 35.675])
extent = meta.get("extent", {})
lon_span = abs(extent.get("maxx", 139.82) - extent.get("minx", 139.74))
lat_span = abs(extent.get("maxy", 35.71) - extent.get("miny", 35.64))
span = max(lon_span, lat_span)
if span < 0.01:
    zoom = 14
elif span < 0.05:
    zoom = 13
elif span < 0.15:
    zoom = 11
else:
    zoom = 10

total_features = meta.get("feature_count", 0)
with pmtiles_path.open("rb") as fh:
    header = fh.read(127)
max_zoom = header[101] if len(header) > 101 else 14
print(center[0], center[1], zoom, total_features, max_zoom)
PY
  )
fi

if [[ -f "$META_IN" ]]; then
  WARD_COUNT="$(python3 -c "import json; print(json.load(open('$META_IN')).get('file_count', 23))")"
fi

cp "$SRC_PMTILES" "$DEST_DIR/$PMTILES_FILE"

sed -e "s/__CENTER_LON__/${CENTER_LON}/g" \
    -e "s/__CENTER_LAT__/${CENTER_LAT}/g" \
    -e "s/__INITIAL_ZOOM__/${INITIAL_ZOOM}/g" \
    -e "s/__TOTAL_FEATURES__/${TOTAL_FEATURES}/g" \
    -e "s/__WARD_COUNT__/${WARD_COUNT}/g" \
    -e "s/__PMTILES_MAX_ZOOM__/${PMTILES_MAX_ZOOM}/g" \
    -e "s/__PMTILES_FILE__/${PMTILES_FILE}/g" \
    "$TEMPLATE" > "$OUTPUT"

DOCS_DIR="$ROOT/docs"
DOCS_DATA="$DOCS_DIR/data"
mkdir -p "$DOCS_DATA"
cp "$OUTPUT" "$DOCS_DIR/index.html"
cp "$SRC_PMTILES" "$DOCS_DATA/$PMTILES_FILE"

{
  echo "=== deploy_viewer.sh $(date -u +%Y-%m-%dT%H:%M:%SZ) ==="
  echo "copied $SRC_PMTILES -> $DEST_DIR/$PMTILES_FILE"
  echo "copied viewer -> $DOCS_DIR/ (GitHub Pages)"
  echo "center=[$CENTER_LON, $CENTER_LAT] zoom=$INITIAL_ZOOM wards=$WARD_COUNT"
  echo "wrote $OUTPUT"
} | tee -a "$LOG"
