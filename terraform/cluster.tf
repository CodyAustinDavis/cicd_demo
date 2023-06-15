## Do we need clusters in prod? 

## Yes! For prod troubleshooting, etc. and ensuring that clusters are governed

variable "cluster_name" {}
variable "cluster_autotermination_minutes" {}
variable "cluster_num_workers" {}
variable "cluster_data_security_mode" {}
variable "cluster_policy_id" {}

# Create the cluster with the "smallest" amount
# of resources allowed.
data "databricks_node_type" "smallest" {
  local_disk = true
  graviton = true
  photon_driver_capable = true
  photon_worker_capable = true
}

# Use the latest Databricks Runtime
# Long Term Support (LTS) version.
data "databricks_spark_version" "latest_lts" {
  long_term_support = true
}

resource "databricks_cluster" "this" {
  cluster_name            = var.cluster_name
  node_type_id            = data.databricks_node_type.smallest.id
  spark_version           = data.databricks_spark_version.latest_lts.id
  autotermination_minutes = var.cluster_autotermination_minutes
  num_workers             = var.cluster_num_workers
  data_security_mode      = var.cluster_data_security_mode
  policy_id = var.cluster_policy_id
  runtime_engine = "PHOTON"
  
}

output "cluster_url" {
 value = databricks_cluster.this.url
}