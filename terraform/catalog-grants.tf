variable "catalog_admin_privileges" {}
variable "catalog_usage_privileges" {}
variable "catalog_admins_display_name" {}
variable "catalog_users_display_name" {}
variable default_admin_privileges {}

data "databricks_group" "catalog_admins" {
  display_name = var.catalog_admins_display_name
}

data "databricks_group" "catalog_users" {
  display_name = var.catalog_users_display_name
}

## For creating and governing access to new catalog
resource "databricks_grants" "catalog" {
  depends_on = [ databricks_catalog.bu_catalog ]
  catalog    = databricks_catalog.bu_catalog.name
  grant {
    principal  = data.databricks_group.catalog_admins.display_name
    privileges = var.catalog_admin_privileges
  }
  grant {
    principal  = data.databricks_group.catalog_users.display_name
    privileges = var.catalog_usage_privileges
  }
}