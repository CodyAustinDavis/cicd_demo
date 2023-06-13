# Databricks notebook source
# MAGIC %md
# MAGIC
# MAGIC <img src="https://databricks.com/wp-content/uploads/2019/08/Delta-Lake-Multi-Hop-Architecture-Bronze.png" >

# COMMAND ----------

# MAGIC %md
# MAGIC
# MAGIC ## Configs

# COMMAND ----------

# DBTITLE 1,Imports
from pyspark.sql.functions import *
from pyspark.sql.types import *
import uuid
from pyspark.sql.functions import udf

# COMMAND ----------

# DBTITLE 1,Import Config from repo
from config.config import *
from helpers.business_logic_functions import *

## You can manage imports / config using either repos or building python wheels / Java jar files.  Repos is much easier as it acts much more like a normal local development env for python DEVs

# COMMAND ----------

# DBTITLE 1,Define Environment Parameters
dbutils.widgets.dropdown("Environment", "DEV", ["PROD", "DEV"])

env = dbutils.widgets.get("Environment").lower()

conf = Config().config.get(env)

source_bucket = conf.get("source_bucket")

## You can make DEV/TEST always re-run the same test data set, but PROD never starts over
start_over = conf.get("notebook_params").get("StartOver")

database_name = str(conf.get("catalog")) + "." + str(conf.get("target_database"))

print(f"Env Configs: {conf}")
print(f"Start Over? : {start_over}")
print(f"Running pipeline in {env} on Database: {database_name}")

# COMMAND ----------

# DBTITLE 1,Set Database For Session  - This should all be governed in Terraform in PROD
spark.sql(f"""DROP DATABASE IF EXISTS {database_name} CASCADE;""")
spark.sql(f"""CREATE DATABASE IF NOT EXISTS {database_name};""")
spark.sql(f"""USE {database_name};""")

# COMMAND ----------

# MAGIC %md
# MAGIC
# MAGIC ## Key points: 
# MAGIC 1.  If in production, dev user should NOT have had access to run the above statement! Its a bad practice to create catalogs/databases in code, so:
# MAGIC 2. Do not allow create permissions in production on the catalog for databases and tables

# COMMAND ----------

# MAGIC %md 
# MAGIC
# MAGIC ## Access to read files in UC
# MAGIC
# MAGIC 1. Set up external locations in UC and allow user READ access to data source storage locations. 
# MAGIC
# MAGIC For example: "s3://oetrta/iotdemo/"

# COMMAND ----------

# DBTITLE 1,Set up parameters - Make Integration test path point to integration test bucket
## Set up source and checkpoints
## REPLACE WITH YOUR OWN PATHS

## This way when running integration test, its simply a config runtime switch!
file_source_location = conf.get("source_bucket") + "source_data/"
checkpoint_location_raw_to_bronze = conf.get("source_bucket") + f"checkpoints/RawToBronze/"
checkpoint_location_bronze_to_silver = conf.get("source_bucket") + f"checkpoints/BronzeToSilver/"
print("Now running Weather Data Streaming Service...")
print(f"...from source location {file_source_location}")
print(f"... with checkpoint location {checkpoint_location}")

# COMMAND ----------

# DBTITLE 1,Show source location
dbutils.fs.ls(file_source_location)

# COMMAND ----------

# DBTITLE 1,Start Over Checkpoint in ENV
if start_over == "yes":
  print("Removing Checkpoint and starting over!")
  dbutils.fs.rm(checkpoint_location_raw_to_bronze, recurse=True)
  dbutils.fs.rm(checkpoint_location_bronze_to_silver, recurse=True)

# COMMAND ----------

#### Register udf for generating UUIDs
uuidUdf= udf(lambda : str(uuid.uuid4()),StringType())

# COMMAND ----------

## Dont necessarily need to define schema all the time. Better to define schema for speed, but schema-on-read is better just by specifying columns in a select or copy into statement
weatherInputSensorSchema = StructType([StructField("Skip", StringType(), True),
                                      StructField("SkipResult", StringType(), True),
                                      StructField("SkipTable", StringType(), True),
                                      StructField("WindowAverageStartDateTime", TimestampType(), True),
                                      StructField("WindowAverageStopDateTime", TimestampType(), True),
                                      StructField("MeasurementDateTime", TimestampType(), True),
                                      StructField("SensorValue", DecimalType(), True),
                                      StructField("SensorUnitDescription", StringType(), True),
                                      StructField("SensorMeasurement", StringType(), True),
                                      StructField("SensorLocation", StringType(), True),
                                      StructField("Id", StringType(), True)]
                                     )

# COMMAND ----------

# MAGIC %md
# MAGIC
# MAGIC ## Read Stream

# COMMAND ----------

df_raw = (spark
        .readStream
        .option("header", "true")
        .option("inferSchema", "true")
        .schema(weatherInputSensorSchema) #infer
        .format("csv")
        .load(file_source_location) ## This will only work on a UC enabled cluster if that cluster has an IAM role directly or if the user has access via an external location
        .withColumn("Id", uuidUdf())
        .withColumn("InputFileName", input_file_name())
      )

# COMMAND ----------

# DBTITLE 1,Do ETL As needed on the readStream or read
##### Do ETL/Modelling as needed for products

## This is a function that transforms the data and needs to be tested via unit tests

df_cleaned = df_raw.transform(clean_raw_data)

# COMMAND ----------

#display(df_cleaned)

# COMMAND ----------

# DBTITLE 1,Write Stream to Bronze Table
#### Actually execute stream or file run with same logic!

(df_cleaned
 .writeStream
 .format("delta")
 .trigger(once=True) ## You can put this in the config by environment as well!
 .option("checkpointLocation", checkpoint_location_raw_to_bronze)
 .option("mergeSchema", "true")
 .toTable(f"{database_name}.Bronze_AllSensors_Simple")
)


# COMMAND ----------

# MAGIC %md
# MAGIC
# MAGIC # Bronze to Silver: Merge Upsert

# COMMAND ----------

# DBTITLE 1,Create Silver Target Table -- No need to specify target location. If you DO, then manage create of tables OUTSIDE code
spark.sql(f"""CREATE OR REPLACE TABLE {database_name}.Silver_AllSensors_Simple 
(
MeasurementDateTime TIMESTAMP,
SensorValue DECIMAL(10,0),
SensorUnitDescription STRING,
SensorMeasurement STRING,
SensorLocation STRING,
Id STRING,
InputFileName STRING
)
USING DELTA
PARTITIONED BY (SensorLocation, SensorMeasurement);
""")

# COMMAND ----------

# DBTITLE 1,Stream Bronze to Silver With Merge Using Delta
## This is an incremental load
bronze_all_sensors_df = spark.readStream.table(f"{database_name}.Bronze_AllSensors_Simple")

# COMMAND ----------

# DBTITLE 1,For each batch Logic - microBatch
def mergeFunction(inputDf, id):
  
  ##### SQL Version of Merge
  
  #from delta.tables import DeltaTable
  
  inputDf.createOrReplaceGlobalTempView("updates")
  
  spark.sql(f"""
  MERGE INTO {database_name}.Silver_AllSensors_Simple  AS target
  USING global_temp.updates AS source --This can be a select statement that is incremental by timestamp like USING (SELECT * FROM updates WHERE update_timetstamp >= (SELECT MAX(update_timestamp) FROM SilverTable)
  ON target.Id = source.Id -- Can also add any other SCD logic
  WHEN NOT MATCHED
  THEN INSERT *
  """)
  
  
  ##### Python/Scala Version of Merge in Streaming
  """
  deltaTable = DeltaTable.forName({database_name}.Silver_AllSensors_Simple )
  
  (deltaTable.alias("t")
    .merge(
      inputDf.alias("s"),
      "s.Id = t.Id")
    .whenMatched().updateAll()
    .whenNotMatched().insertAll()
    .execute()
  )
  """
  return

# COMMAND ----------

(bronze_all_sensors_df
 .writeStream
 .queryName(f"{database_name}.IotStreamUpsert")
 .trigger(once=True) #processingTime='15 seconds' 
 .option("checkpointLocation", checkpoint_location)
 .foreachBatch(mergeFunction)
 .start()
)

# COMMAND ----------

df_final = spark.sql(f"SELECT * FROM {database_name}.Silver_AllSensors_Simple")

display(df_final)

# COMMAND ----------

spark.sql(f"""OPTIMIZE {database_name}.Silver_AllSensors_Simple ZORDER BY (MeasurementDateTime)""")

# COMMAND ----------

# MAGIC %md
# MAGIC
# MAGIC ## Now how to get to prod?
# MAGIC
# MAGIC Thinking about
# MAGIC
# MAGIC 1. Table Creation - with proper governance and ownership
# MAGIC 2. Unit Testing
