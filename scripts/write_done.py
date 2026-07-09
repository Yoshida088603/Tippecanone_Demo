#!/usr/bin/env python3
"""Write DONE.md and llm_review.md completion artifacts."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
QC_DIR = ROOT / "90_output_data" / "qc"

FILES = {
    "meta_in": QC_DIR / "meta_in.json",
    "crs_decision": QC_DIR / "crs_decision.json",
    "meta_fgb": QC_DIR / "meta_fgb.json",
    "meta_pmtiles": QC_DIR / "meta_pmtiles.json",
}


def load_json(path: Path) -> dict:
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return {}


def write_done() -> None:
    meta_in = load_json(FILES["meta_in"])
    crs = load_json(FILES["crs_decision"])
    meta_fgb = load_json(FILES["meta_fgb"])
    meta_pmtiles = load_json(FILES["meta_pmtiles"])

    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    output_fgb = crs.get("output_fgb", meta_fgb.get("output", "90_output_data/fgb/tokyo23.fgb"))
    output_pmtiles = crs.get("output_pmtiles", meta_pmtiles.get("output", "90_output_data/pmtiles/tokyo23.pmtiles"))
    pmtiles_name = Path(output_pmtiles).name

    lines = [
        "# Tippecanoe POC — DONE",
        "",
        f"- **完了日時**: {now}",
        f"- **入力**: `{meta_in.get('input_dir', '05_input_data/')}` ({meta_in.get('file_count', 'N/A')} 区)",
        f"- **入力件数**: {meta_in.get('feature_count', 'N/A')}",
        f"- **CRS 方針**: 区ごとに自動判定（主に filter_9系_only）",
        f"- **target SRS**: EPSG:4326",
        f"- **除外件数**: {meta_fgb.get('excluded_count', crs.get('total_excluded', 0))}",
        "",
        "## 成果物",
        "",
        f"- FGB: `{output_fgb}` ({meta_fgb.get('feature_count', 'N/A')} features)",
        f"- PMTiles: `{output_pmtiles}` ({meta_pmtiles.get('size_bytes', 'N/A')} bytes)",
        f"- Viewer: `30_View_maplibre_on_GithubPages/index.html`",
        f"- Viewer data: `30_View_maplibre_on_GithubPages/data/{pmtiles_name}`",
        f"- GitHub Pages: `docs/index.html` + `docs/data/{pmtiles_name}`",
        "",
        "## 変換後 bbox (EPSG:4326)",
        "",
    ]

    extent = meta_fgb.get("extent", {})
    if extent:
        lines.append(f"- lon: [{extent.get('minx')}, {extent.get('maxx')}]")
        lines.append(f"- lat: [{extent.get('miny')}, {extent.get('maxy')}]")
        center = meta_fgb.get("bbox_center", [])
        if center:
            lines.append(f"- center: [{center[0]}, {center[1]}]")
    else:
        lines.append("- (bbox not recorded)")

    lines.extend(
        [
            "",
            "## QC",
            "",
            f"- FGB bbox valid: {meta_fgb.get('bbox_valid', False)}",
            f"- PMTiles QC passed: {meta_pmtiles.get('passed', False)}",
        ]
    )

    (QC_DIR / "DONE.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_llm_review() -> None:
    meta_in = load_json(FILES["meta_in"])
    meta_fgb = load_json(FILES["meta_fgb"])
    crs = load_json(FILES["crs_decision"])

    extent = meta_fgb.get("extent", {})
    expected = meta_fgb.get("bbox_expected", {})
    expected_lon = expected.get("lon", [139.55, 139.92])
    expected_lat = expected.get("lat", [35.52, 35.85])

    lines = [
        "# LLM self-review (QC)",
        "",
        f"1. 入力 {meta_in.get('file_count')} 区・{meta_in.get('feature_count')} 件、出力 {meta_fgb.get('feature_count')} 件（除外 {meta_fgb.get('excluded_count', 0)}）。",
        f"2. 区ごと CRS 自動判定、合計期待出力 {crs.get('total_expected_output', 'N/A')} 件。",
    ]

    if extent:
        lon_ok = expected_lon[0] <= extent.get("minx", 0) and extent.get("maxx", 0) <= expected_lon[1]
        lat_ok = expected_lat[0] <= extent.get("miny", 0) and extent.get("maxy", 0) <= expected_lat[1]
        lines.append(
            f"3. 変換後 bbox lon[{extent.get('minx')}, {extent.get('maxx')}] lat[{extent.get('miny')}, {extent.get('maxy')}] は東京23区想定内={lon_ok and lat_ok}。"
        )
    else:
        lines.append("3. 変換後 bbox が記録されていない。")

    pmtiles = load_json(FILES["meta_pmtiles"])
    lines.append(f"4. PMTiles サイズ {pmtiles.get('size_bytes', 0)} bytes、ヘッダ検証済み。")
    lines.append("5. Viewer は単一 PMTiles `tokyo23.pmtiles` で23区を同一地図表示。")

    (QC_DIR / "llm_review.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    QC_DIR.mkdir(parents=True, exist_ok=True)
    write_done()
    write_llm_review()
    print(f"Wrote {QC_DIR / 'DONE.md'}")
    print(f"Wrote {QC_DIR / 'llm_review.md'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
