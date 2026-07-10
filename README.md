# Tippecanone Demo

東京23区の土地境界データ（GPKG）を **GPKG → FGB → PMTiles → MapLibre** のパイプラインで変換し、GitHub Pages 上で地図表示する POC です。

## デモ（GitHub Pages）

**アクセス URL:** https://yoshida088603.github.io/Tippecanone_Demo/

| 機能 | 説明 |
| --- | --- |
| 地図表示 | 東京23区の土地境界ポリゴン（154,440 筆）を単一 PMTiles で表示 |
| 地番ラベル | ズーム 15 以上で `地番` を表示 |
| 属性パネル | ポリゴンをクリックすると属性テーブルを表示 |
| 表示統計 | ズーム・表示ポリゴン数・LOD などを左下パネルに表示 |
| モバイル対応 | `100dvh` レイアウト・絶対 PMTiles URL・`map.resize()` によりスマートフォンでも表示 |

### 表示範囲（EPSG:4326）

- 経度: 139.569° 〜 139.911°
- 緯度: 35.565° 〜 35.815°
- 初期表示: center `[139.740159, 35.689984]`, zoom `10`

## ディレクトリ構成

```
Tippecanone_Demo/
  05_input_data/                # 入力 GPKG（東京23区、Git LFS）
  10_geopackage2FGB_pipleine/   # GPKG→FGB 変換 + QC
  20_Tippecanone_FGB2PMTlies/   # FGB→PMTiles（tippecanoe）
  30_View_maplibre_on_GithubPages/  # MapLibre ビューア
  90_output_data/               # 成果物（FGB / PMTiles / QC / logs）
  docs/                         # GitHub Pages 公開用（/docs フォルダ）
  run_pipeline.sh               # 端到端パイプライン
  plan.md                       # 実装計画書
```

## クイックスタート（パイプライン再実行）

### 前提

- Ubuntu 等の Linux 環境（Windows 11 では WSL 等を利用）
- `gdal-bin`, `tippecanoe`, `python3-venv` が利用可能であること
- 入力 GPKG は Git LFS で取得すること

```bash
git lfs pull
sudo apt-get install -y gdal-bin tippecanoe python3-venv
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
bash run_pipeline.sh
```

### 主な成果物

| ファイル | 内容 |
| --- | --- |
| `90_output_data/fgb/tokyo23.fgb` | マージ済み FGB（EPSG:4326、154,440 features） |
| `90_output_data/pmtiles/tokyo23.pmtiles` | 配信用 PMTiles（約 11 MB） |
| `docs/index.html` | GitHub Pages ビューア |
| `docs/data/tokyo23.pmtiles` | Pages 配信 PMTiles |
| `90_output_data/qc/DONE.md` | 完了証跡 |

## 入力データ

`05_input_data/` に東京23区の土地境界 GPKG（`13101`〜`13123`）を同梱しています。  
ファイルは **Git LFS** 管理です。クローン後は `git lfs pull` を実行してください。

## 既知の制限（POC スコープ）

| 項目 | 内容 |
| --- | --- |
| 荒川区（13118） | 任意座標系のみのため、本 POC では変換・表示対象外 |
| 任意座標系の筆 | 約 281 万件は `filter_9系_only` 方針により除外 |
| 表示件数 | 公共座標9系のみ 154,440 筆（22 区相当） |

CRS 判定の詳細は `90_output_data/qc/crs_decision.json` を参照してください。

## GitHub Pages 設定

| 項目 | 値 |
| --- | --- |
| Source | Deploy from a branch |
| Branch | `main` |
| Folder | `/docs` |
| 公開 URL | https://yoshida088603.github.io/Tippecanone_Demo/ |

`run_pipeline.sh` 実行後、`deploy_viewer.sh` が `docs/` にビューアと PMTiles をコピーします。  
`main` ブランチへマージすると GitHub Pages から自動公開されます。

## 技術スタック

- **変換**: GDAL (`ogr2ogr`), tippecanoe
- **QC**: Python (`pyogrio`)
- **配信**: PMTiles
- **表示**: MapLibre GL JS + pmtiles プロトコル
- **フォント**: MapLibre デモ glyphs（地番ラベル用）

## ライセンス・データ出典

土地境界データの著作権・利用条件は元データの提供元に従います。  
本リポジトリは変換・表示の技術検証（POC）を目的としています。
