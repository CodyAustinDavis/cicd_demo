variable "DBX_HOST" {
    type = string
}

variable "DBX_TOKEN" {
    type = string
}

variable "databricks_connection_profile" {}


terraform {
  required_providers {
    databricks = {
      source = "databricks/databricks"
    }
    aws = {
      source = "hashicorp/aws"
    }
  }
}
## Use Environment variables so this can be run from GitHub Actions easier

provider "databricks" {
    #host=var.DBX_HOST
    #token=var.DBX_TOKEN
    profile=var.databricks_connection_profile
}