variable "project_id" {
  description = "The project ID to host the resources in."
  type        = string
  default     = "kite-trader"
}

variable "region" {
  description = "The region to host the resources in."
  type        = string
  default     = "us-central1"
}

variable "billing_account" {
  description = "The billing account to associate with the project."
  type        = string
}

variable "org_id" {
  description = "The organization ID to associate with the project."
  type        = string
}

variable "apis" {
  description = "The APIs to enable on the project."
  type        = list(string)
  default = [
    "run.googleapis.com",
    "secretmanager.googleapis.com",
    "sqladmin.googleapis.com",
    "pubsub.googleapis.com",
    "dataflow.googleapis.com",
    "aiplatform.googleapis.com",
    "artifactregistry.googleapis.com",
  ]
}
