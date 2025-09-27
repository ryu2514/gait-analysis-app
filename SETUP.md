# MediaPipe歩行分析アプリ - セットアップガイド

## 🚀 クイックスタート

このアプリケーションは、MediaPipeを使用してスマートフォン動画から歩行分析を行うシステムです。

## 📋 必要条件

### システム要件
- **Python**: 3.11以上
- **Flutter**: 3.0以上
- **Node.js**: 18以上
- **Docker**: 20.10以上（オプション）

### 推奨スペック
- **RAM**: 8GB以上
- **CPU**: 4コア以上
- **ストレージ**: 10GB以上の空き容量

## 🔧 バックエンドセットアップ

### 1. 仮想環境の作成と依存関係インストール

```bash
cd backend
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install --upgrade pip
pip install -r requirements.txt
```

または、提供されたスクリプトを使用：

```bash
cd backend
chmod +x install_deps.sh
./install_deps.sh
```

### 2. 環境変数の設定

```bash
cp .env.example .env
# .env ファイルを編集して必要な設定を行う
```

### 3. サーバーの起動

```bash
source venv/bin/activate
python main.py
```

サーバーは http://localhost:8000 で起動します。

### 4. 動作確認

```bash
curl http://localhost:8000/api/v1/health
```

## 📱 フロントエンドセットアップ

### 1. 依存関係のインストール

```bash
cd frontend
flutter pub get
```

### 2. ウェブアプリの起動

```bash
flutter run -d chrome
```

### 3. モバイルアプリのビルド（オプション）

```bash
# Android
flutter build apk

# iOS
flutter build ios
```

## 🐳 Dockerでの起動

### 1. Dockerイメージのビルド

```bash
cd backend
docker build -t gait-analysis-api .
```

### 2. Docker Composeでの起動

```bash
docker-compose up -d
```

## 🧪 テスト実行

### バックエンドテスト

```bash
cd backend
source venv/bin/activate
python test_server.py
```

### フロントエンドテスト

```bash
cd frontend
flutter test
```

## 📊 API仕様

### エンドポイント一覧

- `GET /` - ルートエンドポイント
- `GET /api/v1/health` - ヘルスチェック
- `GET /api/v1/ready` - レディネスチェック
- `POST /api/v1/analyze` - 歩行分析実行
- `GET /api/v1/analysis/{id}` - 分析結果取得
- `GET /api/v1/supported-formats` - サポート形式取得

### API仕様詳細

サーバー起動後、以下でSwagger UIを確認できます：
http://localhost:8000/docs

## 🔧 トラブルシューティング

### よくある問題

#### 1. MediaPipeのインストールエラー

```bash
# macOSの場合
brew install cmake
pip install mediapipe

# Linuxの場合
sudo apt-get install libopencv-dev
pip install mediapipe
```

#### 2. Flutterの依存関係エラー

```bash
flutter clean
flutter pub get
```

#### 3. ポート番号の競合

`.env`ファイルでポート番号を変更：

```
PORT=8001
```

#### 4. メモリ不足エラー

動画サイズを小さくするか、以下の設定を調整：

```
MAX_VIDEO_SIZE_MB=50
MAX_VIDEO_DURATION_SECONDS=15
```

## 📂 プロジェクト構造

```
gait-analysis-app/
├── backend/          # FastAPI + MediaPipe API
│   ├── app/
│   │   ├── api/      # APIエンドポイント
│   │   ├── core/     # 設定・ログ
│   │   ├── models/   # データモデル
│   │   └── services/ # ビジネスロジック
│   ├── main.py       # アプリケーションエントリポイント
│   └── requirements.txt
├── frontend/         # Flutter Webアプリ
│   ├── lib/
│   │   ├── screens/  # 画面
│   │   ├── widgets/  # ウィジェット
│   │   ├── services/ # API通信
│   │   └── models/   # データモデル
│   └── pubspec.yaml
└── docs/            # ドキュメント
```

## 🚀 デプロイ

### Google Cloud Platform

```bash
cd deploy/gcp
gcloud app deploy
```

### Docker

```bash
docker build -t gait-analysis .
docker run -p 8000:8000 gait-analysis
```

## 📞 サポート

問題が発生した場合は、以下を確認してください：

1. [トラブルシューティング](#-トラブルシューティング)
2. ログファイルの確認
3. 依存関係の再インストール

## 📚 参考資料

- [MediaPipe Documentation](https://mediapipe.dev/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Flutter Documentation](https://flutter.dev/docs)

---

**開発チーム**  
MediaPipe歩行分析アプリプロジェクト