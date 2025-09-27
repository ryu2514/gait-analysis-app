# Gait Analysis API - デプロイメントガイド

このガイドでは、Gait Analysis APIを様々な環境にデプロイする方法について説明します。

## 目次

1. [前提条件](#前提条件)
2. [環境設定](#環境設定)
3. [ローカル開発環境](#ローカル開発環境)
4. [ステージング環境](#ステージング環境)
5. [本番環境](#本番環境)
6. [監視とログ](#監視とログ)
7. [トラブルシューティング](#トラブルシューティング)

## 前提条件

### 必要なソフトウェア

- Docker 20.10+
- Docker Compose 2.0+
- Google Cloud SDK (クラウドデプロイメント用)
- Terraform 1.0+ (インフラ管理用)

### Google Cloud Platform設定

1. GCPプロジェクトの作成
2. 必要なAPIの有効化
3. サービスアカウントの作成
4. 認証情報の設定

```bash
# Google Cloud SDKのインストール
curl https://sdk.cloud.google.com | bash
exec -l $SHELL

# プロジェクトの設定
gcloud config set project YOUR_PROJECT_ID
gcloud auth login
gcloud auth application-default login
```

## 環境設定

### 環境変数ファイルの準備

各環境用の設定ファイルを作成します：

```bash
# 開発環境
cp .env.example .env

# ステージング環境
cp .env.example .env.staging

# 本番環境
cp .env.prod.example .env.prod
```

必要に応じて各ファイルの値を編集してください。

## ローカル開発環境

### Docker Composeを使用したデプロイ

```bash
# アプリケーションのビルドと起動
docker-compose up --build

# バックグラウンドで実行
docker-compose up -d --build

# ログの確認
docker-compose logs -f gait-api

# 停止
docker-compose down
```

### 開発用コマンド

```bash
# 個別サービスの再起動
docker-compose restart gait-api

# データベースのリセット
docker-compose down -v
docker-compose up -d postgres
docker-compose exec gait-api python -c "from app.database.connection import init_database; import asyncio; asyncio.run(init_database())"

# テストの実行
docker-compose exec gait-api python -m pytest tests/
```

## ステージング環境

### デプロイメントスクリプトの使用

```bash
# ステージング環境へのデプロイ
./deployment/deploy.sh staging --project-id YOUR_PROJECT_ID

# テストのスキップ
./deployment/deploy.sh staging --project-id YOUR_PROJECT_ID --skip-tests

# 強制デプロイ（確認なし）
./deployment/deploy.sh staging --project-id YOUR_PROJECT_ID --force
```

### 手動デプロイ

```bash
# イメージのビルドとプッシュ
docker build -t gcr.io/YOUR_PROJECT_ID/gait-analysis-api:staging .
docker push gcr.io/YOUR_PROJECT_ID/gait-analysis-api:staging

# Cloud Runへのデプロイ
gcloud run deploy gait-analysis-api-staging \
  --image gcr.io/YOUR_PROJECT_ID/gait-analysis-api:staging \
  --region us-central1 \
  --platform managed \
  --allow-unauthenticated \
  --memory 2Gi \
  --cpu 2 \
  --max-instances 5 \
  --timeout 600
```

## 本番環境

### インフラの作成 (Terraform)

```bash
cd deployment/gcp/terraform

# 初期化
terraform init

# プランの確認
terraform plan -var="project_id=YOUR_PROJECT_ID"

# インフラの作成
terraform apply -var="project_id=YOUR_PROJECT_ID"
```

### アプリケーションのデプロイ

```bash
# 本番環境へのデプロイ
./deployment/deploy.sh production --project-id YOUR_PROJECT_ID

# データベースバックアップのスキップ（緊急時のみ）
./deployment/deploy.sh production --project-id YOUR_PROJECT_ID --skip-backup
```

### Cloud Build (CI/CD)

```bash
# Cloud Buildの有効化
gcloud services enable cloudbuild.googleapis.com

# ビルドトリガーの作成
gcloud builds triggers create github \
  --repo-name=gait-analysis-app \
  --repo-owner=YOUR_GITHUB_USERNAME \
  --branch-pattern="^main$" \
  --build-config=deployment/gcp/cloudbuild.yaml
```

## 監視とログ

### 監視システムの起動

```bash
# 監視スタックの起動
docker-compose -f docker-compose.monitoring.yml up -d

# アクセス先
# Prometheus: http://localhost:9090
# Grafana: http://localhost:3001 (admin/admin123)
# AlertManager: http://localhost:9093
```

### ログの確認

```bash
# アプリケーションログ
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=gait-analysis-api" --limit 50 --format json

# エラーログのみ
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=gait-analysis-api AND severity>=ERROR" --limit 20

# リアルタイムログ
gcloud logging tail "resource.type=cloud_run_revision AND resource.labels.service_name=gait-analysis-api"
```

### パフォーマンス監視

```bash
# Cloud Monitoringダッシュボードの確認
https://console.cloud.google.com/monitoring

# カスタムメトリクスの確認
gcloud monitoring metrics list --filter="metric.type:custom.googleapis.com/gait_analysis/*"
```

## セキュリティ設定

### SSL/TLS証明書の設定

```bash
# Let's Encryptを使用した証明書の取得
sudo certbot certonly --standalone -d api.yourdomain.com

# 証明書ファイルの配置
sudo cp /etc/letsencrypt/live/api.yourdomain.com/fullchain.pem ./ssl/
sudo cp /etc/letsencrypt/live/api.yourdomain.com/privkey.pem ./ssl/
```

### ファイアウォール設定

```bash
# Cloud Armorの設定
gcloud compute security-policies create gait-analysis-security-policy

# レート制限ルールの追加
gcloud compute security-policies rules create 1000 \
  --security-policy=gait-analysis-security-policy \
  --action=rate-based-ban \
  --rate-limit-threshold-count=100 \
  --rate-limit-threshold-interval-sec=60 \
  --ban-duration-sec=600
```

## バックアップ・復旧

### データベースバックアップ

```bash
# 手動バックアップ
gcloud sql backups create --instance=gait-analysis-db-prod

# 自動バックアップの設定
gcloud sql instances patch gait-analysis-db-prod \
  --backup-start-time=03:00 \
  --enable-bin-log \
  --backup-location=us-central1
```

### データ復旧

```bash
# 特定のバックアップからの復旧
gcloud sql backups restore BACKUP_ID \
  --restore-instance=gait-analysis-db-prod \
  --backup-instance=gait-analysis-db-prod
```

## トラブルシューティング

### よくある問題

1. **メモリ不足エラー**
   ```bash
   # メモリ制限の増加
   gcloud run services update gait-analysis-api --memory 4Gi
   ```

2. **タイムアウトエラー**
   ```bash
   # タイムアウト時間の延長
   gcloud run services update gait-analysis-api --timeout 900
   ```

3. **データベース接続エラー**
   ```bash
   # 接続確認
   gcloud sql connect gait-analysis-db-prod --user=gait_user
   
   # VPCコネクタの確認
   gcloud compute networks vpc-access connectors describe gait-analysis-connector --region=us-central1
   ```

4. **イメージプルエラー**
   ```bash
   # Container Registryの認証確認
   gcloud auth configure-docker
   
   # イメージの存在確認
   gcloud container images list --repository=gcr.io/YOUR_PROJECT_ID
   ```

### ヘルスチェック

```bash
# APIヘルスチェック
curl https://your-api-url/api/v1/health

# 詳細なヘルスチェック
curl https://your-api-url/api/v1/health?detailed=true
```

### ログ分析

```bash
# エラー率の確認
gcloud logging read "
  resource.type=cloud_run_revision 
  AND resource.labels.service_name=gait-analysis-api 
  AND httpRequest.status>=400
" --format="value(timestamp,httpRequest.status)" --limit=100

# レスポンス時間の分析
gcloud logging read "
  resource.type=cloud_run_revision 
  AND resource.labels.service_name=gait-analysis-api 
  AND httpRequest.latency.seconds>5
" --format="value(timestamp,httpRequest.latency)" --limit=50
```

## 継続的な改善

### パフォーマンス最適化

1. **Cloud CDNの有効化**
2. **データベースクエリの最適化**
3. **キャッシュ戦略の改善**
4. **リソース使用量の監視**

### セキュリティ強化

1. **定期的なセキュリティスキャン**
2. **依存関係の更新**
3. **アクセスログの分析**
4. **侵入検知システムの設定**

## サポート

問題が発生した場合は、以下の情報を収集してサポートチームに連絡してください：

1. エラーメッセージとスタックトレース
2. 発生時刻
3. 使用環境（ブラウザ、OS等）
4. 再現手順
5. アプリケーションログ