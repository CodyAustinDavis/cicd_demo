variable "DBX_HOST" {
    type = string
}

variable "DBX_TOKEN" {
    type = string
}

terraform {
    required_providers {
      source = "databricks/databricks"
    }
}

## Use Environment variables so this can be run from GitHub Actions easier

provider "databricks" {
    host=var.DBX_HOST
    token=var.DBX_TOKEN
  
}