"""
Great Expectations configuration for data quality validation
"""

import json
from great_expectations.dataset import PandasDataset, SqlAlchemyDataset
from great_expectations import validate
import pandas as pd
from sqlalchemy import create_engine

# Connection configuration
DB_HOST = "postgres"
DB_USER = "datauser"
DB_PASSWORD = "datapassword"
DB_NAME = "datalakehouse"
DB_PORT = 5432

def create_connection():
    """Create database connection"""
    connection_string = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    return create_engine(connection_string)

def validate_raw_events():
    """
    Validate ODS raw events table
    """
    engine = create_connection()
    
    # Define expectations
    expectations = {
        "ge_suites": [
            {
                "name": "ods.raw_events",
                "expectations": [
                    {
                        "expectation_type": "expect_table_row_count_to_be_between",
                        "kwargs": {
                            "min_value": 0,
                            "max_value": 1000000
                        }
                    },
                    {
                        "expectation_type": "expect_column_to_exist",
                        "kwargs": {
                            "column": "event_id"
                        }
                    },
                    {
                        "expectation_type": "expect_column_values_to_not_be_null",
                        "kwargs": {
                            "column": "event_id"
                        }
                    },
                    {
                        "expectation_type": "expect_column_values_to_be_unique",
                        "kwargs": {
                            "column": "event_id"
                        }
                    },
                    {
                        "expectation_type": "expect_column_values_to_not_be_null",
                        "kwargs": {
                            "column": "event_type"
                        }
                    },
                    {
                        "expectation_type": "expect_column_values_to_not_be_null",
                        "kwargs": {
                            "column": "ingested_at"
                        }
                    },
                ]
            }
        ]
    }
    
    return expectations

def validate_staging_events():
    """
    Validate staging earthquake events
    """
    expectations = {
        "ge_suites": [
            {
                "name": "staging.stg_earthquake_events",
                "expectations": [
                    {
                        "expectation_type": "expect_column_values_to_not_be_null",
                        "kwargs": {
                            "column": "event_id"
                        }
                    },
                    {
                        "expectation_type": "expect_column_values_to_not_be_null",
                        "kwargs": {
                            "column": "magnitude"
                        }
                    },
                    {
                        "expectation_type": "expect_column_values_to_be_between",
                        "kwargs": {
                            "column": "magnitude",
                            "min_value": -2,
                            "max_value": 10
                        }
                    },
                    {
                        "expectation_type": "expect_column_values_to_not_be_null",
                        "kwargs": {
                            "column": "event_time"
                        }
                    },
                ]
            }
        ]
    }
    
    return expectations

def validate_earthquake_metrics():
    """
    Validate business metrics table
    """
    expectations = {
        "ge_suites": [
            {
                "name": "marts.fct_earthquake_metrics",
                "expectations": [
                    {
                        "expectation_type": "expect_column_values_to_not_be_null",
                        "kwargs": {
                            "column": "event_date"
                        }
                    },
                    {
                        "expectation_type": "expect_column_values_to_be_increasing",
                        "kwargs": {
                            "column": "event_count"
                        }
                    },
                    {
                        "expectation_type": "expect_column_values_to_be_between",
                        "kwargs": {
                            "column": "avg_magnitude",
                            "min_value": -2,
                            "max_value": 10
                        }
                    },
                ]
            }
        ]
    }
    
    return expectations

if __name__ == "__main__":
    print("Raw events expectations:")
    print(json.dumps(validate_raw_events(), indent=2))
    
    print("\nStaging events expectations:")
    print(json.dumps(validate_staging_events(), indent=2))
    
    print("\nMetrics expectations:")
    print(json.dumps(validate_earthquake_metrics(), indent=2))
