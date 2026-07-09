#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
exec python3 "$ROOT/10_geopackage2FGB_pipleine/convert_all_to_fgb.py"
