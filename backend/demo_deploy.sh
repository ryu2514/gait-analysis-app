#!/bin/bash

# Enhanced Gait Analysis API Demo Deployment Script
# デモ環境デプロイメントスクリプト

set -e

echo "🚀 Starting Enhanced Gait Analysis API Demo Deployment..."

# 色付きテキスト用の関数
print_status() {
    echo -e "\033[1;34m[INFO]\033[0m $1"
}

print_success() {
    echo -e "\033[1;32m[SUCCESS]\033[0m $1"
}

print_warning() {
    echo -e "\033[1;33m[WARNING]\033[0m $1"
}

print_error() {
    echo -e "\033[1;31m[ERROR]\033[0m $1"
}

# 前提条件チェック
check_prerequisites() {
    print_status "Checking prerequisites..."
    
    # Docker確認
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed. Please install Docker first."
        exit 1
    fi
    
    # Docker Compose確認
    if ! command -v docker-compose &> /dev/null; then
        print_error "Docker Compose is not installed. Please install Docker Compose first."
        exit 1
    fi
    
    # Pythonバージョン確認
    python_version=$(python3 --version 2>&1 | awk '{print $2}')
    if [[ $(echo "$python_version >= 3.9" | bc -l) -eq 0 ]]; then
        print_warning "Python 3.9+ is recommended. Current version: $python_version"
    fi
    
    print_success "Prerequisites check completed"
}

# デモディレクトリ作成
create_demo_directories() {
    print_status "Creating demo directories..."
    
    mkdir -p demo_data/{videos,reports,logs}
    mkdir -p reports
    mkdir -p uploads
    mkdir -p ssl
    mkdir -p logs
    
    print_success "Demo directories created"
}

# デモ用環境変数ファイル確認
check_env_files() {
    print_status "Checking environment files..."
    
    if [[ ! -f .env.demo ]]; then
        print_warning ".env.demo not found. Creating from template..."
        cp .env.demo.template .env.demo 2>/dev/null || {
            print_error "Please create .env.demo file"
            exit 1
        }
    fi
    
    print_success "Environment files are ready"
}

# Docker イメージビルド
build_docker_images() {
    print_status "Building Docker images..."
    
    docker-compose -f docker-compose.demo.yml build --no-cache
    
    print_success "Docker images built successfully"
}

# データベース初期化
initialize_database() {
    print_status "Initializing database..."
    
    # PostgreSQL起動とマイグレーション実行
    docker-compose -f docker-compose.demo.yml up -d postgres-demo
    sleep 10
    
    # データベース作成確認
    docker-compose -f docker-compose.demo.yml exec -T postgres-demo psql -U demo_user -d gait_analysis_demo -c "SELECT version();" || {
        print_error "Database initialization failed"
        exit 1
    }
    
    print_success "Database initialized"
}

# Redis起動確認
start_redis() {
    print_status "Starting Redis cache..."
    
    docker-compose -f docker-compose.demo.yml up -d redis-demo
    sleep 5
    
    # Redis接続確認
    docker-compose -f docker-compose.demo.yml exec -T redis-demo redis-cli ping || {
        print_error "Redis startup failed"
        exit 1
    }
    
    print_success "Redis cache started"
}

# アプリケーション起動
start_application() {
    print_status "Starting Enhanced Gait Analysis API..."
    
    docker-compose -f docker-compose.demo.yml up -d gait-api-demo
    
    # ヘルスチェック待機
    print_status "Waiting for application to be ready..."
    max_attempts=30
    attempt=0
    
    while [[ $attempt -lt $max_attempts ]]; do
        if curl -f -s http://localhost:8000/api/v1/health > /dev/null 2>&1; then
            break
        fi
        sleep 2
        ((attempt++))
        echo -n "."
    done
    echo ""
    
    if [[ $attempt -eq $max_attempts ]]; then
        print_error "Application failed to start within timeout"
        exit 1
    fi
    
    print_success "Enhanced Gait Analysis API started successfully"
}

# 監視サービス起動
start_monitoring() {
    print_status "Starting monitoring services..."
    
    docker-compose -f docker-compose.demo.yml up -d prometheus-demo
    
    print_success "Monitoring services started"
}

# Nginx起動（オプション）
start_nginx() {
    if [[ "$1" == "--with-nginx" ]]; then
        print_status "Starting Nginx reverse proxy..."
        
        # Nginx設定確認
        if [[ ! -f nginx/demo.conf ]]; then
            print_warning "Creating default Nginx configuration..."
            mkdir -p nginx
            cat > nginx/demo.conf << 'EOF'
server {
    listen 80;
    server_name localhost;
    
    location /api/ {
        proxy_pass http://gait-api-demo:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    location / {
        root /usr/share/nginx/html;
        index index.html;
        try_files $uri $uri/ /index.html;
    }
}
EOF
        fi
        
        docker-compose -f docker-compose.demo.yml up -d nginx-demo
        print_success "Nginx reverse proxy started"
    fi
}

# デモデータ作成
create_demo_data() {
    print_status "Creating demo data..."
    
    # サンプル動画ファイル作成（模擬）
    cat > demo_data/videos/README.md << 'EOF'
# Demo Video Files

Place sample gait analysis video files here:

- normal_gait.mp4: Normal walking pattern sample
- pathological_gait.mp4: Pathological gait pattern sample  
- elderly_gait.mp4: Elderly gait pattern sample
- athletic_gait.mp4: Athletic gait pattern sample

File requirements:
- Format: MP4, AVI, MOV
- Duration: 5-30 seconds
- Resolution: 720p+ recommended
- Frame rate: 30-60 fps
- Size: Under 100MB
EOF

    # デモレポート作成
    cat > demo_data/reports/README.md << 'EOF'
# Demo Report Files

Generated analysis reports will be stored here:

- PDF reports: Detailed clinical analysis reports
- Video outputs: Slow-motion skeleton overlay videos
- JSON data: Raw analysis data files
- Graph images: Time-series charts and visualizations
EOF

    # API使用例作成
    cat > demo_data/api_examples.md << 'EOF'
# Enhanced Gait Analysis API Usage Examples

## Basic Enhanced Analysis

```bash
curl -X POST "http://localhost:8000/api/v1/gait-analysis/analyze-enhanced" \
  -H "Content-Type: multipart/form-data" \
  -F "video=@demo_data/videos/normal_gait.mp4" \
  -F "user_height_cm=170" \
  -F "analysis_mode=detailed" \
  -F "camera_position=side" \
  -F "enable_30s_optimization=true" \
  -F "enable_compensation_alerts=true" \
  -F "enable_balance_analysis=true"
```

## Check API Capabilities

```bash
curl http://localhost:8000/api/v1/gait-analysis/capabilities
```

## Get Demo Data

```bash
curl http://localhost:8000/api/v1/gait-analysis/demo-data
```

## Health Check

```bash
curl http://localhost:8000/api/v1/health
```
EOF

    print_success "Demo data created"
}

# システム状態確認
check_system_status() {
    print_status "Checking system status..."
    
    echo ""
    echo "📊 Service Status:"
    echo "=================="
    
    # Docker コンテナ状態
    docker-compose -f docker-compose.demo.yml ps
    
    echo ""
    echo "🌐 API Endpoints:"
    echo "================="
    echo "• Enhanced API: http://localhost:8000/api/v1/gait-analysis/analyze-enhanced"
    echo "• API Documentation: http://localhost:8000/docs"
    echo "• Health Check: http://localhost:8000/api/v1/health"
    echo "• Capabilities: http://localhost:8000/api/v1/gait-analysis/capabilities"
    echo "• Demo Data: http://localhost:8000/api/v1/gait-analysis/demo-data"
    
    if docker-compose -f docker-compose.demo.yml ps | grep -q nginx-demo; then
        echo "• Nginx Proxy: http://localhost/"
    fi
    
    if docker-compose -f docker-compose.demo.yml ps | grep -q prometheus-demo; then
        echo "• Prometheus: http://localhost:9090"
    fi
    
    echo ""
    echo "📁 Data Directories:"
    echo "==================="
    echo "• Upload: ./uploads/"
    echo "• Reports: ./reports/"
    echo "• Demo Data: ./demo_data/"
    echo "• Logs: ./logs/"
    
    print_success "System status check completed"
}

# 終了処理
cleanup_on_exit() {
    if [[ "$1" == "--stop" ]]; then
        print_status "Stopping all demo services..."
        docker-compose -f docker-compose.demo.yml down
        print_success "All services stopped"
    fi
}

# ヘルプ表示
show_help() {
    echo "Enhanced Gait Analysis API Demo Deployment Script"
    echo ""
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  --help          Show this help message"
    echo "  --stop          Stop all running services"
    echo "  --with-nginx    Start with Nginx reverse proxy"
    echo "  --rebuild       Force rebuild of Docker images"
    echo ""
    echo "Examples:"
    echo "  $0                    # Standard demo deployment"
    echo "  $0 --with-nginx       # Deploy with Nginx proxy"
    echo "  $0 --stop             # Stop all services"
    echo ""
}

# メイン実行フロー
main() {
    case "$1" in
        --help)
            show_help
            exit 0
            ;;
        --stop)
            cleanup_on_exit --stop
            exit 0
            ;;
        --rebuild)
            print_status "Rebuilding with --no-cache option..."
            docker-compose -f docker-compose.demo.yml down
            docker-compose -f docker-compose.demo.yml build --no-cache
            ;;
    esac
    
    echo "🎯 Enhanced MediaPipe Gait Analysis API v2.0"
    echo "=============================================="
    echo ""
    
    check_prerequisites
    create_demo_directories
    check_env_files
    
    if [[ "$1" == "--rebuild" ]] || ! docker images | grep -q gait-analysis; then
        build_docker_images
    fi
    
    initialize_database
    start_redis
    start_application
    start_monitoring
    start_nginx "$1"
    create_demo_data
    
    echo ""
    print_success "🎉 Enhanced Gait Analysis API Demo Deployment Completed!"
    echo ""
    
    check_system_status
    
    echo ""
    echo "🚀 Next Steps:"
    echo "============="
    echo "1. Visit http://localhost:8000/docs for interactive API documentation"
    echo "2. Upload a sample video using the /analyze-enhanced endpoint"
    echo "3. Check capabilities with /capabilities endpoint"
    echo "4. View demo data with /demo-data endpoint"
    echo "5. Monitor logs: docker-compose -f docker-compose.demo.yml logs -f"
    echo ""
    echo "🛑 To stop all services: $0 --stop"
    echo ""
}

# スクリプト実行
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi