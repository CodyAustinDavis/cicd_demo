from pyspark.sql.functions import *
from pyspark.sql import DataFrame


def clean_raw_data(df: DataFrame) -> DataFrame:
  df_cleaned = (df.filter((col("SensorValue").isNotNull())) 
              .drop("Skip", "SkipResult", "SkipTable")
              )
  
  return df_cleaned