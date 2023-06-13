import json


## Usually config goes to a yaml or json file
## Ideally want to store alone
class Config():

  def __init__(self):

    ## Set up target tables, databases, checkpoint locations, table locations, parameters, data sources, etc. Permissions will be governed by UC and built by terraform
    self.config = {"dev": {"source_bucket": "s3://codydemos_dev/", "catalog": "cody_business_unit_dev", "target_database": "iot_system"},
                   "prod": {"source_bucket": "s3://cody_demos_prod/", "catalog": "cody_business_unit_prod", "target_database": "iot_system"}
                   }
    

  def get_conf(self):
    return self.config 