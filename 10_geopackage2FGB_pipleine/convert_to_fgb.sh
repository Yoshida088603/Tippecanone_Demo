#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
GPKG="$ROOT/05_input_data/13102-0100-2026.gpkg"
DECISION="$ROOT/90_output_data/qc/crs_decision.json"
OUT_FGB="$ROOT/90_output_data/fgb/13102.fgb"
LOG="$ROOT/90_output_data/logs/convert.log"

mkdir -p "$(dirname "$OUT_FGB")" "$(dirname "$LOG")"

if [[ ! -f "$DECISION" ]]; then
  echo "ERROR: missing crs_decision.json" >&2
  exit 1
fi

LAYER=$(python3 -c "import json; print(json.load(open('$DECISION'))['input_layer'])")
STRATEGY=$(python3 -c "import json; print(json.load(open('$DECISION'))['strategy'])")
SOURCE_SRS=$(python3 -c "import json; d=json.load(open('$DECISION')); print(d.get('source_srs') or '')")
TARGET_SRS=$(python3 -c "import json; print(json.load(open('$DECISION'))['target_srs'])")
SQL_WHERE=$(python3 -c "import json; d=json.load(open('$DECISION')); print(d.get('sql_where') or '')")

{
  echo "=== convert_to_fgb.sh $(date -u +%Y-%m-%dT%H:%M:%SZ) ==="
  echo "layer=$LAYER strategy=$STRATEGY"

  rm -f "$OUT_FGB"

  if [[ "$STRATEGY" == "filter_9系_only" ]]; then
    SQL="SELECT * FROM \"$LAYER\" WHERE $SQL_WHERE"
    if [[ -n "$SOURCE_SRS" ]]; then
      CMD=(ogr2ogr -f FlatGeobuf "$OUT_FGB" "$GPKG" -sql "$SQL" -s_srs "$SOURCE_SRS" -t_srs "$TARGET_SRS" -nln parcels)
    else
      CMD=(ogr2ogr -f FlatGeobuf "$OUT_FGB" "$GPKG" -sql "$SQL" -t_srs "$TARGET_SRS" -nln parcels)
    fi
  elif [[ "$STRATEGY" == "force_6677_to_4326" ]]; then
    CMD=(ogr2ogr -f FlatGeobuf "$OUT_FGB" "$GPKG" "$LAYER" -s_srs "$SOURCE_SRS" -t_srs "$TARGET_SRS" -nln parcels)
  else
    CMD=(ogr2ogr -f FlatGeobuf "$OUT_FGB" "$GPKG" "$LAYER" -t_srs "$TARGET_SRS" -nln parcels)
  fi

  echo "CMD: ${CMD[*]}"
  "${CMD[@]}"
  echo "OK: $OUT_FGB"
} 2>&1 | tee -a "$LOG"
