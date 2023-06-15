variable "schema_admin_privileges" {
    type = list(string)
    default = ["ALL PRIVILEGES"]
}
variable "schema_user_privileges" {
    type = list(string)
    default = ["USE_SCHEMA", "EXECUTE", "SELECT"]
}


resource "databricks_grants" "iot_system" {
  depends_on = [ databricks_schema.iot_system ]
  schema = "${databricks_catalog.bu_catalog.name}.${databricks_schema.iot_system.name}"
  grant {
    principal  = data.databricks_group.schema_admins.display_name
    privileges = var.schema_admin_privileges
  }
  grant {
    principal  = data.databricks_group.schema_users.display_name
    privileges = var.schema_user_privileges
  }
}