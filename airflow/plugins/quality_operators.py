"""
Airflow plugin for custom operators and utilities
"""

from airflow.models import BaseOperator
from airflow.utils.decorators import apply_defaults
from airflow.exceptions import AirflowException
import logging

logger = logging.getLogger(__name__)

class DataQualityOperator(BaseOperator):
    """
    Custom operator for running data quality checks
    """
    template_fields = ['schema', 'table']
    
    @apply_defaults
    def __init__(self, schema, table, checks, *args, **kwargs):
        super(DataQualityOperator, self).__init__(*args, **kwargs)
        self.schema = schema
        self.table = table
        self.checks = checks
    
    def execute(self, context):
        """Execute data quality checks"""
        logger.info(f"Running quality checks on {self.schema}.{self.table}")
        
        from quality.data_quality_monitor import DataQualityMonitor
        
        monitor = DataQualityMonitor()
        
        # Run checks based on type
        results = []
        for check in self.checks:
            check_type = check.get('type')
            
            if check_type == 'null_check':
                result = monitor.check_null_values(
                    f"{self.schema}.{self.table}",
                    check['column']
                )
            elif check_type == 'duplicate_check':
                result = monitor.check_duplicate_keys(
                    f"{self.schema}.{self.table}",
                    check['key_column']
                )
            elif check_type == 'range_check':
                result = monitor.check_value_range(
                    f"{self.schema}.{self.table}",
                    check['column'],
                    check['min_value'],
                    check['max_value']
                )
            elif check_type == 'freshness_check':
                result = monitor.check_data_freshness(
                    f"{self.schema}.{self.table}",
                    check['timestamp_column'],
                    check.get('max_age_hours', 24)
                )
            else:
                logger.warning(f"Unknown check type: {check_type}")
                continue
            
            results.append(result)
            
            # Fail if check failed
            if result['status'] == 'FAIL':
                logger.error(f"Quality check FAILED: {result}")
                if check.get('fail_on_error', True):
                    raise AirflowException(f"Quality check failed: {result}")
        
        logger.info(f"Completed {len(results)} quality checks")
        return results
