import json


## Usually config goes to a yaml or json file
## Ideally want to store alone
class Config():

  def __init__(self):

    ## Set up target tables, databases, checkpoint locations, table locations, parameters, data sources, etc. Permissions will be governed by UC and built by terraform
    self.config = {"dev": {"source_bucket": "dbfs:/FileStore/shared_uploads/cody.davis@databricks.com/IotDemo/dev/", 
                           "catalog": "cody_business_unit_dev", 
                           "target_database": "iot_system",
                           "notebook_params": {"StartOver": "yes"}},
                   "prod": {"source_bucket": "dbfs:/FileStore/shared_uploads/cody.davis@databricks.com/IotDemo/prod/", 
                            "catalog": "cody_business_unit_prod", 
                            "target_database": "iot_system",
                            "notebook_params": {"StartOver": "no"}}
                   }
    

  def get_conf(self):
    return self.config 