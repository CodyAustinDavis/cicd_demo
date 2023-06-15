variable "schema_name" {}

resource "databricks_schema" "iot_system" {
  depends_on   = [ databricks_catalog.bu_catalog ]
  catalog_name = databricks_catalog.bu_catalog.name
  name         = var.schema_name
}