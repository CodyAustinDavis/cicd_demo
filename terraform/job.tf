variable "email_notifications_list" {
    type = list(string)
}


resource "databricks_job" "iot_system_pipeline" {
  name = "IoT System ETL Pipeline on UC"
  max_concurrent_runs = 1

schedule {
  quartz_cron_expression = "35 0 0 * * ?"
  timezone_id = "UTC"
}

tags = {
    Environment = "PROD"
    Managed = "TF_MANAGED"
}

git_source {
  url = "https://github.com/CodyAustinDavis/cicd_demo.git"
  provider = "gitHub"
  branch = "main" ## For development / testing build process, run everything on "DEV" and put DEV param into jobs and add an integration test
}

email_notifications {
  on_failure = var.email_notifications_list
}

  job_cluster {
    job_cluster_key = "PROD_CLUSTER_JOB"
    new_cluster {
      num_workers   = 2
      data_security_mode = "SINGLE_USER"
      spark_version = data.databricks_spark_version.latest_lts.id
      node_type_id  = data.databricks_node_type.smallest.id
    }
  }

  task {
    task_key = "Raw_To_Silver"
    job_cluster_key = "PROD_CLUSTER_JOB"
    notebook_task {
      notebook_path = "source/IotPipeline_Python"
      base_parameters = {
        Environment = "PROD"
      }
    }

  }



}