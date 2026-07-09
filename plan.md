# Tippecanoe POC — Cloud Agent 実装計画

土地境界 GPKG → FGB → PMTiles → MapLibre（GitHub Pages）の端到端 POC。  
**実行主体**: Cursor Cloud Agent。人間の途中判断なしで完走する。

## 制約

- 編集可: `mojXML/_temp/Tippecanone_Demo/**` のみ（公開用リポはこのディレクトリ単位）
- 入力は **同梱** `05_input_data/` のみ参照（親の `tokyo2026/` に依存しない）
- ローカル QGIS 前提にしない（Cloud VM = Ubuntu。`apt` / venv で GDAL・tippecanoe を自前導入）
- 成果物はすべて `90_output_data/` に集約。Pages 用静的ファイルは `30_View_maplibre_on_GithubPages/`

## 固定決定（迷わない）

| 項目 | 値 |
| --- | --- |
| 入力 | `05_input_data/13102-0100-2026.gpkg`（中央区・tokyo2026 からコピー） |
| 配信 CRS | **必ず EPSG:4326**（MapLibre / tippecanoe 向け）。元が 6677 等なら変換時に再投影 |
| 中間 | `90_output_data/fgb/13102.fgb`（4326） |
| 配信 | `90_output_data/pmtiles/13102.pmtiles` を Pages 配下へコピー |
| tippecanoe | `-zg --drop-densest-as-needed --extend-zooms-if-still-dropping -l parcels` |
| 表示 | MapLibre GL + pmtiles プロトコル。初期中心は QC の bbox 中心 |
| Cesium | 今回スコープ外（同一 PMTiles を後続可） |

## CRS 注意（要・実行時判定）

**メタデータだけ信じない。** 中央区 GPKG の現状（ローカル確認済み）:

- Layer SRS: **EPSG:4326** と宣言
- Extent: `(-6618.57, -39614.68) – (203.20, 158.11)` → **度ではなくメートル域**
- 属性 `座標系` は「任意座標系」「公共座標9系」混在（9系 ≒ **EPSG:6677**）

つまり「SRS=4326」でも実座標が平面直角の可能性あり。Agent は次で判定する:

| 判定 | 条件 | 処理 |
| --- | --- | --- |
| 度座標 | `|x|≤180` かつ `|y|≤90` が大半 | 再投影なし（必要なら `-a_srs EPSG:4326` のみ） |
| 平面直角（9系疑い） | 値が数千〜数万 m オーダー、または SRS/属性が 6677・公共9系 | `ogr2ogr -s_srs EPSG:6677 -t_srs EPSG:4326`（宣言が嘘でも `-s_srs` で上書き） |
| 混在/任意 | 同一レイヤに度と m が混在、または任意座標のみ | POC では **公共9系（平面）フィーチャーだけ抽出して 6677→4326**。任意座標はスキップし `qc` に件数を記録 |

合格 bbox（変換後・4326）: lon `[139.74, 139.82]`, lat `[35.64, 35.71]`。  
変換前の m 域 bbox をこの数値で判定しないこと。

## ディレクトリ

```
Tippecanone_Demo/
  05_input_data/                # 同梱サンプル（中央区 GPKG）
  10_geopackage2FGB_pipleine/   # convert + QC スクリプト
  20_Tippecanone_FGB2PMTlies/   # tippecanoe ラッパ
  30_View_maplibre_on_GithubPages/  # index.html 等（PMTiles 同梱 or data/）
  90_output_data/{fgb,pmtiles,qc,logs}/
  plan.md
  requirements.txt              # 必要なら（pyogrio/gdal 等）
```

`05_input_data/README.md` は任意。出典メモ: 元は `mojXML/30_output_data/tokyo2026/13102-0100-2026.gpkg`。

## 環境セットアップ（Agent が最初に実行）

```bash
sudo apt-get update
sudo apt-get install -y gdal-bin libgdal-dev tippecanoe python3-venv python3-pip
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt   # 最小: メタ取得用（pyogrio または gdal）
```

`ogr2ogr` / `ogrinfo` / `tippecanoe` が PATH にあれば Python バインディングは任意。無い場合のみ venv で補う。

## パイプライン（自動・順次）

1. **QC in** — layer名・件数・extent・宣言 CRS・座標オーダー判定 → `meta_in.json`（`coord_unit`: `degree` / `metre_suspect`）
2. **CRS 方針決定** — 上表どおり。方針と採用 `-s_srs` を `qc/crs_decision.json` に書く
3. **GPKG→FGB（4326）** — 必要なら 6677→4326。混在時は平面ラベルのみ SQL/where で絞る
4. **合格判定（機械・変換後）** — 件数>0、FGB extent が中央区 lon/lat 想定内。失敗時はログ残して終了
5. **QC mid** — `meta_fgb.json`（件数・4326 bbox・入力からの除外件数）
6. **FGB→PMTiles** — tippecanoe → `13102.pmtiles` + コマンドログ
7. **QC out** — ファイルサイズ > 0、`pmtiles` ヘッダ/メタが読めること
8. **Viewer** — `30_.../index.html` + `data/13102.pmtiles`。basemap CDN、parcel fill+line
9. **完了証跡** — `qc/DONE.md`（入力・件数・CRS方針・bbox・成果物パス）

## 範囲確認（人間なし）

人間の地図目視はゲートにしない。代わりに:

- bbox / 件数の機械チェック（上記）
- Agent が `meta_*.json` を読み、想定範囲との差分を `qc/llm_review.md` に 5 行以内で自己記録
- （任意）Cloud Agent にブラウザがあれば Viewer を開き、コンソールエラー無しを確認。無くてもブロッカーにしない

## 完了定義

- [ ] FGB/PMTiles が **4326** で中央区 bbox 内
- [ ] `qc/crs_decision.json` と `DONE.md` あり
- [ ] Viewer が相対パスで PMTiles を読む
- GitHub Pages 設定・push は任意

## 作業順

1. ツール導入 → 2. QC in + CRS判定 → 3. FGB(4326) → 4. PMTiles → 5. Viewer → 6. DONE.md
