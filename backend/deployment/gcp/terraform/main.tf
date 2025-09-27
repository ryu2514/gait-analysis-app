# Terraform configuration for GCP infrastructure

terraform {
  required_version = ">= 1.0"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 4.0"
    }
    google-beta = {
      source  = "hashicorp/google-beta"
      version = "~> 4.0"
    }
  }
}

# Variables
variable "project_id" {
  description = "GCP Project ID"
  type        = string
}

variable "region" {
  description = "GCP Region"
  type        = string
  default     = "us-central1"
}

variable "zone" {
  description = "GCP Zone"
  type        = string
  default     = "us-central1-a"
}

variable "environment" {
  description = "Environment (dev, staging, prod)"
  type        = string
  default     = "prod"
}

# Provider configuration
provider "google" {
  project = var.project_id
  region  = var.region
  zone    = var.zone
}

provider "google-beta" {
  project = var.project_id
  region  = var.region
  zone    = var.zone
}

# Enable required APIs
resource "google_project_service" "required_apis" {
  for_each = toset([
    "cloudbuild.googleapis.com",
    "run.googleapis.com",
    "sql-component.googleapis.com",
    "sqladmin.googleapis.com",
    "storage.googleapis.com",
    "secretmanager.googleapis.com",
    "vpcaccess.googleapis.com",
    "redis.googleapis.com"
  ])
  
  project = var.project_id
  service = each.value
  
  disable_dependent_services = true
}

# VPC Network
resource "google_compute_network" "gait_analysis_vpc" {
  name                    = "gait-analysis-vpc"
  auto_create_subnetworks = false
  
  depends_on = [google_project_service.required_apis]
}

# Subnet
resource "google_compute_subnetwork" "gait_analysis_subnet" {
  name          = "gait-analysis-subnet"
  ip_cidr_range = "10.0.0.0/24"
  region        = var.region
  network       = google_compute_network.gait_analysis_vpc.id
  
  secondary_ip_range {
    range_name    = "gait-analysis-pods"
    ip_cidr_range = "10.1.0.0/16"
  }
  
  secondary_ip_range {
    range_name    = "gait-analysis-services"
    ip_cidr_range = "10.2.0.0/16"
  }
}

# VPC Access Connector for Cloud Run
resource "google_vpc_access_connector" "gait_analysis_connector" {
  provider = google-beta
  
  name          = "gait-analysis-connector"
  region        = var.region
  network       = google_compute_network.gait_analysis_vpc.name
  ip_cidr_range = "10.8.0.0/28"
  
  depends_on = [google_project_service.required_apis]
}

# Cloud SQL instance
resource "google_sql_database_instance" "gait_analysis_db" {
  name             = "gait-analysis-db-${var.environment}"
  database_version = "POSTGRES_15"
  region           = var.region
  
  settings {
    tier              = "db-f1-micro"
    availability_type = "ZONAL"
    disk_type         = "PD_SSD"
    disk_size         = 20
    disk_autoresize   = true
    
    backup_configuration {
      enabled                        = true
      start_time                     = "03:00"
      point_in_time_recovery_enabled = true
    }
    
    ip_configuration {
      ipv4_enabled    = false
      private_network = google_compute_network.gait_analysis_vpc.id
      require_ssl     = true
    }
    
    database_flags {
      name  = "log_checkpoints"
      value = "on"
    }
    
    database_flags {
      name  = "log_connections"
      value = "on"
    }
    
    database_flags {
      name  = "log_disconnections"
      value = "on"
    }
  }
  
  deletion_protection = false  # Set to true for production
  
  depends_on = [
    google_project_service.required_apis,
    google_compute_network.gait_analysis_vpc
  ]
}

# Database
resource "google_sql_database" "gait_analysis" {
  name     = "gait_analysis"
  instance = google_sql_database_instance.gait_analysis_db.name
}

# Database user
resource "google_sql_user" "gait_user" {
  name     = "gait_user"
  instance = google_sql_database_instance.gait_analysis_db.name
  password = random_password.db_password.result
}

# Random password for database
resource "random_password" "db_password" {
  length  = 32
  special = true
}

# Redis instance
resource "google_redis_instance" "gait_analysis_cache" {
  name           = "gait-analysis-cache-${var.environment}"
  memory_size_gb = 1
  region         = var.region
  
  authorized_network = google_compute_network.gait_analysis_vpc.id
  redis_version      = "REDIS_7_0"
  display_name       = "Gait Analysis Cache"
  
  depends_on = [
    google_project_service.required_apis,
    google_compute_network.gait_analysis_vpc
  ]
}

# Cloud Storage bucket for video files
resource "google_storage_bucket" "gait_analysis_videos" {
  name          = "${var.project_id}-gait-analysis-videos"
  location      = var.region
  force_destroy = false
  
  uniform_bucket_level_access = true
  
  versioning {
    enabled = true
  }
  
  lifecycle_rule {
    condition {
      age = 90
    }
    action {
      type = "Delete"
    }
  }
  
  lifecycle_rule {
    condition {
      age = 30
    }
    action {
      type = "SetStorageClass"
      storage_class = "NEARLINE"
    }
  }
  
  depends_on = [google_project_service.required_apis]
}

# Cloud Storage bucket for reports
resource "google_storage_bucket" "gait_analysis_reports" {
  name          = "${var.project_id}-gait-analysis-reports"
  location      = var.region
  force_destroy = false
  
  uniform_bucket_level_access = true
  
  versioning {
    enabled = true
  }
  
  lifecycle_rule {
    condition {
      age = 365
    }
    action {
      type = "Delete"
    }
  }
  
  depends_on = [google_project_service.required_apis]
}

# Secret Manager secrets
resource "google_secret_manager_secret" "db_password" {
  secret_id = "db-password"
  
  replication {
    automatic = true
  }
  
  depends_on = [google_project_service.required_apis]
}

resource "google_secret_manager_secret_version" "db_password" {
  secret      = google_secret_manager_secret.db_password.id
  secret_data = random_password.db_password.result
}

resource "google_secret_manager_secret" "jwt_secret" {
  secret_id = "jwt-secret"
  
  replication {
    automatic = true
  }
  
  depends_on = [google_project_service.required_apis]
}

resource "google_secret_manager_secret_version" "jwt_secret" {
  secret      = google_secret_manager_secret.jwt_secret.id
  secret_data = random_password.jwt_secret.result
}

resource "random_password" "jwt_secret" {
  length  = 64
  special = true
}

# Outputs
output "project_id" {
  value = var.project_id
}

output "database_connection_name" {
  value = google_sql_database_instance.gait_analysis_db.connection_name
}

output "redis_host" {
  value = google_redis_instance.gait_analysis_cache.host
}

output "vpc_connector_name" {
  value = google_vpc_access_connector.gait_analysis_connector.name
}

output "videos_bucket_name" {
  value = google_storage_bucket.gait_analysis_videos.name
}

output "reports_bucket_name" {
  value = google_storage_bucket.gait_analysis_reports.name
}