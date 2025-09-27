#!/usr/bin/env python3
"""
Production Deployment Script
プロダクション環境デプロイメントスクリプト
"""

import os
import sys
import subprocess
import json
import yaml
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any

# Add the project root to Python path
sys.path.insert(0, str(Path(__file__).parent))

from app.core.advanced_logger import get_logger

logger = get_logger("production_deploy")


class ProductionDeployer:
    """プロダクション環境デプロイメントクラス"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.deployment_config = {}
        self.deployment_log = []
        
    def log_step(self, message: str, success: bool = True):
        """デプロイメントステップをログ"""
        timestamp = datetime.now().isoformat()
        status = "✅" if success else "❌"
        log_entry = f"{status} {timestamp}: {message}"
        print(log_entry)
        self.deployment_log.append(log_entry)
        
        if success:
            logger.info(message)
        else:
            logger.error(message)
    
    def check_prerequisites(self) -> bool:
        """前提条件チェック"""
        self.log_step("🔍 Checking deployment prerequisites...")
        
        checks = []
        
        # Dockerの確認
        try:
            result = subprocess.run(['docker', '--version'], capture_output=True, text=True)
            if result.returncode == 0:
                checks.append(("Docker", True, result.stdout.strip()))
            else:
                checks.append(("Docker", False, "Not installed"))
        except FileNotFoundError:
            checks.append(("Docker", False, "Not found"))
        
        # Docker Composeの確認
        try:
            result = subprocess.run(['docker-compose', '--version'], capture_output=True, text=True)
            if result.returncode == 0:
                checks.append(("Docker Compose", True, result.stdout.strip()))
            else:
                checks.append(("Docker Compose", False, "Not installed"))
        except FileNotFoundError:
            checks.append(("Docker Compose", False, "Not found"))
        
        # 必要なファイルの確認
        required_files = [
            "Dockerfile",
            "docker-compose.yml",
            "docker-compose.prod.yml",
            "requirements.txt",
            "main.py"
        ]
        
        for file_path in required_files:
            file_exists = (self.project_root / file_path).exists()
            checks.append((f"File: {file_path}", file_exists, "Found" if file_exists else "Missing"))
        
        # 結果表示
        all_passed = True
        for check_name, passed, details in checks:
            status = "✅" if passed else "❌"
            print(f"   {status} {check_name}: {details}")
            if not passed:
                all_passed = False
        
        if all_passed:
            self.log_step("Prerequisites check passed")
        else:
            self.log_step("Prerequisites check failed", False)
        
        return all_passed
    
    def create_production_config(self) -> bool:
        """プロダクション設定作成"""
        self.log_step("⚙️  Creating production configuration...")
        
        try:
            # 環境変数テンプレート作成
            env_content = """# Production Environment Variables
# プロダクション環境変数

# Database Configuration
DATABASE_URL=postgresql://gait_user:secure_password@db:5432/gait_analysis_prod
POSTGRES_DB=gait_analysis_prod
POSTGRES_USER=gait_user
POSTGRES_PASSWORD=secure_password

# Redis Configuration
REDIS_URL=redis://redis:6379/0

# JWT Configuration
JWT_SECRET_KEY=your-super-secret-jwt-key-change-this-in-production
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30

# Firebase Configuration
FIREBASE_PROJECT_ID=your-firebase-project-id
FIREBASE_PRIVATE_KEY_ID=your-firebase-private-key-id
FIREBASE_PRIVATE_KEY=your-firebase-private-key
FIREBASE_CLIENT_EMAIL=your-firebase-client-email
FIREBASE_CLIENT_ID=your-firebase-client-id
FIREBASE_AUTH_URI=https://accounts.google.com/o/oauth2/auth
FIREBASE_TOKEN_URI=https://oauth2.googleapis.com/token

# Google Cloud Configuration
GOOGLE_CLOUD_PROJECT=your-gcp-project-id
GOOGLE_APPLICATION_CREDENTIALS=/app/credentials/service-account.json

# API Configuration
ALLOWED_ORIGINS=["https://yourdomain.com", "https://www.yourdomain.com"]
API_HOST=0.0.0.0
API_PORT=8000

# MediaPipe Configuration
MEDIAPIPE_MODEL_COMPLEXITY=1
MEDIAPIPE_MIN_DETECTION_CONFIDENCE=0.7
MEDIAPIPE_MIN_TRACKING_CONFIDENCE=0.5
MEDIAPIPE_ENABLE_SEGMENTATION=false

# Performance Configuration
ENABLE_PERFORMANCE_MONITORING=true
CACHE_TTL=3600
MAX_UPLOAD_SIZE=100MB

# Security Configuration
ENABLE_CORS=true
ENABLE_HTTPS_REDIRECT=true
SECURE_COOKIES=true

# Logging Configuration
LOG_LEVEL=INFO
LOG_FORMAT=json
ENABLE_FILE_LOGGING=true
LOG_RETENTION_DAYS=30
"""
            
            env_file = self.project_root / ".env.prod"
            with open(env_file, 'w') as f:
                f.write(env_content)
            
            # Nginx設定作成
            nginx_config = """
server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;
    
    # HTTPS リダイレクト
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name yourdomain.com www.yourdomain.com;
    
    # SSL証明書設定（Let's Encryptなど）
    ssl_certificate /etc/ssl/certs/ssl-cert.pem;
    ssl_certificate_key /etc/ssl/private/ssl-cert.key;
    
    # SSL設定
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;
    
    # セキュリティヘッダー
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
    add_header Strict-Transport-Security "max-age=63072000; includeSubDomains; preload";
    
    # ファイルアップロード制限
    client_max_body_size 100M;
    
    # バックエンドAPI
    location /api/ {
        proxy_pass http://backend:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # WebSocket サポート
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        
        # タイムアウト設定
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
    
    # 静的ファイル
    location /static/ {
        alias /app/static/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
    
    # フロントエンド（Flutter Web）
    location / {
        root /var/www/html;
        try_files $uri $uri/ /index.html;
        
        # キャッシュ設定
        location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg)$ {
            expires 1y;
            add_header Cache-Control "public, immutable";
        }
    }
}
"""
            
            nginx_dir = self.project_root / "nginx"
            nginx_dir.mkdir(exist_ok=True)
            
            with open(nginx_dir / "default.conf", 'w') as f:
                f.write(nginx_config)
            
            self.log_step("Production configuration created")
            return True
            
        except Exception as e:
            self.log_step(f"Failed to create production config: {e}", False)
            return False
    
    def update_docker_compose_prod(self) -> bool:
        """プロダクション用Docker Compose設定更新"""
        self.log_step("🐳 Updating production Docker Compose configuration...")
        
        try:
            docker_compose_prod = {
                "version": "3.8",
                "services": {
                    "backend": {
                        "build": {
                            "context": ".",
                            "dockerfile": "Dockerfile"
                        },
                        "container_name": "gait-analysis-backend-prod",
                        "env_file": ".env.prod",
                        "volumes": [
                            "./logs:/app/logs",
                            "./uploads:/app/uploads",
                            "./credentials:/app/credentials:ro"
                        ],
                        "depends_on": [
                            "db",
                            "redis"
                        ],
                        "networks": [
                            "gait-network"
                        ],
                        "restart": "unless-stopped",
                        "healthcheck": {
                            "test": ["CMD", "curl", "-f", "http://localhost:8000/api/v1/health"],
                            "interval": "30s",
                            "timeout": "10s",
                            "retries": 3,
                            "start_period": "40s"
                        }
                    },
                    "db": {
                        "image": "postgres:15",
                        "container_name": "gait-analysis-db-prod",
                        "env_file": ".env.prod",
                        "volumes": [
                            "postgres_data:/var/lib/postgresql/data",
                            "./database/init.sql:/docker-entrypoint-initdb.d/init.sql:ro"
                        ],
                        "networks": [
                            "gait-network"
                        ],
                        "restart": "unless-stopped",
                        "healthcheck": {
                            "test": ["CMD-SHELL", "pg_isready -U $POSTGRES_USER -d $POSTGRES_DB"],
                            "interval": "10s",
                            "timeout": "5s",
                            "retries": 5
                        }
                    },
                    "redis": {
                        "image": "redis:7-alpine",
                        "container_name": "gait-analysis-redis-prod",
                        "volumes": [
                            "redis_data:/data"
                        ],
                        "networks": [
                            "gait-network"
                        ],
                        "restart": "unless-stopped",
                        "healthcheck": {
                            "test": ["CMD", "redis-cli", "ping"],
                            "interval": "10s",
                            "timeout": "3s",
                            "retries": 3
                        }
                    },
                    "nginx": {
                        "image": "nginx:alpine",
                        "container_name": "gait-analysis-nginx-prod",
                        "ports": [
                            "80:80",
                            "443:443"
                        ],
                        "volumes": [
                            "./nginx/default.conf:/etc/nginx/conf.d/default.conf:ro",
                            "./ssl:/etc/ssl:ro",
                            "./frontend/build:/var/www/html:ro",
                            "./static:/app/static:ro"
                        ],
                        "depends_on": [
                            "backend"
                        ],
                        "networks": [
                            "gait-network"
                        ],
                        "restart": "unless-stopped"
                    }
                },
                "volumes": {
                    "postgres_data": {},
                    "redis_data": {}
                },
                "networks": {
                    "gait-network": {
                        "driver": "bridge"
                    }
                }
            }
            
            with open(self.project_root / "docker-compose.prod.yml", 'w') as f:
                yaml.dump(docker_compose_prod, f, default_flow_style=False, indent=2)
            
            self.log_step("Production Docker Compose configuration updated")
            return True
            
        except Exception as e:
            self.log_step(f"Failed to update Docker Compose config: {e}", False)
            return False
    
    def create_deployment_scripts(self) -> bool:
        """デプロイメントスクリプト作成"""
        self.log_step("📜 Creating deployment scripts...")
        
        try:
            # デプロイメントスクリプト
            deploy_script = """#!/bin/bash
# Production Deployment Script
# プロダクション環境デプロイメントスクリプト

set -e

echo "🚀 Starting production deployment..."

# Check if .env.prod exists
if [ ! -f .env.prod ]; then
    echo "❌ .env.prod file not found. Please create it first."
    exit 1
fi

# Create necessary directories
mkdir -p logs uploads ssl credentials

# Stop existing containers
echo "🛑 Stopping existing containers..."
docker-compose -f docker-compose.prod.yml down

# Build and start containers
echo "🔨 Building and starting containers..."
docker-compose -f docker-compose.prod.yml build --no-cache
docker-compose -f docker-compose.prod.yml up -d

# Wait for services to be ready
echo "⏳ Waiting for services to be ready..."
sleep 30

# Check health status
echo "🔍 Checking service health..."
docker-compose -f docker-compose.prod.yml ps

# Run database migrations (if any)
echo "🗃️  Running database setup..."
docker-compose -f docker-compose.prod.yml exec -T backend python -c "
from app.database.init_db import init_database
init_database()
print('Database initialized successfully')
"

# Test API endpoints
echo "🧪 Testing API endpoints..."
curl -f http://localhost/api/v1/health || echo "⚠️  Health check failed"

echo "✅ Production deployment completed!"
echo "🌐 API is available at: http://localhost/api/v1/"
echo "📊 Monitoring dashboard: http://localhost/api/v1/monitoring/"
echo "📚 API documentation: http://localhost/docs"
"""
            
            with open(self.project_root / "deploy.sh", 'w') as f:
                f.write(deploy_script)
            
            # 実行権限を付与
            os.chmod(self.project_root / "deploy.sh", 0o755)
            
            # バックアップスクリプト
            backup_script = """#!/bin/bash
# Database Backup Script
# データベースバックアップスクリプト

set -e

BACKUP_DIR="./backups"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_FILE="gait_analysis_backup_${TIMESTAMP}.sql"

echo "📦 Creating database backup..."

# Create backup directory
mkdir -p $BACKUP_DIR

# Create database backup
docker-compose -f docker-compose.prod.yml exec -T db pg_dump -U gait_user gait_analysis_prod > "$BACKUP_DIR/$BACKUP_FILE"

# Compress backup
gzip "$BACKUP_DIR/$BACKUP_FILE"

echo "✅ Database backup created: $BACKUP_DIR/${BACKUP_FILE}.gz"

# Keep only last 7 backups
find $BACKUP_DIR -name "gait_analysis_backup_*.sql.gz" -type f -mtime +7 -delete

echo "🧹 Old backups cleaned up"
"""
            
            with open(self.project_root / "backup.sh", 'w') as f:
                f.write(backup_script)
            
            os.chmod(self.project_root / "backup.sh", 0o755)
            
            # 監視スクリプト
            monitor_script = """#!/bin/bash
# System Monitoring Script
# システム監視スクリプト

echo "🔍 System Status Check"
echo "======================"

# Container status
echo "📦 Container Status:"
docker-compose -f docker-compose.prod.yml ps

echo ""

# Resource usage
echo "💾 Resource Usage:"
docker stats --no-stream --format "table {{.Container}}\\t{{.CPUPerc}}\\t{{.MemUsage}}\\t{{.NetIO}}"

echo ""

# Log recent errors
echo "🚨 Recent Errors (last 10):"
docker-compose -f docker-compose.prod.yml logs --tail=10 | grep -i error || echo "No recent errors found"

echo ""

# Disk usage
echo "💿 Disk Usage:"
df -h | grep -E '^/dev/'

echo ""

# API Health check
echo "🏥 API Health Check:"
curl -s http://localhost/api/v1/health | jq '.' || echo "❌ API health check failed"
"""
            
            with open(self.project_root / "monitor.sh", 'w') as f:
                f.write(monitor_script)
            
            os.chmod(self.project_root / "monitor.sh", 0o755)
            
            self.log_step("Deployment scripts created")
            return True
            
        except Exception as e:
            self.log_step(f"Failed to create deployment scripts: {e}", False)
            return False
    
    def create_production_dockerfile(self) -> bool:
        """プロダクション用Dockerfile作成"""
        self.log_step("🐳 Creating production Dockerfile...")
        
        try:
            dockerfile_content = """# Production Dockerfile for Gait Analysis API
FROM python:3.9-slim

# システムパッケージの更新とインストール
RUN apt-get update && apt-get install -y \\
    build-essential \\
    libgl1-mesa-glx \\
    libglib2.0-0 \\
    libsm6 \\
    libxext6 \\
    libxrender-dev \\
    libgomp1 \\
    curl \\
    && rm -rf /var/lib/apt/lists/*

# 作業ディレクトリ設定
WORKDIR /app

# Pythonの最適化設定
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PIP_NO_CACHE_DIR=1
ENV PIP_DISABLE_PIP_VERSION_CHECK=1

# 依存関係をインストール
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# アプリケーションコードをコピー
COPY . .

# 必要なディレクトリを作成
RUN mkdir -p logs uploads static temp

# 実行権限設定
RUN chmod +x deploy.sh backup.sh monitor.sh

# ヘルスチェック
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \\
    CMD curl -f http://localhost:8000/api/v1/health || exit 1

# ポート公開
EXPOSE 8000

# 本番環境用の起動コマンド
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
"""
            
            with open(self.project_root / "Dockerfile", 'w') as f:
                f.write(dockerfile_content)
            
            self.log_step("Production Dockerfile created")
            return True
            
        except Exception as e:
            self.log_step(f"Failed to create Dockerfile: {e}", False)
            return False
    
    def generate_deployment_documentation(self) -> bool:
        """デプロイメント文書生成"""
        self.log_step("📚 Generating deployment documentation...")
        
        try:
            docs_content = """# Production Deployment Guide
# プロダクション環境デプロイメントガイド

## 概要

このガイドでは、MediaPipe歩行分析APIをプロダクション環境にデプロイする手順を説明します。

## 前提条件

- Docker 20.10以上
- Docker Compose 2.0以上
- 最低4GB RAM、2CPU
- 50GB以上のディスク容量
- SSL証明書（HTTPS用）

## デプロイメント手順

### 1. 環境設定

1. `.env.prod`ファイルを編集し、本番環境用の設定を行います：
   ```bash
   cp .env.prod.example .env.prod
   nano .env.prod
   ```

2. 必要な設定項目：
   - データベース接続情報
   - JWT秘密鍵
   - Firebase認証情報
   - Google Cloud設定
   - 許可するオリジンドメイン

### 2. SSL証明書設置

SSL証明書を`ssl`ディレクトリに配置：
```bash
mkdir -p ssl
# 証明書ファイルをコピー
cp your-cert.pem ssl/ssl-cert.pem
cp your-key.pem ssl/ssl-cert.key
```

### 3. デプロイメント実行

```bash
# デプロイメントスクリプトを実行
./deploy.sh
```

### 4. 動作確認

- API Health Check: `http://yourdomain.com/api/v1/health`
- API Documentation: `http://yourdomain.com/docs`
- Monitoring Dashboard: `http://yourdomain.com/api/v1/monitoring/`

## 運用管理

### バックアップ

データベースのバックアップを実行：
```bash
./backup.sh
```

### 監視

システム状態の確認：
```bash
./monitor.sh
```

### ログ確認

```bash
# 全サービスのログ
docker-compose -f docker-compose.prod.yml logs

# 特定サービスのログ
docker-compose -f docker-compose.prod.yml logs backend
```

### アップデート

```bash
# コードを更新
git pull origin main

# 再デプロイ
./deploy.sh
```

## トラブルシューティング

### コンテナが起動しない

1. ログを確認：
   ```bash
   docker-compose -f docker-compose.prod.yml logs
   ```

2. 設定ファイルを確認：
   ```bash
   docker-compose -f docker-compose.prod.yml config
   ```

### データベース接続エラー

1. データベースコンテナの状態確認：
   ```bash
   docker-compose -f docker-compose.prod.yml ps db
   ```

2. データベース接続テスト：
   ```bash
   docker-compose -f docker-compose.prod.yml exec db psql -U gait_user -d gait_analysis_prod
   ```

### パフォーマンス問題

1. リソース使用量確認：
   ```bash
   docker stats
   ```

2. 監視ダッシュボードでメトリクス確認

## セキュリティ設定

### ファイアウォール

必要なポートのみ開放：
- 80 (HTTP)
- 443 (HTTPS)
- 22 (SSH)

### 定期的なセキュリティ更新

```bash
# システムパッケージ更新
sudo apt update && sudo apt upgrade

# Dockerイメージ更新
docker-compose -f docker-compose.prod.yml pull
```

## メンテナンス

### 定期バックアップ（cron設定例）

```bash
# 毎日2時にバックアップ実行
0 2 * * * /path/to/gait-analysis-app/backend/backup.sh
```

### ログローテーション

```bash
# logrotateの設定
sudo nano /etc/logrotate.d/gait-analysis
```

## サポート

問題が発生した場合は、以下の情報を含めてサポートに連絡してください：

1. エラーメッセージ
2. ログファイル
3. システム環境情報
4. 再現手順

連絡先: support@gaitanalysis.com
"""
            
            with open(self.project_root / "DEPLOYMENT.md", 'w') as f:
                f.write(docs_content)
            
            self.log_step("Deployment documentation generated")
            return True
            
        except Exception as e:
            self.log_step(f"Failed to generate documentation: {e}", False)
            return False
    
    def run_deployment_checks(self) -> bool:
        """デプロイメント最終チェック"""
        self.log_step("🔍 Running final deployment checks...")
        
        checks_passed = True
        
        # 必要なファイルの存在確認
        required_files = [
            ".env.prod",
            "docker-compose.prod.yml",
            "Dockerfile",
            "deploy.sh",
            "backup.sh",
            "monitor.sh",
            "DEPLOYMENT.md",
            "nginx/default.conf"
        ]
        
        missing_files = []
        for file_path in required_files:
            if not (self.project_root / file_path).exists():
                missing_files.append(file_path)
                checks_passed = False
        
        if missing_files:
            self.log_step(f"Missing required files: {missing_files}", False)
        
        # Docker設定の妥当性チェック
        try:
            result = subprocess.run(
                ['docker-compose', '-f', 'docker-compose.prod.yml', 'config'],
                capture_output=True,
                text=True,
                cwd=self.project_root
            )
            if result.returncode != 0:
                self.log_step(f"Docker Compose configuration error: {result.stderr}", False)
                checks_passed = False
        except Exception as e:
            self.log_step(f"Failed to validate Docker configuration: {e}", False)
            checks_passed = False
        
        if checks_passed:
            self.log_step("All deployment checks passed")
        else:
            self.log_step("Some deployment checks failed", False)
        
        return checks_passed
    
    def generate_deployment_summary(self) -> Dict[str, Any]:
        """デプロイメント要約生成"""
        summary = {
            "timestamp": datetime.now().isoformat(),
            "deployment_log": self.deployment_log,
            "generated_files": [
                ".env.prod (template)",
                "docker-compose.prod.yml",
                "Dockerfile",
                "deploy.sh",
                "backup.sh", 
                "monitor.sh",
                "DEPLOYMENT.md",
                "nginx/default.conf"
            ],
            "next_steps": [
                "1. Edit .env.prod with your production settings",
                "2. Obtain and install SSL certificates in ssl/ directory",
                "3. Configure domain name in nginx/default.conf",
                "4. Run ./deploy.sh to start production deployment",
                "5. Set up monitoring and backup schedules",
                "6. Configure firewall and security settings"
            ],
            "endpoints": {
                "api": "https://yourdomain.com/api/v1/",
                "health": "https://yourdomain.com/api/v1/health",
                "docs": "https://yourdomain.com/docs",
                "monitoring": "https://yourdomain.com/api/v1/monitoring/",
                "performance": "https://yourdomain.com/api/v1/performance/"
            }
        }
        
        return summary


def main():
    """メイン実行"""
    print("🚀 Production Deployment Setup")
    print("=" * 50)
    
    deployer = ProductionDeployer()
    
    try:
        # 前提条件チェック
        if not deployer.check_prerequisites():
            print("\n❌ Prerequisites not met. Please install required tools.")
            return False
        
        # プロダクション設定作成
        if not deployer.create_production_config():
            return False
        
        # Docker Compose設定更新
        if not deployer.update_docker_compose_prod():
            return False
        
        # Dockerfile作成
        if not deployer.create_production_dockerfile():
            return False
        
        # デプロイメントスクリプト作成
        if not deployer.create_deployment_scripts():
            return False
        
        # ドキュメント生成
        if not deployer.generate_deployment_documentation():
            return False
        
        # 最終チェック
        if not deployer.run_deployment_checks():
            return False
        
        # 要約表示
        summary = deployer.generate_deployment_summary()
        
        print("\n✅ Production deployment setup completed!")
        print("\n📁 Generated Files:")
        for file_name in summary["generated_files"]:
            print(f"   📄 {file_name}")
        
        print("\n🔄 Next Steps:")
        for step in summary["next_steps"]:
            print(f"   {step}")
        
        print("\n🌐 Production Endpoints:")
        for name, url in summary["endpoints"].items():
            print(f"   {name.capitalize()}: {url}")
        
        print("\n📚 Documentation:")
        print("   • Deployment Guide: DEPLOYMENT.md")
        print("   • Configuration: .env.prod")
        print("   • Scripts: deploy.sh, backup.sh, monitor.sh")
        
        print("\n🎉 Ready for production deployment!")
        print("   Run './deploy.sh' when configuration is complete.")
        
        return True
        
    except Exception as e:
        deployer.log_step(f"Deployment setup failed: {e}", False)
        print(f"\n💥 Deployment setup failed: {e}")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)