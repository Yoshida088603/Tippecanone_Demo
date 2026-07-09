# Tippecanoe POC — DONE

- **完了日時**: 2026-07-09 23:54:08 UTC
- **入力**: `05_input_data` (23 区)
- **入力件数**: 2968919
- **CRS 方針**: 区ごとに自動判定（主に filter_9系_only）
- **target SRS**: EPSG:4326
- **除外件数**: 2814479

## 成果物

- FGB: `90_output_data/fgb/tokyo23.fgb` (154440 features)
- PMTiles: `90_output_data/pmtiles/tokyo23.pmtiles` (11139045 bytes)
- Viewer: `30_View_maplibre_on_GithubPages/index.html`
- Viewer data: `30_View_maplibre_on_GithubPages/data/tokyo23.pmtiles`
- GitHub Pages: `docs/index.html` + `docs/data/tokyo23.pmtiles`

## 変換後 bbox (EPSG:4326)

- lon: [139.569180813, 139.911137039]
- lat: [35.564878479, 35.815088586]
- center: [139.740159, 35.689984]

## QC

- FGB bbox valid: True
- PMTiles QC passed: True
