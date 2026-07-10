# Tippecanoe Demo

東京23区の土地境界データを **GPKG → FGB → PMTiles → MapLibre** のパイプラインで変換し、GitHub Pages で地図表示する技術検証（POC）です。

## 🌐 デモ

**https://yoshida088603.github.io/Tippecanone_Demo/**

### 主な機能

| 機能 | 説明 |
| --- | --- |
| 🗺️ 地図表示 | 東京23区の土地境界ポリゴン 154,440筆を単一PMTilesで配信 |
| 🏷️ 地番ラベル | ズームレベル15以上で地番を表示 |
| 📋 属性パネル | ポリゴンクリックで属性情報を表示 |
| 📊 表示統計 | ズーム・表示ポリゴン数・LODを左下パネルに表示 |
| 📱 モバイル対応 | レスポンシブデザイン（スマートフォン・タブレット対応） |

### 表示範囲

- **座標系**: EPSG:4326（WGS84）
- **経度**: 139.569° 〜 139.911°
- **緯度**: 35.565° 〜 35.815°
- **初期表示**: 中心 [139.740159, 35.689984]、ズーム 10

## 📁 ディレクトリ構成

```
Tippecanone_Demo/
├── 05_input_data/              # 入力データ（GPKG、Git LFS管理）
├── 10_geopackage2FGB_pipleine/ # GPKG → FGB 変換スクリプト + QC
├── 20_Tippecanone_FGB2PMTlies/ # FGB → PMTiles 変換（tippecanoe）
├── 30_View_maplibre_on_GithubPages/ # MapLibre ビューア
├── 90_output_data/             # 成果物（FGB / PMTiles / QC）
│   ├── fgb/                    # FlatGeobuf出力（Git LFS管理）
│   │   ├── parts/              # 区ごとの個別FGB（Git管理外）
│   │   └── tokyo23.fgb         # 統合FGB（113MB、154,440筆）
│   ├── pmtiles/                # PMTiles出力（Git LFS管理）
│   │   └── tokyo23.pmtiles     # 配信用PMTiles（11MB）
│   └── qc/                     # 品質管理レポート
├── docs/                       # GitHub Pages公開用
├── run_pipeline.sh             # パイプライン実行スクリプト
├── requirements.txt            # Python依存パッケージ
└── plan.md                     # 実装計画書
```

## 🚀 クイックスタート

### 前提条件

- **OS**: Ubuntu 20.04以降（Windows 11の場合はWSL2を推奨）
- **Git LFS**: インストール済み
- **必要なツール**: 以下のパイプライン実行で自動インストール

### パイプライン実行

```bash
# 1. リポジトリをクローン
git clone https://github.com/Yoshida088603/Tippecanone_Demo.git
cd Tippecanone_Demo

# 2. Git LFSファイルを取得
git lfs pull

# 3. 必要なツールをインストール
sudo apt-get update
sudo apt-get install -y gdal-bin tippecanoe python3-venv

# 4. Python仮想環境をセットアップ
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 5. パイプライン実行（GPKG → FGB → PMTiles）
bash run_pipeline.sh
```

### 成果物

| ファイル | サイズ | 説明 |
| --- | --- | --- |
| `90_output_data/fgb/tokyo23.fgb` | 113MB | 統合FGB（EPSG:4326、154,440筆） |
| `90_output_data/fgb/parts/*.fgb` | - | 区ごとの個別FGB（22ファイル） |
| `90_output_data/pmtiles/tokyo23.pmtiles` | 11MB | 配信用PMTiles |
| `docs/index.html` | - | GitHub Pages ビューア |
| `docs/data/tokyo23.pmtiles` | 11MB | Pages配信用PMTiles（コピー） |
| `90_output_data/qc/DONE.md` | - | 完了証跡・統計情報 |

## 📊 データ処理の流れ

### 入力データ

- **場所**: `05_input_data/`
- **形式**: GeoPackage（GPKG）
- **対象**: 東京23区の土地境界データ（区コード `13101`〜`13123`）
- **管理**: Git LFS管理（クローン後に `git lfs pull` が必要）
- **総件数**: 2,968,919 features

### 処理フロー

```
GPKG (23区) → [QC + CRS判定] → FGB parts (22区) → tokyo23.fgb → tokyo23.pmtiles
                                                        ↓
                                                   docs/data/
```

### 座標系フィルタリング

本POCでは**公共座標9系**のデータのみを対象としています。

| 項目 | 件数 |
| --- | --- |
| 入力総数 | 2,968,919 筆 |
| 公共座標9系 | 154,440 筆（22区） |
| 任意座標系（除外） | 2,814,479 筆 |

**除外理由**: 任意座標系は測量基準点が不明で、正確な位置変換ができないため

### 荒川区（13118）の扱い

荒川区は全筆が任意座標系のため、本POCでは**変換対象外**となります。

詳細なCRS判定結果は `90_output_data/qc/crs_decision.json` を参照してください。

## ⚙️ 技術スタック

| カテゴリ | 技術 | 用途 |
| --- | --- | --- |
| データ変換 | GDAL (`ogr2ogr`) | GPKG → FGB変換、座標系変換 |
| タイル生成 | tippecanoe | FGB → PMTiles変換 |
| 品質管理 | Python + `pyogrio` | メタデータ取得、バリデーション |
| 配信 | PMTiles | 単一ファイルでのベクトルタイル配信 |
| 地図表示 | MapLibre GL JS | WebGL地図レンダリング |
| フォント | MapLibre glyphs | 日本語ラベル表示 |
| バージョン管理 | Git + Git LFS | 大容量ファイル管理 |

## 🌐 GitHub Pages 設定

| 項目 | 設定値 |
| --- | --- |
| **Source** | Deploy from a branch |
| **Branch** | `main` |
| **Folder** | `/docs` |
| **公開URL** | https://yoshida088603.github.io/Tippecanone_Demo/ |

### デプロイフロー

1. `run_pipeline.sh` 実行で成果物生成
2. `deploy_viewer.sh` が `docs/` にビューアとPMTilesをコピー
3. `main` ブランチにマージ → GitHub Pagesから自動公開

## 📝 ファイル管理（Git LFS）

大容量ファイルは Git LFS で管理しています。

| パターン | サイズ | 管理方法 |
| --- | --- | --- |
| `*.gpkg` | 〜数百MB | Git LFS |
| `*.fgb` | 〜100MB+ | Git LFS |
| `*.pmtiles` | 〜10MB+ | Git LFS |

`.gitignore` により以下は管理対象外です：

- `90_output_data/fgb/parts/` - 中間ファイル（区ごとのFGB）
- `90_output_data/logs/` - パイプライン実行ログ

## 📄 ライセンス・データ出典

- **土地境界データ**: 元データ提供元の著作権・利用条件に従います
- **本リポジトリ**: 変換・表示技術の検証（POC）を目的としています
- **コード**: リポジトリに含まれるスクリプト・設定ファイルは自由にご利用ください

## 🔍 参考資料

- [FlatGeobuf](https://flatgeobuf.org/) - クラウド最適化された地理空間データ形式
- [PMTiles](https://github.com/protomaps/PMTiles) - 単一ファイルベクトルタイル
- [MapLibre GL JS](https://maplibre.org/) - オープンソースWeb地図ライブラリ
- [tippecanoe](https://github.com/felt/tippecanoe) - ベクトルタイル生成ツール
