# Databricks notebook source
dbutils.widgets.text("Entity Name", "")
dbutils.widgets.dropdown("Entity Mode", "user", ["user", "group"])

selected_entity = dbutils.widgets.get("Entity Name")

print(f"Running Access Analysis for {selected_entity}")

# COMMAND ----------

df_user = spark.sql(f"""SHOW GROUPS WITH USER `{selected_entity}`""")

df_user.createOrReplaceTempView("group_entity_of_user")

display(df_user)

# COMMAND ----------

df_all_entities = spark.sql(f"""WITH all_entities_of_user_or_group AS (
  SELECT '{selected_entity}' AS entity, 'user' AS entity_type
  UNION 
  SELECT name AS entity, 'group' AS entity_type FROM group_entity_of_user
)

SELECT * FROM all_entities_of_user_or_group
""")

df_all_entities.createOrReplaceTempView("all_entities")

# COMMAND ----------

# DBTITLE 1,Catalog Access
# MAGIC %sql
# MAGIC
# MAGIC SELECT * 
# MAGIC FROM main.information_schema.catalog_privileges cc
# MAGIC INNER JOIN all_entities ae ON cc.grantee = ae.entity
# MAGIC
# MAGIC

# COMMAND ----------

# DBTITLE 1,Explicit Schema Access
# MAGIC %sql
# MAGIC
# MAGIC SELECT catalog_name,
# MAGIC schema_name,
# MAGIC grantor,
# MAGIC cc.privilege_type
# MAGIC FROM main.information_schema.schema_privileges cc
# MAGIC INNER JOIN all_entities ae ON cc.grantee = ae.entity
# MAGIC WHERE inherited_from = 'NONE' AND cc.schema_name != 'information_schema'
# MAGIC ORDER BY cc.catalog_name, cc.schema_name

# COMMAND ----------

# DBTITLE 1,Inherited Access From Groups
# MAGIC %sql
# MAGIC
# MAGIC SELECT 
# MAGIC catalog_name,
# MAGIC schema_name,
# MAGIC grantor,
# MAGIC cc.privilege_type,
# MAGIC ae.entity AS EntityInheritedFrom,
# MAGIC ae.entity_type,
# MAGIC cc.inherited_from
# MAGIC FROM main.information_schema.schema_privileges cc
# MAGIC INNER JOIN all_entities ae ON cc.grantee = ae.entity
# MAGIC WHERE inherited_from != 'NONE' AND cc.schema_name != 'information_schema'
# MAGIC ORDER BY cc.catalog_name, cc.schema_name

# COMMAND ----------

# DBTITLE 1,Table Access
# MAGIC %sql
# MAGIC
# MAGIC SELECT * FROM main.information_schema.table_privileges cc
# MAGIC INNER JOIN all_entities ae ON cc.grantee = ae.entity

# COMMAND ----------

# DBTITLE 1,Table This user created
# MAGIC %sql
# MAGIC
# MAGIC SELECT table_catalog, 
# MAGIC table_schema, 
# MAGIC table_name, 
# MAGIC cc.last_altered,
# MAGIC cc.last_altered_by,
# MAGIC cc.created,
# MAGIC cc.storage_sub_directory
# MAGIC FROM main.information_schema.tables cc
# MAGIC INNER JOIN all_entities ae ON cc.table_owner = ae.entity
# MAGIC

# COMMAND ----------

# DBTITLE 1,Stale Tables this user created - Tables 1 month or older
# MAGIC %sql
# MAGIC
# MAGIC SELECT table_catalog, 
# MAGIC table_schema, 
# MAGIC table_name, 
# MAGIC cc.last_altered,
# MAGIC cc.last_altered_by,
# MAGIC cc.created,
# MAGIC cc.storage_sub_directory
# MAGIC FROM main.information_schema.tables cc
# MAGIC INNER JOIN all_entities ae ON cc.table_owner = ae.entity
# MAGIC WHERE cc.last_altered <= (current_timestamp() - INTERVAL 30 DAYS)
