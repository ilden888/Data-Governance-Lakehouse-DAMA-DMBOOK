# Data Governance Lakehouse Demo

A production-inspired **end-to-end data engineering template project** demonstrating how to design, build, and operate a modern **Lakehouse architecture** aligned with **DAMA-DMBOK (Data Management Body of Knowledge)** Data Governance principles.

This repository is designed as a **portfolio-grade reference implementation** for Data Engineers, Analytics Engineers, and Platform Engineers.

---

## Project Goals

This project demonstrates:

* Practical implementation of **Data Governance domains** (DAMA-DMBOK)
* Modern **Lakehouse architecture**
* Production-style **data ingestion, transformation, orchestration, quality checks, lineage, and security**
* Realistic enterprise data workflows

---

## Architecture Overview

```
API Sources → Airflow (ETL/ELT)
           → Raw Zone (S3)
           → PostgreSQL DWH
               ├── ODS Layer
               ├── Staging Layer
               └── Data Mart Layer

PostgreSQL → Metabase (BI)

Monitoring:
- Great Expectations (Data Quality)
- OpenMetadata (Metadata & Lineage)
```

---

## DAMA-DMBOK Mapping

This project explicitly maps features to **Data Governance knowledge areas**.

| DAMA Domain               | Implementation                   |
| ------------------------- | -------------------------------- |
| Data Architecture         | Lakehouse design, layered DWH    |
| Data Modeling & Design    | Dimensional models, star schemas |
| Data Storage & Operations | S3 + PostgreSQL + partitioning   |
| Data Security             | RBAC, secrets management         |
| Data Integration          | API ingestion, batch pipelines   |
| Documents & Content       | Data contracts, schema docs      |
| Reference & Master Data   | Lookup tables, dimensions        |
| Data Warehousing & BI     | Data marts, Metabase             |
| Metadata                  | OpenMetadata catalog             |
| Data Quality              | Great Expectations checks        |

---

## Tech Stack

### Core

* **Python 3.11**
* **Apache Airflow** — orchestration
* **PostgreSQL** — analytical warehouse
* **AWS S3 / MinIO** — data lake storage
* **dbt** — transformations

### Governance Layer

* **Great Expectations** — data quality
* **OpenMetadata** — metadata, lineage

### BI

* **Metabase** — analytics and dashboards

### Infrastructure

* **Docker & Docker Compose**
* **Makefile automation**

---

## Repository Structure

```
project-root/
│
├── airflow/
│   ├── dags/
│   └── plugins/
│
├── dbt/
│   ├── models/
│   │   ├── staging/
│   │   ├── ods/
│   │   └── marts/
│   └── tests/
│
├── lakehouse/
│   ├── raw/
│   ├── bronze/
│   ├── silver/
│   └── gold/
│
├── metadata/
│   └── openmetadata/
│
├── quality/
│   └── great_expectations/
│
├── infra/
│   ├── docker-compose.yml
│   └── env/
│
├── docs/
│   ├── architecture.md
│   ├── governance.md
│   └── data_dictionary.md
│
└── README.md
```

---

## Data Pipeline Flow

### Step 1 — Data Ingestion

* Pull data from public API (example: Earthquake API)
* Store raw JSON into S3 (Raw Zone)

### Step 2 — Load to ODS

* Airflow loads raw data into PostgreSQL ODS schema

### Step 3 — Transformation (dbt)

* Staging models: cleaning & typing
* ODS models: normalized layer
* Data Marts: business-ready tables

### Step 4 — Data Quality

* Validate:

  * Schema
  * Null constraints
  * Freshness
  * Volume anomalies

### Step 5 — Metadata & Lineage

* Automatically register datasets
* Track pipeline lineage

### Step 6 — BI Consumption

* Metabase dashboards built on Gold layer

---

## Data Governance Implementation

### Data Quality

* Expectations:

  * Not null
  * Unique keys
  * Valid ranges
  * Referential integrity

### Metadata Management

* Dataset ownership
* Column descriptions
* Business glossary

### Security

* Separate service users
* Read-only BI role
* Environment secrets

### Documentation

* Architecture diagrams
* Data dictionary
* Model descriptions

---

## How To Run Locally

### Prerequisites

* Docker
* Docker Compose
* Make

### Start Stack

```bash
make up
```

Services:

| Service      | URL                                            |
| ------------ | ---------------------------------------------- |
| Airflow      | [http://localhost:8080](http://localhost:8080) |
| Metabase     | [http://localhost:3000](http://localhost:3000) |
| OpenMetadata | [http://localhost:8585](http://localhost:8585) |
| Postgres     | localhost:5432                                 |

---

## Example Use Cases

* Portfolio project for Data Engineers
* Interview demo project
* Governance framework reference
* Training sandbox

---

## Future Extensions

* CDC streaming (Kafka)
* Iceberg tables
* Feature Store
* ML pipelines
* Data mesh domains

---

## License

MIT License

---

## Why This Project Matters

Most demo projects show only ingestion or dashboards.

This project shows:

* Enterprise-grade architecture
* Governance-first mindset
* Production-style workflows

It reflects how modern data platforms are built in real companies.
