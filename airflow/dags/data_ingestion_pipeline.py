"""
Main ETL DAG for Data Ingestion and Loading
Ingests data from API and loads to PostgreSQL ODS layer
"""
from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator
from airflow.providers.postgres.operators.postgres import PostgresOperator
from airflow.utils.task_group import TaskGroup
import json
import requests
import pandas as pd
from psycopg2 import connect
from dotenv import load_dotenv
import os

load_dotenv()

# Default arguments
default_args = {
    'owner': 'data_engineering',
    'retries': 2,
    'retry_delay': timedelta(minutes=5),
    'email_on_failure': False,
}

# DAG definition
dag = DAG(
    'data_ingestion_pipeline',
    default_args=default_args,
    description='End-to-end data ingestion and transformation pipeline',
    schedule_interval='@daily',
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=['data_engineering', 'ingestion'],
)

# Task functions
def fetch_earthquake_data():
    """
    Fetch earthquake data from USGS API
    https://earthquake.usgs.gov/fdsnws/event/1/
    """
    try:
        url = "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/all_day.geojson"
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        
        # Extract features
        features = data.get('features', [])
        
        # Transform to records
        records = []
        for feature in features:
            props = feature.get('properties', {})
            geometry = feature.get('geometry', {})
            
            record = {
                'event_id': feature.get('id'),
                'magnitude': props.get('mag'),
                'place': props.get('place'),
                'time': datetime.fromtimestamp(props.get('time', 0) / 1000),
                'latitude': geometry.get('coordinates', [None, None])[1],
                'longitude': geometry.get('coordinates', [None, None])[0],
                'depth': geometry.get('coordinates', [None, None, None])[2],
                'event_type': props.get('type'),
                'full_data': json.dumps(feature)
            }
            records.append(record)
        
        # Save to JSON for staging
        with open('/tmp/earthquake_data.json', 'w') as f:
            json.dump(records, f, indent=2, default=str)
        
        print(f"Fetched {len(records)} earthquake records")
        
        return {
            'records_count': len(records),
            'timestamp': datetime.now().isoformat()
        }
    
    except Exception as e:
        print(f"Error fetching earthquake data: {str(e)}")
        raise

def load_to_ods():
    """
    Load data from JSON to PostgreSQL ODS layer
    """
    try:
        # Read the data
        with open('/tmp/earthquake_data.json', 'r') as f:
            records = json.load(f)
        
        # Connect to PostgreSQL
        conn = connect(
            host=os.getenv('DB_HOST', 'postgres'),
            database=os.getenv('DB_NAME', 'datalakehouse'),
            user=os.getenv('DB_USER', 'datauser'),
            password=os.getenv('DB_PASSWORD', 'datapassword'),
            port=5432
        )
        cursor = conn.cursor()
        
        # Insert records
        insert_query = """
        INSERT INTO ods.raw_events 
        (event_id, event_type, event_data, source_system, ingested_at)
        VALUES (%s, %s, %s, %s, %s)
        ON CONFLICT (event_id) DO UPDATE SET
            event_data = EXCLUDED.event_data,
            ingested_at = EXCLUDED.ingested_at
        """
        
        for record in records:
            cursor.execute(insert_query, (
                record['event_id'],
                record['event_type'],
                json.dumps(record),
                'usgs_earthquake_api',
                datetime.now()
            ))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        print(f"Loaded {len(records)} records to ODS layer")
        
        return {'records_loaded': len(records)}
    
    except Exception as e:
        print(f"Error loading to ODS: {str(e)}")
        raise

def run_quality_checks():
    """
    Run data quality checks on ingested data
    """
    try:
        conn = connect(
            host=os.getenv('DB_HOST', 'postgres'),
            database=os.getenv('DB_NAME', 'datalakehouse'),
            user=os.getenv('DB_USER', 'datauser'),
            password=os.getenv('DB_PASSWORD', 'datapassword'),
            port=5432
        )
        cursor = conn.cursor()
        
        # Check 1: Not null checks
        cursor.execute("""
        SELECT COUNT(*) FROM ods.raw_events 
        WHERE event_id IS NULL OR event_type IS NULL
        """)
        null_count = cursor.fetchone()[0]
        
        # Check 2: Data freshness (records from last 24h)
        cursor.execute("""
        SELECT COUNT(*) FROM ods.raw_events 
        WHERE ingested_at > NOW() - INTERVAL '24 hours'
        """)
        fresh_count = cursor.fetchone()[0]
        
        # Check 3: Total record count
        cursor.execute("SELECT COUNT(*) FROM ods.raw_events")
        total_count = cursor.fetchone()[0]
        
        # Store quality results
        quality_results = {
            'null_violations': null_count,
            'fresh_records_24h': fresh_count,
            'total_records': total_count,
            'timestamp': datetime.now().isoformat()
        }
        
        if null_count > 0:
            print(f"WARNING: {null_count} records with null values")
        
        print(f"Quality checks: {quality_results}")
        
        cursor.close()
        conn.close()
        
        return quality_results
    
    except Exception as e:
        print(f"Error running quality checks: {str(e)}")
        raise

def log_lineage():
    """
    Log data lineage information
    """
    try:
        conn = connect(
            host=os.getenv('DB_HOST', 'postgres'),
            database=os.getenv('DB_NAME', 'datalakehouse'),
            user=os.getenv('DB_USER', 'datauser'),
            password=os.getenv('DB_PASSWORD', 'datapassword'),
            port=5432
        )
        cursor = conn.cursor()
        
        lineage_query = """
        INSERT INTO metadata.data_lineage 
        (source_system, source_table, target_table, transformation_type)
        VALUES (%s, %s, %s, %s)
        """
        
        cursor.execute(lineage_query, (
            'usgs_earthquake_api',
            'earthquake_data',
            'ods.raw_events',
            'ingestion'
        ))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        print("Lineage logged successfully")
        
    except Exception as e:
        print(f"Error logging lineage: {str(e)}")
        raise

# DAG tasks
with TaskGroup("data_ingestion", tooltip="Data ingestion phase") as ingestion_tg:
    
    fetch_data = PythonOperator(
        task_id='fetch_earthquake_data',
        python_callable=fetch_earthquake_data,
        doc='Fetch earthquake data from USGS API',
    )
    
    load_ods = PythonOperator(
        task_id='load_to_ods_layer',
        python_callable=load_to_ods,
        doc='Load data to PostgreSQL ODS layer',
    )
    
    fetch_data >> load_ods

with TaskGroup("quality_and_monitoring", tooltip="Quality checks and monitoring") as quality_tg:
    
    quality = PythonOperator(
        task_id='run_quality_checks',
        python_callable=run_quality_checks,
        doc='Run data quality validations',
    )
    
    lineage = PythonOperator(
        task_id='log_data_lineage',
        python_callable=log_lineage,
        doc='Log data lineage to metadata store',
    )
    
    quality >> lineage

dbt_run = BashOperator(
    task_id='dbt_run_transformations',
    bash_command='cd /dbt && dbt run --profiles-dir . || true',
    doc='Run dbt transformation models',
)

# Task dependencies
ingestion_tg >> quality_tg >> dbt_run
