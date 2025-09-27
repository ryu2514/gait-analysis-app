#!/bin/bash

# Gait Analysis API Deployment Script
# This script handles deployment to various environments

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
DOCKER_IMAGE_NAME="gait-analysis-api"
DEFAULT_ENVIRONMENT="development"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Usage information
usage() {
    echo "Usage: $0 [OPTIONS] ENVIRONMENT"
    echo ""
    echo "ENVIRONMENT:"
    echo "  development   Deploy to local development environment"
    echo "  staging       Deploy to staging environment"
    echo "  production    Deploy to production environment"
    echo ""
    echo "OPTIONS:"
    echo "  -h, --help           Show this help message"
    echo "  -f, --force          Force deployment without confirmation"
    echo "  -b, --build-only     Build image only, don't deploy"
    echo "  -p, --project-id     GCP Project ID (for cloud deployments)"
    echo "  -r, --region         GCP Region (default: us-central1)"
    echo "  --skip-tests         Skip running tests before deployment"
    echo "  --skip-backup        Skip database backup (staging/production)"
    echo ""
    echo "Examples:"
    echo "  $0 development"
    echo "  $0 staging --project-id my-project"
    echo "  $0 production --project-id my-project --region us-east1"
}

# Parse command line arguments
ENVIRONMENT=""
FORCE=false
BUILD_ONLY=false
PROJECT_ID=""
REGION="us-central1"
SKIP_TESTS=false
SKIP_BACKUP=false

while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            usage
            exit 0
            ;;
        -f|--force)
            FORCE=true
            shift
            ;;
        -b|--build-only)
            BUILD_ONLY=true
            shift
            ;;
        -p|--project-id)
            PROJECT_ID="$2"
            shift 2
            ;;
        -r|--region)
            REGION="$2"
            shift 2
            ;;
        --skip-tests)
            SKIP_TESTS=true
            shift
            ;;
        --skip-backup)
            SKIP_BACKUP=true
            shift
            ;;
        -*)
            log_error "Unknown option: $1"
            usage
            exit 1
            ;;
        *)
            if [[ -z "$ENVIRONMENT" ]]; then
                ENVIRONMENT="$1"
            else
                log_error "Multiple environments specified"
                usage
                exit 1
            fi
            shift
            ;;
    esac
done

# Validate environment
if [[ -z "$ENVIRONMENT" ]]; then
    ENVIRONMENT="$DEFAULT_ENVIRONMENT"
fi

if [[ ! "$ENVIRONMENT" =~ ^(development|staging|production)$ ]]; then
    log_error "Invalid environment: $ENVIRONMENT"
    usage
    exit 1
fi

# Validate GCP settings for cloud deployments
if [[ "$ENVIRONMENT" == "staging" || "$ENVIRONMENT" == "production" ]]; then
    if [[ -z "$PROJECT_ID" ]]; then
        log_error "Project ID is required for $ENVIRONMENT deployment"
        exit 1
    fi
fi

log_info "Starting deployment to $ENVIRONMENT environment"

# Change to project root
cd "$PROJECT_ROOT"

# Pre-deployment checks
pre_deployment_checks() {
    log_info "Running pre-deployment checks..."
    
    # Check if required files exist
    local required_files=(
        "requirements.txt"
        "main.py"
        "Dockerfile"
    )
    
    for file in "${required_files[@]}"; do
        if [[ ! -f "$file" ]]; then
            log_error "Required file not found: $file"
            exit 1
        fi
    done
    
    # Check environment file
    local env_file=""
    case $ENVIRONMENT in
        development)
            env_file=".env"
            ;;
        staging)
            env_file=".env.staging"
            ;;
        production)
            env_file=".env.prod"
            ;;
    esac
    
    if [[ -n "$env_file" && ! -f "$env_file" ]]; then
        log_warning "Environment file not found: $env_file"
        if [[ -f "${env_file}.example" ]]; then
            log_info "Please copy ${env_file}.example to $env_file and configure it"
        fi
    fi
    
    log_success "Pre-deployment checks completed"
}

# Run tests
run_tests() {
    if [[ "$SKIP_TESTS" == "true" ]]; then
        log_warning "Skipping tests as requested"
        return
    fi
    
    log_info "Running tests..."
    
    if [[ -f "test_server.py" ]]; then
        python test_server.py
    fi
    
    if [[ -d "tests" ]]; then
        python -m pytest tests/ -v
    fi
    
    log_success "Tests completed successfully"
}

# Build Docker image
build_image() {
    log_info "Building Docker image..."
    
    local image_tag=""
    case $ENVIRONMENT in
        development)
            image_tag="$DOCKER_IMAGE_NAME:dev"
            ;;
        staging)
            image_tag="gcr.io/$PROJECT_ID/$DOCKER_IMAGE_NAME:staging"
            ;;
        production)
            image_tag="gcr.io/$PROJECT_ID/$DOCKER_IMAGE_NAME:latest"
            ;;
    esac
    
    docker build -t "$image_tag" .
    
    log_success "Docker image built: $image_tag"
    
    # Push to registry for cloud deployments
    if [[ "$ENVIRONMENT" == "staging" || "$ENVIRONMENT" == "production" ]]; then
        log_info "Pushing image to Google Container Registry..."
        docker push "$image_tag"
        log_success "Image pushed successfully"
    fi
}

# Deploy to development
deploy_development() {
    log_info "Deploying to development environment..."
    
    # Stop existing container if running
    if docker ps -q --filter "name=gait-api-dev" | grep -q .; then
        log_info "Stopping existing development container..."
        docker stop gait-api-dev
        docker rm gait-api-dev
    fi
    
    # Run new container
    docker run -d \
        --name gait-api-dev \
        -p 8000:8000 \
        --env-file .env \
        -v "$(pwd)/app:/app/app" \
        -v "$(pwd)/data:/app/data" \
        -v /tmp:/tmp \
        "$DOCKER_IMAGE_NAME:dev"
    
    log_success "Development deployment completed"
    log_info "API available at: http://localhost:8000"
}

# Deploy to staging
deploy_staging() {
    log_info "Deploying to staging environment..."
    
    # Deploy to Cloud Run
    gcloud run deploy gait-analysis-api-staging \
        --image "gcr.io/$PROJECT_ID/$DOCKER_IMAGE_NAME:staging" \
        --region "$REGION" \
        --platform managed \
        --allow-unauthenticated \
        --memory 2Gi \
        --cpu 2 \
        --max-instances 5 \
        --min-instances 0 \
        --timeout 600 \
        --set-env-vars "DEBUG=False,LOG_LEVEL=INFO,ENVIRONMENT=staging" \
        --project "$PROJECT_ID"
    
    # Get service URL
    local service_url
    service_url=$(gcloud run services describe gait-analysis-api-staging \
        --region="$REGION" \
        --project="$PROJECT_ID" \
        --format='value(status.url)')
    
    log_success "Staging deployment completed"
    log_info "API available at: $service_url"
}

# Deploy to production
deploy_production() {
    log_info "Deploying to production environment..."
    
    # Confirmation for production deployment
    if [[ "$FORCE" != "true" ]]; then
        echo -n "Are you sure you want to deploy to PRODUCTION? (yes/no): "
        read -r confirmation
        if [[ "$confirmation" != "yes" ]]; then
            log_info "Production deployment cancelled"
            exit 0
        fi
    fi
    
    # Create database backup (if not skipped)
    if [[ "$SKIP_BACKUP" != "true" ]]; then
        log_info "Creating database backup..."
        local backup_timestamp
        backup_timestamp=$(date +%Y%m%d_%H%M%S)
        
        gcloud sql backups create \
            --instance "gait-analysis-db-prod" \
            --project "$PROJECT_ID" \
            --description "Pre-deployment backup $backup_timestamp"
        
        log_success "Database backup created"
    fi
    
    # Deploy to Cloud Run
    gcloud run deploy gait-analysis-api \
        --image "gcr.io/$PROJECT_ID/$DOCKER_IMAGE_NAME:latest" \
        --region "$REGION" \
        --platform managed \
        --allow-unauthenticated \
        --memory 2Gi \
        --cpu 2 \
        --max-instances 10 \
        --min-instances 1 \
        --timeout 600 \
        --set-env-vars "DEBUG=False,LOG_LEVEL=INFO,ENVIRONMENT=production" \
        --project "$PROJECT_ID"
    
    # Get service URL
    local service_url
    service_url=$(gcloud run services describe gait-analysis-api \
        --region="$REGION" \
        --project="$PROJECT_ID" \
        --format='value(status.url)')
    
    log_success "Production deployment completed"
    log_info "API available at: $service_url"
}

# Post-deployment tests
post_deployment_tests() {
    log_info "Running post-deployment tests..."
    
    local base_url=""
    case $ENVIRONMENT in
        development)
            base_url="http://localhost:8000"
            ;;
        staging|production)
            local service_name=""
            if [[ "$ENVIRONMENT" == "staging" ]]; then
                service_name="gait-analysis-api-staging"
            else
                service_name="gait-analysis-api"
            fi
            
            base_url=$(gcloud run services describe "$service_name" \
                --region="$REGION" \
                --project="$PROJECT_ID" \
                --format='value(status.url)')
            ;;
    esac
    
    # Wait for service to be ready
    log_info "Waiting for service to be ready..."
    local max_attempts=30
    local attempt=1
    
    while [[ $attempt -le $max_attempts ]]; do
        if curl -f -s "$base_url/api/v1/health" > /dev/null 2>&1; then
            break
        fi
        
        log_info "Attempt $attempt/$max_attempts: Service not ready yet..."
        sleep 10
        ((attempt++))
    done
    
    if [[ $attempt -gt $max_attempts ]]; then
        log_error "Service failed to become ready after $max_attempts attempts"
        exit 1
    fi
    
    # Test health endpoint
    log_info "Testing health endpoint..."
    if ! curl -f -s "$base_url/api/v1/health" | grep -q "healthy"; then
        log_error "Health check failed"
        exit 1
    fi
    
    log_success "Post-deployment tests completed"
}

# Main deployment function
main() {
    log_info "Gait Analysis API Deployment"
    log_info "Environment: $ENVIRONMENT"
    log_info "Project ID: ${PROJECT_ID:-N/A}"
    log_info "Region: $REGION"
    echo ""
    
    # Run deployment steps
    pre_deployment_checks
    run_tests
    build_image
    
    if [[ "$BUILD_ONLY" == "true" ]]; then
        log_success "Build completed. Skipping deployment as requested."
        exit 0
    fi
    
    # Deploy based on environment
    case $ENVIRONMENT in
        development)
            deploy_development
            ;;
        staging)
            deploy_staging
            ;;
        production)
            deploy_production
            ;;
    esac
    
    # Run post-deployment tests
    post_deployment_tests
    
    log_success "Deployment completed successfully!"
}

# Run main function
main "$@"