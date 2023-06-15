# Databricks notebook source
# MAGIC %md
# MAGIC
# MAGIC # Overview:
# MAGIC
# MAGIC 1. Create Catalogs, Databases, Users and Groups for proper governance in UC
# MAGIC 2. Assign production catalogs to separate workspace, S3 location, and role
# MAGIC 3. Allocate permissions for PROD + DEV environment for various groups
# MAGIC 4. Create tables in catalogs (test access etc.)
# MAGIC 5. Define Cluster Policies to ensure non-credentialed access via UC ACLs
# MAGIC 6. Table Hive --> UC Migration Strategies
# MAGIC 7. CI/CD - Promote a pipeline developed in one catalog to a production job via terraform + Github Actions

# COMMAND ----------

# MAGIC %md
# MAGIC
# MAGIC ## Setting up Catalogs + Databases to Scale
# MAGIC
# MAGIC
# MAGIC ### Catalog: 
# MAGIC
# MAGIC 1. Ideally separate by business unit or large production system that utilizes multiple databases and can span across workspaces
# MAGIC
# MAGIC
# MAGIC ### Database:
# MAGIC
# MAGIC 1. Separate by need to govern user access within departments, large BUs, or use cases. i.e. development / test / prod databases, sandbox envs for users, etc. 
# MAGIC 2. Set locations at database level to avoid needing to specifiy location manually for every table if you want table control and organization in S3
# MAGIC

# COMMAND ----------

# MAGIC %sql
# MAGIC
# MAGIC --DROP CATALOG cody_business_unit IF EXISTS CASCADE;
# MAGIC CREATE CATALOG IF NOT EXISTS cody_business_unit_dev
# MAGIC MANAGED LOCATION 's3://<root_bucket>/cody_business_unit_dev';
# MAGIC
# MAGIC --OPTIONALLY DEFINE MANAGED LOCATION IN DIFFERENT S3 BUCKET
# MAGIC DROP CATALOG IF EXISTS cody_business_unit_prod CASCADE;
# MAGIC CREATE CATALOG IF NOT EXISTS cody_business_unit_prod;

# COMMAND ----------

# MAGIC %md
# MAGIC
# MAGIC ### Key Tip: It is important to manage locations of database and tables upfront and in a uniform way so that you can apply S3 lifecyle policies to buckets and remove stale data without having to search and ask where everything lives. 
# MAGIC
# MAGIC #### Live cycles policies can be done in a few layers:
# MAGIC
# MAGIC 1. SQL - DELETE / VACUUM statements - Delete and Vacuum stale data automatically (DLT / UC Managed Tables) or on a scheulde in Databricks
# MAGIC 2. S3 Lifecycle policies - Remove stale data outside of core database locations (so that you can manage databricks tables with SQL/UC) and prevent straggler tables/data from laying around: https://docs.aws.amazon.com/AmazonS3/latest/userguide/lifecycle-configuration-examples.html
# MAGIC
# MAGIC If you try to implement S3 lifecyle policies WITHOUT governing the specific location of production and development tables, people will come out of the woodworks complaining about broken tables! This way you dont have to search AND if people create objects outside of the governed locations, they are at their own risk (or not able to at all)

# COMMAND ----------

# MAGIC %sql
# MAGIC DROP CATALOG IF EXISTS cody_business_unit_prod CASCADE;
# MAGIC CREATE CATALOG IF NOT EXISTS cody_business_unit_prod;

# COMMAND ----------

# MAGIC %sql
# MAGIC USE CATALOG cody_business_unit_prod;

# COMMAND ----------

# MAGIC %md
# MAGIC
# MAGIC ## Create databases for core pipelines...

# COMMAND ----------

# MAGIC %sql
# MAGIC
# MAGIC CREATE DATABASE IF NOT EXISTS cody_business_unit_dev.dev
# MAGIC MANAGED LOCATION 's3://oet<root_bucket>rta/cody_business_unit_dev/dev';
# MAGIC

# COMMAND ----------

# MAGIC %md
# MAGIC
# MAGIC ##Creating separate catalogs for production products is good because you can fully isolate user editing any part of the data because 
# MAGIC
# MAGIC 1: Database/Catalog cannot be accessed even in Non-UC cluster if the catalog is assigned only to a prod workspace
# MAGIC 2: Admins can define distinct separate storage locations for production data and ensure NO cluster except for production roles can access data or metadata

# COMMAND ----------

# MAGIC %sql
# MAGIC CREATE DATABASE IF NOT EXISTS cody_business_unit_prod.test
# MAGIC MANAGED LOCATION 's3://<root_bucket>/cody_business_unit_prod/test';

# COMMAND ----------

# MAGIC %sql
# MAGIC
# MAGIC DROP DATABASE IF EXISTS cody_business_unit_prod.prod;
# MAGIC CREATE DATABASE IF NOT EXISTS cody_business_unit_prod.prod
# MAGIC MANAGED LOCATION 's3://<root_bucket>/cody_business_unit_prod/prod';

# COMMAND ----------

# MAGIC %md
# MAGIC
# MAGIC ### AND/OR create databases for specific products and teams!

# COMMAND ----------

# MAGIC %sql
# MAGIC --DROP DATABASE IF EXISTS prod_separate_product CASCADE;
# MAGIC CREATE DATABASE IF NOT EXISTS cody_business_unit_dev.iot_system
# MAGIC MANAGED LOCATION 's3://<root_bucket>/cody_business_unit_dev/prod_separate_product';

# COMMAND ----------

# MAGIC %md
# MAGIC
# MAGIC ## Let terraform create the production databases

# COMMAND ----------

# MAGIC %sql
# MAGIC --DROP DATABASE IF EXISTS prod_separate_product CASCADE;
# MAGIC CREATE DATABASE IF NOT EXISTS cody_business_unit_dev.iot_system
# MAGIC MANAGED LOCATION 's3://<root_bucket>/cody_business_unit_dev/prod_separate_product';

# COMMAND ----------

# DBTITLE 1,Define Dev Databases for Users
# MAGIC %sql
# MAGIC --DROP DATABASE IF EXISTS ds_development CASCADE;
# MAGIC CREATE DATABASE IF NOT EXISTS cody_business_unit_dev.ds_development
# MAGIC MANAGED LOCATION 's3://<root_bucket>/cody_business_unit_dev/ds_development';
# MAGIC
# MAGIC --DROP DATABASE IF EXISTS ds_development CASCADE;
# MAGIC CREATE DATABASE IF NOT EXISTS cody_business_unit_dev.dataeng_development
# MAGIC MANAGED LOCATION 's3://<root_bucket>/cody_business_unit_dev/dataeng_development';
# MAGIC
# MAGIC
# MAGIC --DROP DATABASE IF EXISTS ds_development CASCADE;
# MAGIC CREATE DATABASE IF NOT EXISTS cody_business_unit_dev.analytics_development
# MAGIC MANAGED LOCATION 's3://<root_bucket>/cody_business_unit_dev/analytics_development';

# COMMAND ----------

# MAGIC %md
# MAGIC
# MAGIC ## Defining a Managed Location:
# MAGIC
# MAGIC 1. Blocks access to it from UC enabled cluster except from ACL SQL permissions i.e. dbutils.fs.ls(<managed_location>) does not work

# COMMAND ----------

# MAGIC %sql
# MAGIC
# MAGIC SHOW DATABASES IN cody_business_unit;

# COMMAND ----------

# DBTITLE 1,Set ownership to an admin group that can manage
# MAGIC %sql
# MAGIC
# MAGIC --Group in UC must be created at account level and then assigned to a workspace for them to own UC objects)
# MAGIC
# MAGIC DESCRIBE CATALOG cody_business_unit_dev;
# MAGIC ALTER CATALOG cody_business_unit_dev OWNER TO `dataengineers`;

# COMMAND ----------

# MAGIC %sql
# MAGIC
# MAGIC DESCRIBE CATALOG cody_business_unit_dev

# COMMAND ----------

# MAGIC %md
# MAGIC
# MAGIC ### Lets Allocate groups to these databases and tables
# MAGIC
# MAGIC 1. analysts
# MAGIC 2. dataengineers
# MAGIC 3. datascientists

# COMMAND ----------

# MAGIC %md
# MAGIC
# MAGIC ## Key Tips: Generally, it is best to grant ownership of databases and tables to specific groups, especially in productions to manage personnel changes or other risks

# COMMAND ----------

# DBTITLE 1,Allow Groups to Manage their own sandboxes
# MAGIC %sql
# MAGIC ALTER DATABASE cody_business_unit_dev.dataeng_development OWNER TO `dataengineers`;
# MAGIC ALTER DATABASE cody_business_unit_dev.analytics_development OWNER TO `analysts`;
# MAGIC ALTER DATABASE cody_business_unit_dev.ds_development OWNER TO `datascientists`;

# COMMAND ----------

# DBTITLE 1,Change back owner to me just for demo
# MAGIC %sql
# MAGIC
# MAGIC ALTER CATALOG cody_business_unit_dev OWNER TO `cody.davis@databricks.com`; --just so I can do the demo, lets pretend I am in the data engineers group
# MAGIC ALTER DATABASE cody_business_unit_dev.dataeng_development OWNER TO `cody.davis@databricks.com`;
# MAGIC ALTER DATABASE cody_business_unit_dev.analytics_development OWNER TO `cody.davis@databricks.com`;
# MAGIC ALTER DATABASE cody_business_unit_dev.ds_development OWNER TO `cody.davis@databricks.com`;

# COMMAND ----------

# DBTITLE 1,Create any other managed sandboxes for others to share 
# MAGIC %sql
# MAGIC
# MAGIC --let this be managed for easy discovery and clean up
# MAGIC CREATE DATABASE cody_business_unit_dev.sandbox;

# COMMAND ----------

# DBTITLE 1,Set up access to a shared dev database
# MAGIC %sql
# MAGIC
# MAGIC GRANT USAGE ON SCHEMA cody_business_unit_dev.sandbox TO `dataengineers`;
# MAGIC GRANT USAGE ON SCHEMA cody_business_unit_dev.sandbox TO `analysts`;
# MAGIC GRANT USAGE ON SCHEMA cody_business_unit_dev.sandbox TO `datascientists`;
# MAGIC
# MAGIC
# MAGIC GRANT CREATE ON SCHEMA cody_business_unit_dev.sandbox TO `dataengineers`;
# MAGIC GRANT CREATE ON SCHEMA cody_business_unit_dev.sandbox TO `analysts`;
# MAGIC GRANT CREATE ON SCHEMA cody_business_unit_dev.sandbox TO `datascientists`;
# MAGIC
# MAGIC GRANT SELECT ON SCHEMA cody_business_unit_dev.sandbox TO `dataengineers`;
# MAGIC GRANT SELECT ON SCHEMA cody_business_unit_dev.sandbox TO `analysts`;
# MAGIC GRANT SELECT ON SCHEMA cody_business_unit_dev.sandbox TO `datascientists`;
# MAGIC
# MAGIC GRANT EXECUTE ON SCHEMA cody_business_unit_dev.sandbox TO `dataengineers`;
# MAGIC GRANT EXECUTE ON SCHEMA cody_business_unit_dev.sandbox TO `analysts`;
# MAGIC GRANT EXECUTE ON SCHEMA cody_business_unit_dev.sandbox TO `datascientists`;
# MAGIC
# MAGIC GRANT MODIFY ON SCHEMA cody_business_unit_dev.sandbox TO `dataengineers`;
# MAGIC GRANT MODIFY ON SCHEMA cody_business_unit_dev.sandbox TO `analysts`;
# MAGIC GRANT MODIFY ON SCHEMA cody_business_unit_dev.sandbox TO `datascientists`;

# COMMAND ----------

# MAGIC %md
# MAGIC
# MAGIC ## What if a team needs access to read raw files from a specific location?

# COMMAND ----------

# MAGIC %md
# MAGIC
# MAGIC ## Key Tips: 
# MAGIC
# MAGIC 1. There are <b> external locations </b> and <b> storage credentials</b>. In general, it is best practices to associate a storage credential with a external location, and then give access only to the external location. 
# MAGIC
# MAGIC https://docs.databricks.com/data-governance/unity-catalog/manage-external-locations-and-credentials.html#manage-storage-credentials

# COMMAND ----------

# DBTITLE 1,How to give users permission to read and write raw files from specific locations with UC managed credentials
# MAGIC %sql
# MAGIC
# MAGIC -- Give them access to a stoarge location and a storage credential
# MAGIC
# MAGIC GRANT READ FILES ON EXTERNAL LOCATION  oetrta TO `dataengineers`;
# MAGIC GRANT WRITE FILES ON EXTERNAL LOCATION oetrta TO `dataengineers`;

# COMMAND ----------

# MAGIC %md
# MAGIC
# MAGIC ## Now develop some tables!

# COMMAND ----------

# MAGIC %md
# MAGIC
# MAGIC ## Elements of Migration
# MAGIC
# MAGIC 1. Data sources - Does the way the pipelines read data in need to change?
# MAGIC 2. Data Tables (metadata and underlying) - How to the tables need to change (i.e. Location, table version, ACLS)
# MAGIC 3. Data State - How to we track the state of the data from one table to the new. How do we manage that?
# MAGIC 4. Code References - How and when do we change the code references from the code to new tables?
# MAGIC 5. Permissions - How to we assign permissions now that we are in UC (terraform example)

# COMMAND ----------

# DBTITLE 1,Migrate from this Hive Metastore
# MAGIC %sql
# MAGIC
# MAGIC SHOW TABLES IN hive_metastore.codydemos

# COMMAND ----------

# DBTITLE 1,Option 1: CTAS  - Easiest Pipeline ever, and most simple way to migrate to UC!
# MAGIC %sql
# MAGIC USE cody_business_unit_dev.dataeng_development;
# MAGIC
# MAGIC -- Risks / Cons: Physically moves all the data
# MAGIC -- 1. Can do this with either managed or external HMS tables
# MAGIC -- 2. Can specific NEW MANAGED LOCATION as well even if migrating from DBFS (managed HMS)
# MAGIC
# MAGIC --DROP TABLE IF EXISTS cody_business_unit_dev.dataeng_development.bronze_staging_all_sensors;
# MAGIC
# MAGIC CREATE OR REPLACE TABLE cody_business_unit_dev.dataeng_development.bronze_staging_all_sensors
# MAGIC LOCATION 's3://<root_bucket>/cody_business_unit_dev/dataeng_development/tables/bronze_staging_all_sensors'
# MAGIC AS
# MAGIC SELECT * FROM hive_metastore.codydemos.bronze_staging_all_sensors
# MAGIC ;

# COMMAND ----------

# MAGIC %sql
# MAGIC -- Created Managed Location Version
# MAGIC CREATE OR REPLACE TABLE cody_business_unit_dev.dataeng_development.bronze_staging_all_sensors_managed
# MAGIC AS
# MAGIC SELECT * FROM hive_metastore.codydemos.bronze_staging_all_sensors
# MAGIC ;

# COMMAND ----------

# DBTITLE 1,Option 2: Create Table Like - EXTERNAL TABLES ONLY
# MAGIC %sql
# MAGIC
# MAGIC CREATE TABLE cody_business_unit_dev.dataeng_development.bronze_staging_all_sensors_external_old_location LIKE hive_metastore.codydemos.bronze_staging_all_sensors COPY LOCATION;
# MAGIC ALTER TABLE cody_business_unit_dev.dataeng_development.bronze_staging_all_sensors_external_old_location OWNER TO `cody.davis@databricks.com`;
# MAGIC ALTER TABLE cody_business_unit_dev.dataeng_development.bronze_staging_all_sensors_external_old_location SET TBLPROPERTIES ('upgraded_to' = 'cody_business_unit_dev.dataeng_development.bronze_staging_all_sensors_external_old_location');
# MAGIC

# COMMAND ----------

# MAGIC %md
# MAGIC
# MAGIC ## Now lets build a pipeline in this environment!
# MAGIC
# MAGIC ### Up Next:
# MAGIC
# MAGIC 1. Set up Cluster Policies with this UC environment
# MAGIC 2. Create a development process to publish jobs and use production/dev catalog 

# COMMAND ----------

# MAGIC %sql
# MAGIC
# MAGIC SELECT * FROM hive_metastore.codydemos
