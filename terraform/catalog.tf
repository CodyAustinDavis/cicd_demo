variable "catalog_name" {}

resource "databricks_catalog" "bu_catalog" {
  name         = var.catalog_name
}