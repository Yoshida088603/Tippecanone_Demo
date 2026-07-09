#!/usr/bin/env python3
"""QC PMTiles output: file size and header validation."""

from __future__ import annotations

import json
import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PMTILES = ROOT / "90_output_data" / "pmtiles" / "13102.pmtiles"
OUT = ROOT / "90_output_data" / "qc" / "meta_pmtiles.json"


def read_pmtiles_header(path: Path) -> dict:
    with path.open("rb") as fh:
        header = fh.read(127)
    if len(header) < 7:
        raise ValueError("file too small for PMTiles header")

    magic = header[0:7]
    version = header[7]
    return {
        "magic": magic.decode("ascii", errors="replace"),
        "version": version,
        "header_bytes": len(header),
    }


def main() -> int:
    if not PMTILES.exists():
        print(f"ERROR: PMTiles not found: {PMTILES}", file=sys.stderr)
        return 1

    size = PMTILES.stat().st_size
    errors: list[str] = []

    if size <= 0:
        errors.append("file size must be > 0")

    header_info: dict | None = None
    try:
        header_info = read_pmtiles_header(PMTILES)
        if header_info["magic"] != "PMTiles":
            errors.append(f"unexpected magic: {header_info['magic']!r}")
        if header_info["version"] != 3:
            errors.append(f"unexpected version: {header_info['version']}")
    except Exception as exc:
        errors.append(f"header read failed: {exc}")

    passed = size > 0 and not errors

    meta = {
        "output": str(PMTILES.relative_to(ROOT)),
        "size_bytes": size,
        "header": header_info,
        "passed": passed,
        "errors": errors,
    }

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(meta, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(f"Wrote {OUT}")
    print(f"size={size}, passed={passed}")

    if not passed:
        for err in errors:
            print(f"ERROR: {err}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
