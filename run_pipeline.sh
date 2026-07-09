#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT"

LOG_DIR="$ROOT/90_output_data/logs"
PIPELINE_LOG="$LOG_DIR/pipeline.log"

mkdir -p "$ROOT/90_output_data"/{fgb,pmtiles,qc,logs}

exec > >(tee -a "$PIPELINE_LOG") 2>&1

echo "=== run_pipeline.sh $(date -u +%Y-%m-%dT%H:%M:%SZ) ==="

for tool in ogr2ogr ogrinfo tippecanoe; do
  if ! command -v "$tool" >/dev/null 2>&1; then
    echo "ERROR: required tool not found: $tool" >&2
    exit 1
  fi
done

if [[ ! -f "$ROOT/.venv/bin/activate" ]]; then
  echo "ERROR: virtualenv not found at .venv" >&2
  exit 1
fi

source "$ROOT/.venv/bin/activate"

run_step() {
  local name="$1"
  shift
  echo ""
  echo "--- $name ---"
  "$@"
}

run_step "QC in" python3 "$ROOT/10_geopackage2FGB_pipleine/qc_in.py"
run_step "CRS decide" python3 "$ROOT/10_geopackage2FGB_pipleine/crs_decide.py"
run_step "GPKG to FGB" bash "$ROOT/10_geopackage2FGB_pipleine/convert_to_fgb.sh"
run_step "QC FGB" python3 "$ROOT/10_geopackage2FGB_pipleine/qc_fgb.py"
run_step "FGB to PMTiles" bash "$ROOT/20_Tippecanone_FGB2PMTlies/fgb_to_pmtiles.sh"
run_step "QC PMTiles" python3 "$ROOT/20_Tippecanone_FGB2PMTlies/qc_pmtiles.py"
run_step "Deploy viewer" bash "$ROOT/30_View_maplibre_on_GithubPages/deploy_viewer.sh"
run_step "Write DONE" python3 "$ROOT/scripts/write_done.py"

echo ""
echo "=== pipeline complete ==="
