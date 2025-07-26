terraform {
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "4.51.0"
    }
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

resource "google_project" "project" {
  project_id      = var.project_id
  name            = var.project_id
  billing_account = var.billing_account
  org_id          = var.org_id
}

resource "google_project_service" "apis" {
  project = google_project.project.project_id
  count   = length(var.apis)
  service = var.apis[count.index]

  disable_on_destroy = false
}

resource "google_sql_database_instance" "timescaledb" {
  name             = "timescaledb"
  database_version = "POSTGRES_14"
  region           = var.region

  settings {
    tier = "db-custom-2-8192"
  }
}
