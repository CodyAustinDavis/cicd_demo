# Databricks notebook source
# MAGIC %pip install pytest

# COMMAND ----------

import pytest
import os
import sys

repo_name = "/unit_tests/"

# Get the path to this notebook, for example "/Workspace/Repos/{username}/{repo-name}".
notebook_path = "/Repos/cody.davis@databricks.com/cicd_demo/tests/unit_tests/run_unit_tests"

# Get the repo's root directory name.
repo_root = os.path.dirname(os.path.dirname(notebook_path))

# Prepare to run pytest from the repo.
os.chdir(f"/Workspace{repo_root}/{repo_name}")
print(os.getcwd())

# Skip writing pyc files on a readonly filesystem.
sys.dont_write_bytecode = True

# Run pytest.
retcode = pytest.main([".", "-v", "-p", "no:cacheprovider"])

# Fail the cell execution if there are any test failures.
assert retcode == 0, "The pytest invocation failed. See the log for details."
