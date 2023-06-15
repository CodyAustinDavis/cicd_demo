variable "schema_admins_display_name" {}
variable "schema_users_display_name" {}

data "databricks_group" "schema_admins" {
  display_name = var.schema_admins_display_name
}

data "databricks_group" "schema_users" {
  display_name = var.schema_users_display_name
}





