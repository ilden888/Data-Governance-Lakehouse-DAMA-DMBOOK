# Data Governance Framework

## Governance Domains

### 1. Data Architecture
Defines how data flows through the organization and how systems integrate.

**Implementation:**
- Lakehouse architecture with three-tier model
- Clear separation: Raw (Bronze) → Cleaned (Silver) → Analytics (Gold)
- Metadata repository for cataloging

**Key Decisions:**
- PostgreSQL for DWH (structured, ACID-compliant)
- MinIO for data lake (scalable object storage)
- dbt for transformations (version-controlled SQL)

---

### 2. Data Modeling & Design
Establishes standards for how data is structured and organized.

**Dimensional Models:**
- Facts: `fct_earthquake_metrics` (quantifiable events)
- Dimensions: `dim_earthquake_events` (attributes)
- Slowly Changing Dimensions (SCD) support ready

**Naming Conventions:**
- Staging: `stg_*`
- ODS: `dim_*`, `fact_*`
- Marts: `fct_*` (facts), `dim_*` (dimensions)

**Relationships:**
```
USGS API
  │
  └─► ods.raw_events
       │
       └─► staging.stg_earthquake_events
            │
            └─► ods.dim_earthquake_events
                 │
                 └─► marts.fct_earthquake_metrics
                      │
                      └─► Metabase (BI)
```

---

### 3. Data Quality

**Quality Checks:**

| Check Type | Implementation | Frequency |
|-----------|-----------------|-----------|
| Schema Validation | dbt test | Daily |
| Null Checks | Great Expectations | Daily |
| Uniqueness | Primary keys, unique constraints | On insert |
| Range Validation | Column checks | Daily |
| Referential Integrity | Foreign keys | Daily |
| Freshness | Timestamp checks | Hourly |
| Volume Anomalies | Row count trending | Daily |

**Quality Framework:**
```python
from quality.data_quality_monitor import DataQualityMonitor

monitor = DataQualityMonitor()
results = monitor.run_all_checks()
```

---

### 4. Metadata Management

**Metadata Captured:**

1. **Technical Metadata**
   - Table structures
   - Column types
   - Constraints
   - Indexes

2. **Business Metadata**
   - Descriptions
   - Business glossary terms
   - Owner information
   - Steward contacts

3. **Operational Metadata**
   - Data lineage
   - Transformation logic
   - Quality metrics
   - Refresh schedules

**Data Ownership:**

| Dataset | Owner | Email | Tier |
|---------|-------|-------|------|
| ods.raw_events | Data Engineering | data-eng@company.com | BRONZE |
| staging.stg_earthquake_events | Data Engineering | data-eng@company.com | SILVER |
| marts.fct_earthquake_metrics | Analytics Engineering | analytics-eng@company.com | GOLD |

---

### 5. Data Security

**Access Control:**

```sql
-- Data Engineer role (full access to all layers)
CREATE ROLE data_engineer;
GRANT USAGE ON SCHEMA ods, staging, marts TO data_engineer;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA ods TO data_engineer;

-- Analyst role (read-only access to marts only)
CREATE ROLE analyst;
GRANT USAGE ON SCHEMA marts TO analyst;
GRANT SELECT ON ALL TABLES IN SCHEMA marts TO analyst;

-- Service account (Metabase, read-only)
CREATE USER metabase_user PASSWORD 'secure_password';
GRANT analyst TO metabase_user;
```

**Security Practices:**
- Secrets stored in environment variables
- No hardcoded credentials
- HTTPS for API communications
- Database-level encryption ready

---

### 6. Data Integration

**Ingestion Patterns:**

```
┌─────────────────┐
│  Full Load      │ Initial load of all historical data
├─────────────────┤
│  Incremental    │ Only new/changed records
├─────────────────┤
│  Upsert         │ Insert or update based on key
└─────────────────┘
```

**Error Handling:**
- Automatic retries (2 attempts)
- Detailed error logging
- Failed record quarantine
- Alert notifications

**Idempotency:**
- Unique constraints prevent duplicates
- Upsert logic (ON CONFLICT)
- Deterministic transformation logic

---

### 7. Data Dictionary

**Core Entities:**

#### ods.raw_events
```
Column: event_id
├─ Type: VARCHAR(255)
├─ Nullable: NO
├─ Constraint: PRIMARY KEY, UNIQUE
├─ Description: Unique earthquake event identifier from USGS
└─ Source: USGS Earthquake API

Column: magnitude
├─ Type: FLOAT
├─ Nullable: YES
├─ Description: Earthquake magnitude on Richter scale
├─ Valid Range: -2 to 10
└─ Source: USGS API properties

Column: place
├─ Type: VARCHAR(500)
├─ Nullable: YES
├─ Description: Geographic location description
└─ Example: "10 km NE of Parkfield, CA"

Column: event_data
├─ Type: JSONB
├─ Nullable: NO
├─ Description: Complete event data in JSON format
└─ Schema: GeoJSON FeatureCollection
```

#### marts.fct_earthquake_metrics
```
Column: event_date
├─ Type: DATE
├─ Nullable: NO
├─ Description: Date of aggregation
└─ Partitioned: By month

Column: event_count
├─ Type: INTEGER
├─ Nullable: NO
├─ Description: Number of earthquake events on this date
└─ Range: 0 to 10,000

Column: avg_magnitude
├─ Type: FLOAT
├─ Nullable: YES
├─ Description: Average magnitude for events on this date
└─ Formula: AVG(magnitude)
```

---

### 8. Data Lineage

**Lineage Tracking:**

```
USGS API
  ↓ (ingestion)
ods.raw_events
  ↓ (stg_earthquake_events model)
staging.stg_earthquake_events
  ↓ (dim_earthquake_events model)
ods.dim_earthquake_events
  ↓ (fct_earthquake_metrics model)
marts.fct_earthquake_metrics
  ↓ (visualization)
Metabase Dashboard
```

**Lineage Query:**
```sql
SELECT 
  source_system,
  source_table,
  target_table,
  transformation_type,
  created_at
FROM metadata.data_lineage
ORDER BY created_at DESC;
```

---

### 9. Compliance & Documentation

**Documentation Types:**

1. **Architecture Docs** → `docs/architecture.md`
2. **Governance Policies** → `docs/governance.md`
3. **Data Dictionary** → `docs/data_dictionary.md`
4. **Schema Documentation** → dbt `schema.yml`
5. **Quality Rules** → Great Expectations configs

**Audit Trail:**

```sql
-- All metadata changes are logged
SELECT 
  table_name,
  check_type,
  status,
  checked_at,
  details
FROM metadata.data_quality_checks
ORDER BY checked_at DESC;
```

---

## Best Practices

### 1. Data Quality
- ✅ Test data immediately after ingestion
- ✅ Monitor data freshness continuously
- ✅ Track quality metrics over time
- ❌ Trust external data without validation

### 2. Documentation
- ✅ Document WHY, not just WHAT
- ✅ Keep documentation near code
- ✅ Version documentation
- ❌ Leave code undocumented

### 3. Access Control
- ✅ Principle of least privilege
- ✅ Role-based access
- ✅ Audit all access
- ❌ Give everyone full access

### 4. Data Lineage
- ✅ Track all transformations
- ✅ Enable impact analysis
- ✅ Make lineage visible
- ❌ Hide data dependencies

### 5. Testing
- ✅ Test before production
- ✅ Automated testing in pipelines
- ✅ Test both happy and sad paths
- ❌ Manual testing only

---

## Governance Board Responsibilities

### Data Owners
- Define business requirements
- Approve quality rules
- Manage user access
- Resolve data issues

### Data Stewards
- Maintain data quality
- Update documentation
- Coordinate with owners
- Respond to incidents

### Data Engineers
- Build pipelines
- Implement quality checks
- Monitor performance
- Support troubleshooting

### Analytics Engineers
- Design dimensional models
- Create BI artifacts
- Optimize queries
- Establish standards
