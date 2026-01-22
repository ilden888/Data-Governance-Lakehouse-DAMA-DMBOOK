"""
dbt Transformation DAG
Runs dbt models to transform ODS data to staging, ODS normalized, and marts
"""
from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.operators.python import PythonOperator
import os

default_args = {
    'owner': 'analytics_engineering',
    'retries': 2,
    'retry_delay': timedelta(minutes=5),
}

dag = DAG(
    'dbt_transformation_pipeline',
    default_args=default_args,
    description='dbt transformation and modeling pipeline',
    schedule_interval='@daily',
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=['dbt', 'transformation'],
)

# dbt tasks
dbt_parse = BashOperator(
    task_id='dbt_parse',
    bash_command='cd /dbt && dbt parse || true',
)

dbt_debug = BashOperator(
    task_id='dbt_debug',
    bash_command='cd /dbt && dbt debug || true',
)

dbt_staging = BashOperator(
    task_id='dbt_run_staging',
    bash_command='cd /dbt && dbt run --select path:models/staging/ || true',
)

dbt_ods = BashOperator(
    task_id='dbt_run_ods',
    bash_command='cd /dbt && dbt run --select path:models/ods/ || true',
)

dbt_marts = BashOperator(
    task_id='dbt_run_marts',
    bash_command='cd /dbt && dbt run --select path:models/marts/ || true',
)

dbt_test = BashOperator(
    task_id='dbt_test_all',
    bash_command='cd /dbt && dbt test || true',
)

dbt_docs = BashOperator(
    task_id='dbt_generate_docs',
    bash_command='cd /dbt && dbt docs generate || true',
)

# Task dependencies
dbt_parse >> dbt_debug
dbt_debug >> dbt_staging
dbt_staging >> dbt_ods
dbt_ods >> dbt_marts
dbt_marts >> [dbt_test, dbt_docs]
