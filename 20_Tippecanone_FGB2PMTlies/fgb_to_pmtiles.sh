#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
FGB="$ROOT/90_output_data/fgb/13102.fgb"
OUT="$ROOT/90_output_data/pmtiles/13102.pmtiles"
LOG="$ROOT/90_output_data/logs/tippecanoe.log"

mkdir -p "$(dirname "$OUT")" "$(dirname "$LOG")"

if [[ ! -f "$FGB" ]]; then
  echo "ERROR: FGB not found: $FGB" >&2
  exit 1
fi

{
  echo "=== fgb_to_pmtiles.sh $(date -u +%Y-%m-%dT%H:%M:%SZ) ==="
  rm -f "$OUT"
  CMD=(tippecanoe -o "$OUT" -zg --drop-densest-as-needed --extend-zooms-if-still-dropping -l parcels "$FGB")
  echo "CMD: ${CMD[*]}"
  "${CMD[@]}"
  ls -lh "$OUT"
  echo "OK: $OUT"
} 2>&1 | tee -a "$LOG"
