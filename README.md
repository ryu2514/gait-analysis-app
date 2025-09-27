# MediaPipe 動的歩行分析アプリ

理学療法士・トレーナー・一般利用者がスマートフォン/タブレットのカメラだけで歩行動画を撮影し、歩容（gait）を定量評価できるアプリケーション。

## 概要

MediaPipe Poseを使用してマーカーレスで歩行中のランドマークを取得し、以下の指標を算出します：

- 歩行速度・歩幅・ケイデンス
- 左右対称性指標
- 関節可動域（股関節/膝/足関節）
- 荷重反応タイミング

## プロジェクト構造

```
gait-analysis-app/
├── backend/          # FastAPI + MediaPipe API
├── frontend/         # Flutter Web アプリケーション
├── shared/           # 共通リソース・データモデル
├── docs/             # ドキュメント
├── tests/            # テストスイート
└── deploy/           # デプロイメント設定
```

## 技術スタック

- **Backend**: FastAPI + MediaPipe 0.10 (Python 3.11)
- **Frontend**: Flutter 3 / Web
- **Database**: Firestore + Cloud Storage
- **Cloud**: Google Cloud Platform (Cloud Run, Cloud Functions)

## 開発環境セットアップ

### 必要条件

- Python 3.11+
- Flutter 3.0+
- Node.js 18+
- Docker

### バックエンドセットアップ

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### フロントエンドセットアップ

```bash
cd frontend
flutter pub get
flutter run -d chrome
```

## 開発ステータス

- [x] プロジェクト構造作成
- [ ] バックエンドAPI基盤構築（実装ほぼ完了・要実機テスト）
- [ ] フロントエンド基盤構築（画面骨組み・サービス層あり）
- [ ] MediaPipe統合
- [ ] 歩行分析エンジン実装

## ローカルテスト実行

### バックエンド（FastAPI）

1) 依存関係セットアップ（推奨: 仮想環境）

```bash
cd backend
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

2) スモークテスト（起動確認）

```bash
export LIGHT_MODE=1  # 軽量モード（MediaPipe無効化）
uvicorn main:app
# 別ターミナルで
curl http://localhost:8000/
curl http://localhost:8000/api/v1/health
```

3) 自動テスト（個別スクリプト）

```bash
# サーバーを別プロセスで起動した状態で（推奨: 軽量モード）
export LIGHT_MODE=1
python test_server.py
```

4) pytest（網羅的）

```bash
pytest -q           # 既定で軽量モード（MediaPipe無効）
pytest -q --heavy   # MediaPipe/CV2 を含む重いテストを実行
```

トラブルシュート:

- Pydantic v2 が必須です。グローバル環境に v1 が入っている場合は、上記の仮想環境で実行してください（`field_validator` が見つからないエラーを回避）。
- Redis 非稼働でも起動は可能です（ローカルキャッシュにフォールバック）。
- pytest は既定で `LIGHT_MODE=1` で実行されます（`backend/conftest.py`）。重いテストは `-m heavy` が付き、`--heavy` が無い場合スキップされます。

### フロントエンド（Flutter Web）

```bash
cd frontend
flutter pub get
flutter run -d chrome
```

### デモ用ワンコマンド起動 + 一時URL

```bash
# 1) デモサーバー起動（軽量モード・起動待ち付き）
cd backend
./run_demo.sh
# => Ready URL: http://127.0.0.1:<port>

# 2) （任意）一時URL公開（Cloudflare Tunnel を使用）
# macOS: brew install cloudflared
./run_tunnel.sh <port>   # 省略時は 8000
# => https://xxxx.trycloudflare.com が表示されます
```

TODO（優先度高）:

- カメラ撮影フローの実装（`analysis_screen.dart`）
- 結果共有（PDF/画像）
- 履歴の詳細遷移
- i18n 対応

## ライセンス

MIT License

## 連絡先

開発チーム

## 🚀 デプロイ（Render Blueprint）

このリポジトリには Render Blueprint 用の `render.yaml` が含まれています。GitHub 連携から1クリックで、以下を自動作成・デプロイできます。

- Web(Docker): `gait-backend`（FastAPI）
- Static Site: `gait-frontend`（Flutter Web）
- PostgreSQL: `gait-postgres`
- Redis: `gait-redis`

手順:

1) このリポジトリを GitHub にプッシュ
2) Render にログイン → New → Blueprint → 対象リポジトリを選択
3) 初回は以下の環境変数を確認
   - Backend `ALLOWED_ORIGINS`: `https://gait-frontend.onrender.com` を含める（実URLに合わせて調整）
   - Frontend `API_BASE_URL`: `https://gait-backend.onrender.com/api/v1`（実URLに合わせて調整）
   - Backend `LIGHT_MODE=1`: 初回安定化のため（動作確認後 `0` 推奨）
4) デプロイ完了後、疎通確認
   - Backend Health: `https://<backend>/api/v1/health`
   - Frontend: `https://<frontend>/` から操作（アップロード/分析実行）

補足:
- Render のサブドメインは重複時に変更される可能性があります。実際のURLに合わせて `render.yaml` またはダッシュボード上の環境変数を更新し、再デプロイしてください。
- Flutter Web は `deploy/render-frontend-build.sh` でビルドします。`API_BASE_URL` は `--dart-define` で埋め込まれます。
