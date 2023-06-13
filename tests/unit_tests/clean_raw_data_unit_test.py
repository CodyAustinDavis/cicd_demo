
import pyspark
from helpers.business_logic_functions import clean_raw_data
from pyspark.sql.functions import *
from pyspark.sql.types import *
import pytest ## pip install globally or on test cluster via terraform
from pyspark.sql import SparkSession
from pyspark.sql.types import StructType, StructField, IntegerType, FloatType, StringType

# Because this file is not a Databricks notebook, you
# must create a Spark session. Databricks notebooks
# create a Spark session for you by default.
spark = SparkSession.builder \
                    .appName('unit-tests') \
                    .getOrCreate()

## Define tests
def test_clean_raw_data():
  
  y = [("#default", "_results", None, None, None, None, None, "_field", "_measurement", "location", "0cd35620-51d5-4825-9239-96d7c56f4549", ""),(None, None, 0, "1920-03-05 22:10:01", "2020-03-0522:10:01", "2019-08-17T00:00:00", "82.01", "degress", "average_temperature", "coyote_creek", "f0f4b49d-a319-4031-9d08-bd99da9b4c1b", "")]


  testweatherInputSensorSchema = StructType([StructField("Skip", StringType(), True),
                                          StructField("SkipResult", StringType(), True),
                                          StructField("SkipTable", StringType(), True),
                                          StructField("WindowAverageStartDateTime", StringType(), True),
                                          StructField("WindowAverageStopDateTime", StringType(), True),
                                          StructField("MeasurementDateTime", StringType(), True),
                                          StructField("SensorValue", StringType(), True),
                                          StructField("SensorUnitDescription", StringType(), True),
                                          StructField("SensorMeasurement", StringType(), True),
                                          StructField("SensorLocation", StringType(), True),
                                          StructField("Id", StringType(), True),
                                          StructField("InputFileName", StringType(), True)]
                                        )
  
  z = spark.createDataFrame(y, schema=testweatherInputSensorSchema)

  final_count = z.transform(clean_raw_data).count()

  assert final_count == 1



