# Data Dictionary

Complete reference for all datasets, tables, and columns in the Data Governance Lakehouse.

---

## Overview

| Layer | Schema | Purpose | Materialization |
|-------|--------|---------|-----------------|
| Bronze | ods | Raw ingested data | Table |
| Silver | staging | Cleaned, typed data | View |
| Gold | marts | Business-ready aggregations | Table |
| Metadata | metadata | Governance tracking | Table |

---

## BRONZE Layer (ODS - Operational Data Store)

### Table: ods.raw_events

**Purpose:** Store raw, unmodified event data from source systems

**Materialization:** Table (Heap)

**Update Strategy:** Upsert (Insert or Update on conflict)

**Partitioning:** None (can add by ingested_at for large volumes)

**Indexes:**
- `idx_ods_event_id` on `event_id` (UNIQUE)
- `idx_ods_event_type` on `event_type`
- `idx_ods_ingested_at` on `ingested_at`

| Column | Type | Nullable | Key | Description |
|--------|------|----------|-----|-------------|
| id | SERIAL | NO | PK | Auto-increment primary key |
| event_id | VARCHAR(255) | NO | UK | Unique event identifier from source |
| event_type | VARCHAR(100) | NO | | Type of event (earthquake, aftershock, etc.) |
| event_data | JSONB | NO | | Complete raw event data in JSON format |
| source_system | VARCHAR(100) | NO | | Source system identifier (usgs_earthquake_api) |
| ingested_at | TIMESTAMP | NO | | When record was ingested |
| processed_at | TIMESTAMP | YES | | When record was processed |

**Sample Data:**
```json
{
  "event_id": "us70001abc",
  "event_type": "earthquake",
  "event_data": {
    "magnitude": 5.2,
    "place": "10 km NE of Parkfield, CA",
    "latitude": 35.891,
    "longitude": -120.425,
    "depth": 8.3,
    "time": "2024-01-15T14:30:00Z"
  },
  "source_system": "usgs_earthquake_api",
  "ingested_at": "2024-01-15T14:35:22Z"
}
```

**Quality Rules:**
- `event_id` must be NOT NULL
- `event_id` must be UNIQUE
- `event_type` must be NOT NULL
- `ingested_at` must be recent (< 24 hours)

**Refresh Schedule:** Daily at 02:00 UTC

**Volume Characteristics:**
- Expected daily rows: 100-1,000
- Annual growth: ~100K-400K rows/year
- Data retention: 3+ years (configurable)

**Owner:** Data Engineering Team

---

## SILVER Layer (Staging & Normalized)

### Model: staging.stg_earthquake_events

**Purpose:** Cleaned, typed, and validated earthquake events

**Materialization:** View (on ODS raw data)

**Depends On:** ods.raw_events

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| event_id | VARCHAR(255) | NO | Unique event identifier |
| event_type | VARCHAR(100) | NO | Type of seismic event |
| magnitude | FLOAT | NO | Richter scale magnitude |
| place | VARCHAR(500) | YES | Geographic location description |
| latitude | FLOAT | NO | Latitude coordinate |
| longitude | FLOAT | NO | Longitude coordinate |
| depth | FLOAT | NO | Depth in kilometers |
| event_time | TIMESTAMP | NO | Original event timestamp |
| ingested_at | TIMESTAMP | NO | Ingestion timestamp |
| dbt_loaded_at | TIMESTAMP | NO | dbt transformation timestamp |

**Transformation Logic:**
```sql
-- JSON extraction and type casting
magnitude = CAST(event_data->>'magnitude' AS FLOAT)
place = event_data->>'place'
latitude = CAST(event_data->>'latitude' AS FLOAT)
longitude = CAST(event_data->>'longitude' AS FLOAT)
depth = CAST(event_data->>'depth' AS FLOAT)
event_time = CAST(event_data->>'time' AS TIMESTAMP)
```

**Quality Rules (dbt Tests):**
```yaml
- unique: event_id
- not_null: event_id
- not_null: magnitude
- dbt_utils.accepted_values:
    values: ['earthquake', 'aftershock', 'explosion', 'other']
    column: event_type
```

**Owner:** Data Engineering Team

---

### Model: ods.dim_earthquake_events

**Purpose:** Normalized dimension table for earthquake events

**Materialization:** Table

**Depends On:** staging.stg_earthquake_events

**Schema:**
| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| event_sk | VARCHAR(32) | NO | Surrogate key (MD5 hash of event_id) |
| event_id | VARCHAR(255) | NO | Natural key from source |
| event_type | VARCHAR(100) | NO | Type of event |
| magnitude | FLOAT | NO | Earthquake magnitude |
| place | VARCHAR(500) | YES | Location description |
| latitude | FLOAT | NO | Latitude coordinate |
| longitude | FLOAT | NO | Longitude coordinate |
| depth | FLOAT | NO | Depth in kilometers |
| event_time | TIMESTAMP | NO | Event occurrence time |
| load_date | DATE | NO | Date dimension table was loaded |
| load_timestamp | TIMESTAMP | NO | Timestamp dimension table was loaded |
| ingested_at | TIMESTAMP | NO | Original ingestion time |

**Indexes:**
- `idx_dim_event_id` on `event_id` (UNIQUE)
- `idx_dim_event_time` on `event_time`
- `idx_dim_magnitude` on `magnitude`

**Slowly Changing Dimensions (SCD):**
- Type 1: Overwrite attributes (overwrite event_type, place, etc.)
- Type 2 Ready: Can add `valid_from`, `valid_to` for historical tracking

**Owner:** Data Engineering Team

---

## GOLD Layer (Data Marts)

### Model: marts.fct_earthquake_metrics

**Purpose:** Business-ready aggregated earthquake metrics for analytics

**Materialization:** Table

**Depends On:** ods.dim_earthquake_events

**Grain:** Daily aggregation by event_type and magnitude_category

**Schema:**
| Column | Type | Nullable | Description | Business Logic |
|--------|------|----------|-------------|-----------------|
| event_date | DATE | NO | Aggregation date | |
| event_type | VARCHAR(100) | YES | Type of seismic event | |
| magnitude_category | VARCHAR(20) | NO | Magnitude classification | Micro, Minor, Light, Moderate, Strong, Major, Great |
| event_count | INTEGER | NO | Number of events | COUNT(*) |
| avg_magnitude | FLOAT | YES | Average magnitude | AVG(magnitude) |
| max_magnitude | FLOAT | YES | Maximum magnitude | MAX(magnitude) |
| min_magnitude | FLOAT | YES | Minimum magnitude | MIN(magnitude) |
| distinct_locations | INTEGER | NO | Unique geographic locations | COUNT(DISTINCT place) |
| metric_timestamp | TIMESTAMP | NO | When metric was calculated | CURRENT_TIMESTAMP |

**Partitioning:** Recommended by `event_date` for large volumes

**Materialization Strategy:**
- Full refresh daily
- Only includes events from last 365 days
- Aggregated at midnight UTC

**Business Rules:**
```
Magnitude Categories:
- Micro: magnitude < 2
- Minor: 2 ≤ magnitude < 4
- Light: 4 ≤ magnitude < 5
- Moderate: 5 ≤ magnitude < 6
- Strong: 6 ≤ magnitude < 7
- Major: 7 ≤ magnitude < 8
- Great: magnitude ≥ 8
```

**Quality Tests:**
- `event_count` is NOT NULL
- `event_count` ≥ 0
- `avg_magnitude` is between -2 and 10
- `event_date` is NOT NULL

**BI Usage:**
- Metabase Dashboard: Earthquake Analytics
- Filters: By event_type, magnitude_category, date range
- Charts: Time series, distribution, heatmaps

**Expected Metrics:**
- Rows per day: 10-100 (depending on event distribution)
- Typical materialization time: < 5 minutes
- Data retention: 3+ years

**Owner:** Analytics Engineering Team

**SLA:**
- Freshness: Daily (ideally < 5 minutes after midnight UTC)
- Availability: 99.9%
- Row count anomaly threshold: ±50% from 30-day average

---

## METADATA Layer

### Table: metadata.data_lineage

**Purpose:** Track data transformations and dependencies

| Column | Type | Description |
|--------|------|-------------|
| id | SERIAL | Primary key |
| source_system | VARCHAR(255) | Source system identifier |
| source_table | VARCHAR(255) | Source table/dataset name |
| target_table | VARCHAR(255) | Target table/dataset name |
| transformation_type | VARCHAR(50) | Type: ingestion, transformation, aggregation, etc. |
| created_at | TIMESTAMP | Record creation time |
| updated_at | TIMESTAMP | Last update time |

**Example Lineage:**
```
USGS API → ods.raw_events (ingestion)
ods.raw_events → staging.stg_earthquake_events (transformation)
staging.stg_earthquake_events → ods.dim_earthquake_events (transformation)
ods.dim_earthquake_events → marts.fct_earthquake_metrics (aggregation)
marts.fct_earthquake_metrics → Metabase (visualization)
```

---

### Table: metadata.data_quality_checks

**Purpose:** Store quality check results and history

| Column | Type | Description |
|--------|------|-------------|
| id | SERIAL | Primary key |
| table_name | VARCHAR(255) | Table being checked |
| check_type | VARCHAR(100) | null_check, duplicate_check, range_check, freshness_check |
| check_name | VARCHAR(255) | Descriptive check name |
| status | VARCHAR(50) | PASS or FAIL |
| checked_at | TIMESTAMP | When check was run |
| details | JSONB | Detailed results as JSON |

**Query Quality History:**
```sql
SELECT 
  table_name,
  check_type,
  COUNT(CASE WHEN status = 'FAIL' THEN 1 END) as failure_count,
  COUNT(*) as total_checks,
  ROUND(100.0 * COUNT(CASE WHEN status = 'PASS' THEN 1 END) / COUNT(*), 2) as pass_rate
FROM metadata.data_quality_checks
WHERE checked_at >= CURRENT_DATE - INTERVAL '30 days'
GROUP BY 1, 2
ORDER BY pass_rate ASC;
```

---

### Table: metadata.dataset_ownership

**Purpose:** Track dataset ownership for governance

| Column | Type | Description |
|--------|------|-------------|
| id | SERIAL | Primary key |
| dataset_name | VARCHAR(255) | Full table path |
| owner_name | VARCHAR(255) | Person or team name |
| owner_email | VARCHAR(255) | Contact email |
| last_updated | TIMESTAMP | When ownership record was updated |

**Current Assignments:**
```
ods.raw_events → Data Engineering Team → data-eng@company.com
staging.stg_earthquake_events → Data Engineering Team → data-eng@company.com
ods.dim_earthquake_events → Data Engineering Team → data-eng@company.com
marts.fct_earthquake_metrics → Analytics Engineering Team → analytics-eng@company.com
```

---

## Data Quality Metrics

### Monthly Quality Score

```sql
WITH daily_checks AS (
  SELECT 
    DATE(checked_at) as check_date,
    COUNT(CASE WHEN status = 'PASS' THEN 1 END)::FLOAT / 
    COUNT(*) * 100 as daily_pass_rate
  FROM metadata.data_quality_checks
  WHERE checked_at >= CURRENT_DATE - INTERVAL '30 days'
  GROUP BY 1
)
SELECT 
  DATE_TRUNC('month', check_date)::DATE as month,
  ROUND(AVG(daily_pass_rate), 2) as avg_pass_rate,
  MIN(daily_pass_rate) as min_daily_rate,
  MAX(daily_pass_rate) as max_daily_rate
FROM daily_checks
GROUP BY 1;
```

---

## Access Matrix

| Role | ods.* | staging.* | marts.* | metadata.* |
|------|-------|-----------|---------|-----------|
| Data Engineer | SELECT, INSERT, UPDATE, DELETE | SELECT, INSERT, UPDATE, DELETE | SELECT, INSERT, UPDATE, DELETE | SELECT, INSERT |
| Analyst | SELECT | SELECT | SELECT | SELECT |
| BI Tool (Metabase) | SELECT | SELECT | SELECT | - |
| Public | - | - | - | - |

---

## Refresh & SLA

| Dataset | Layer | Materialization | Refresh | SLA |
|---------|-------|-----------------|---------|-----|
| ods.raw_events | Bronze | Daily full load | 02:00 UTC | Fresh < 24h |
| stg_earthquake_events | Silver | Real-time view | On query | N/A |
| dim_earthquake_events | Silver | After raw load | 02:30 UTC | Fresh < 24h |
| fct_earthquake_metrics | Gold | Daily aggregation | 03:00 UTC | Fresh < 24h, 99.9% avail |

---

## Common Queries

### 1. Recent Earthquakes
```sql
SELECT 
  event_date,
  magnitude_category,
  event_count,
  avg_magnitude
FROM marts.fct_earthquake_metrics
WHERE event_date >= CURRENT_DATE - INTERVAL '7 days'
ORDER BY event_date DESC;
```

### 2. Quality Status
```sql
SELECT 
  table_name,
  status,
  COUNT(*) as check_count,
  MAX(checked_at) as last_check
FROM metadata.data_quality_checks
WHERE checked_at >= CURRENT_DATE
GROUP BY 1, 2;
```

### 3. Data Lineage Impact
```sql
SELECT 
  source_table,
  target_table,
  transformation_type,
  updated_at
FROM metadata.data_lineage
WHERE source_table = 'ods.raw_events'
ORDER BY updated_at DESC;
```

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2024-01-20 | Initial data dictionary |
| 1.1 | 2024-02-01 | Added quality metrics |
| 1.2 | 2024-03-15 | Added lineage tracking |

---

## Contact

**Data Owner Questions:** data-eng@company.com  
**Quality Issues:** quality-team@company.com  
**Access Requests:** datalake-access@company.com
