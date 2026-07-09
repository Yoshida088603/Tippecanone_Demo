# LLM self-review (QC)

1. 入力 29249 件、出力 1036 件（除外 28213）。
2. CRS 方針 `filter_9系_only`: 宣言 EPSG:4326 だが coord_unit=metre_suspect。
3. 変換後 bbox lon[139.767239165, 139.788842465] lat[35.648984336, 35.685438194] は中央区想定内=True。
4. PMTiles サイズ 211780 bytes、ヘッダ検証済み。
5. Viewer は相対パス `data/13102.pmtiles` で読込。GitHub Pages デプロイは任意。
