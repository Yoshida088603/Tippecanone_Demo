# Tippecanoe POC — DONE

- **完了日時**: 2026-07-09 23:21:31 UTC
- **入力**: `05_input_data/13102-0100-2026.gpkg`
- **入力件数**: 29249
- **座標単位判定**: metre_suspect
- **CRS 方針**: filter_9系_only
- **採用 source SRS**: (declared)
- **target SRS**: EPSG:4326
- **除外件数**: 28213

## 成果物

- FGB: `90_output_data/fgb/13102.fgb` (1036 features)
- PMTiles: `90_output_data/pmtiles/13102.pmtiles` (211780 bytes)
- Viewer: `30_View_maplibre_on_GithubPages/index.html`
- Viewer data: `30_View_maplibre_on_GithubPages/data/13102.pmtiles`

## 変換後 bbox (EPSG:4326)

- lon: [139.767239165, 139.788842465]
- lat: [35.648984336, 35.685438194]
- center: [139.778041, 35.667211]

## QC

- FGB bbox valid: True
- PMTiles QC passed: True

Mixed coordinate systems detected; public 9系 subset is already in degree coordinates — extract and keep EPSG:4326 without forced plane-rectangular reprojection.
