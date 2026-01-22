"""
Data Quality Monitoring Module
Runs and tracks data quality checks
"""

import logging
from datetime import datetime
from sqlalchemy import create_engine, text
import json
import os
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

class DataQualityMonitor:
    """Monitor and validate data quality"""
    
    def __init__(self):
        self.db_url = f"postgresql://{os.getenv('DB_USER', 'datauser')}:{os.getenv('DB_PASSWORD', 'datapassword')}@{os.getenv('DB_HOST', 'postgres')}:{os.getenv('DB_PORT', 5432)}/{os.getenv('DB_NAME', 'datalakehouse')}"
        self.engine = create_engine(self.db_url)
    
    def check_null_values(self, table_name, column_name):
        """Check for null values in a column"""
        with self.engine.connect() as conn:
            result = conn.execute(text(f"""
                SELECT COUNT(*) as null_count 
                FROM {table_name} 
                WHERE {column_name} IS NULL
            """))
            row = result.fetchone()
            null_count = row[0] if row else 0
            
            status = "PASS" if null_count == 0 else "FAIL"
            return {
                "check_type": "null_check",
                "table": table_name,
                "column": column_name,
                "null_count": null_count,
                "status": status
            }
    
    def check_duplicate_keys(self, table_name, key_column):
        """Check for duplicate keys"""
        with self.engine.connect() as conn:
            result = conn.execute(text(f"""
                SELECT COUNT(*) - COUNT(DISTINCT {key_column}) as duplicate_count
                FROM {table_name}
            """))
            row = result.fetchone()
            duplicate_count = row[0] if row else 0
            
            status = "PASS" if duplicate_count == 0 else "FAIL"
            return {
                "check_type": "duplicate_check",
                "table": table_name,
                "key_column": key_column,
                "duplicate_count": duplicate_count,
                "status": status
            }
    
    def check_value_range(self, table_name, column_name, min_val, max_val):
        """Check if values are within acceptable range"""
        with self.engine.connect() as conn:
            result = conn.execute(text(f"""
                SELECT 
                    COUNT(*) as total_count,
                    COUNT(CASE WHEN {column_name} < {min_val} OR {column_name} > {max_val} THEN 1 END) as out_of_range
                FROM {table_name}
                WHERE {column_name} IS NOT NULL
            """))
            row = result.fetchone()
            total = row[0] if row else 0
            out_of_range = row[1] if row else 0
            
            status = "PASS" if out_of_range == 0 else "FAIL"
            return {
                "check_type": "range_check",
                "table": table_name,
                "column": column_name,
                "min": min_val,
                "max": max_val,
                "total_count": total,
                "out_of_range_count": out_of_range,
                "status": status
            }
    
    def check_data_freshness(self, table_name, timestamp_column, max_age_hours=24):
        """Check if data is fresh (within max age)"""
        with self.engine.connect() as conn:
            result = conn.execute(text(f"""
                SELECT 
                    COUNT(*) as total_count,
                    COUNT(CASE WHEN {timestamp_column} > NOW() - INTERVAL '{max_age_hours} hours' THEN 1 END) as fresh_count
                FROM {table_name}
            """))
            row = result.fetchone()
            total = row[0] if row else 0
            fresh = row[1] if row else 0
            
            freshness_pct = (fresh / total * 100) if total > 0 else 0
            status = "PASS" if freshness_pct >= 80 else "FAIL"
            
            return {
                "check_type": "freshness_check",
                "table": table_name,
                "timestamp_column": timestamp_column,
                "max_age_hours": max_age_hours,
                "total_count": total,
                "fresh_count": fresh,
                "freshness_percentage": round(freshness_pct, 2),
                "status": status
            }
    
    def run_all_checks(self):
        """Run all quality checks"""
        checks = []
        
        # Raw events checks
        checks.append(self.check_null_values("ods.raw_events", "event_id"))
        checks.append(self.check_duplicate_keys("ods.raw_events", "event_id"))
        checks.append(self.check_data_freshness("ods.raw_events", "ingested_at", 24))
        
        # Store results
        self.store_quality_results(checks)
        
        return checks
    
    def store_quality_results(self, checks):
        """Store quality check results in database"""
        with self.engine.connect() as conn:
            for check in checks:
                conn.execute(text("""
                    INSERT INTO metadata.data_quality_checks
                    (table_name, check_type, check_name, status, details)
                    VALUES (:table, :type, :name, :status, :details)
                """), {
                    "table": check.get("table", check.get("table_name")),
                    "type": check["check_type"],
                    "name": f"{check['check_type']}_{check.get('column', check.get('key_column', ''))}",
                    "status": check["status"],
                    "details": json.dumps(check)
                })
            conn.commit()

if __name__ == "__main__":
    monitor = DataQualityMonitor()
    results = monitor.run_all_checks()
    
    print("Data Quality Check Results:")
    print(json.dumps(results, indent=2, default=str))
