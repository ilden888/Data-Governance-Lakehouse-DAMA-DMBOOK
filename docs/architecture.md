# Data Governance Lakehouse - Architecture

## System Architecture

```
┌─────────────────┐
│  Data Sources   │
│  (USGS API)     │
└────────┬────────┘
         │
         ▼
┌─────────────────────────────────┐
│   Airflow Orchestration         │
│  ┌──────────────────────────┐   │
│  │ Data Ingestion DAG       │   │
│  │ - Fetch from API         │   │
│  │ - Load to ODS            │   │
│  │ - Quality Checks         │   │
│  └──────────────────────────┘   │
│  ┌──────────────────────────┐   │
│  │ dbt Transformation DAG   │   │
│  │ - Staging models         │   │
│  │ - ODS normalized         │   │
│  │ - Marts aggregation      │   │
│  └──────────────────────────┘   │
└────────┬────────────────────────┘
         │
         ▼
┌─────────────────────────────────┐
│   PostgreSQL Data Warehouse     │
│  ┌──────────────────────────┐   │
│  │ ODS Layer                │   │
│  │ - raw_events             │   │
│  └──────────────────────────┘   │
│  ┌──────────────────────────┐   │
│  │ Staging Layer            │   │
│  │ - stg_earthquake_events  │   │
│  └──────────────────────────┘   │
│  ┌──────────────────────────┐   │
│  │ Data Mart Layer          │   │
│  │ - fct_earthquake_metrics │   │
│  └──────────────────────────┘   │
│  ┌──────────────────────────┐   │
│  │ Metadata Layer           │   │
│  │ - data_lineage           │   │
│  │ - data_quality_checks    │   │
│  │ - dataset_ownership      │   │
│  └──────────────────────────┘   │
└────────┬────────────────────────┘
         │
    ┌────┴─────┬──────────────┬──────────┐
    ▼          ▼              ▼          ▼
┌────────┐ ┌────────┐ ┌────────────┐ ┌──────────┐
│Metabase│ │ Great  │ │OpenMetadata│ │   MinIO  │
│  (BI)  │ │Expect. │ │(Lineage)   │ │  (S3)    │
│        │ │(Quality)│ │           │ │          │
└────────┘ └────────┘ └────────────┘ └──────────┘
```

## Data Flow

### Stage 1: Ingestion (Bronze)
- **Source**: USGS Earthquake API
- **Target**: MinIO Raw Zone / PostgreSQL ODS
- **Tool**: Airflow
- **Frequency**: Daily
- **Format**: JSON → Tabular

### Stage 2: Transformation (Silver)
- **Source**: ODS Layer
- **Target**: Staging Schema
- **Tool**: dbt
- **Operations**: Cleaning, Type Casting, Validation
- **Result**: Clean, business-logic-ready data

### Stage 3: Aggregation (Gold)
- **Source**: Staging Layer
- **Target**: Data Marts
- **Tool**: dbt
- **Operations**: Aggregations, Dimensions, Facts
- **Result**: BI-ready datasets

### Stage 4: Consumption
- **Target**: Metabase dashboards
- **Consumers**: Business users, Analysts
- **Latency**: Daily refresh

## Technology Stack

| Component | Technology | Version | Purpose |
|-----------|-----------|---------|---------|
| Orchestration | Apache Airflow | 2.7.3 | Task scheduling, DAG execution |
| Transformation | dbt | 1.7.0 | SQL-based transformations |
| Data Warehouse | PostgreSQL | 15 | Analytical storage |
| Storage | MinIO | latest | S3-compatible object storage |
| Quality | Great Expectations | 0.17.12 | Data validation |
| Metadata | OpenMetadata | - | Lineage & cataloging |
| BI | Metabase | latest | Analytics & dashboards |
| Orchestration | Docker | - | Container management |

## Data Governance Domains (DAMA-DMBOK)

### 1. Data Architecture
- Lakehouse architecture with layered DWH
- Separation of concerns (ODS, Staging, Marts)
- Data contract enforcement

### 2. Data Modeling & Design
- Dimensional modeling (facts & dimensions)
- Normalized ODS layer
- Star schema in marts

### 3. Data Storage & Operations
- PostgreSQL for DWH
- MinIO for raw data lake
- Partitioning by date
- Index optimization

### 4. Data Security
- Role-based access control (RBAC)
- Service user accounts
- Read-only BI role
- Password-protected access

### 5. Data Integration
- API-based ingestion
- Batch processing (daily)
- Error handling & retries
- Idempotent operations

### 6. Reference & Master Data
- Dimension tables (dim_earthquake_events)
- Lookup tables for classifications
- Version control of references

### 7. Data Warehousing & BI
- Dimensional models
- Star schemas
- Metabase dashboards
- Pre-aggregated metrics

### 8. Metadata & Lineage
- OpenMetadata catalog
- Data contract definitions
- Automated lineage tracking
- Column-level lineage

### 9. Data Quality
- Great Expectations validation
- Schema validation
- Null checks
- Range validation
- Freshness monitoring

### 10. Monitoring & Operations
- Airflow task monitoring
- Quality check results
- Lineage audit trail
- Error alerting

## Key Features

### Data Lineage
- Automatic tracking of data flow
- From API → ODS → Staging → Marts
- Column-level lineage visibility
- Impact analysis

### Data Contracts
- Schema versioning
- SLA definitions (freshness, row counts)
- Ownership assignment
- Validation rules

### Quality Framework
- Pre-ingestion validation
- Post-transformation checks
- Continuous monitoring
- Anomaly detection

### Compliance
- Data governance documentation
- Access control
- Audit trails
- Data dictionary
