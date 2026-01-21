-- Initialize schemas and roles for Data Governance Lakehouse

-- Create schemas
CREATE SCHEMA IF NOT EXISTS ods;
CREATE SCHEMA IF NOT EXISTS staging;
CREATE SCHEMA IF NOT EXISTS marts;
CREATE SCHEMA IF NOT EXISTS metadata;

-- Grant permissions
GRANT USAGE ON SCHEMA ods TO datauser;
GRANT USAGE ON SCHEMA staging TO datauser;
GRANT USAGE ON SCHEMA marts TO datauser;
GRANT USAGE ON SCHEMA metadata TO datauser;

-- Create metadata tables
CREATE TABLE IF NOT EXISTS metadata.data_lineage (
    id SERIAL PRIMARY KEY,
    source_system VARCHAR(255),
    source_table VARCHAR(255),
    target_table VARCHAR(255),
    transformation_type VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS metadata.data_quality_checks (
    id SERIAL PRIMARY KEY,
    table_name VARCHAR(255),
    check_type VARCHAR(100),
    check_name VARCHAR(255),
    status VARCHAR(50),
    checked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    details JSONB
);

CREATE TABLE IF NOT EXISTS metadata.dataset_ownership (
    id SERIAL PRIMARY KEY,
    dataset_name VARCHAR(255) UNIQUE,
    owner_name VARCHAR(255),
    owner_email VARCHAR(255),
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create ODS layer (Operational Data Store)
CREATE TABLE IF NOT EXISTS ods.raw_events (
    id SERIAL PRIMARY KEY,
    event_id VARCHAR(255) UNIQUE,
    event_type VARCHAR(100),
    event_data JSONB,
    source_system VARCHAR(100),
    ingested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    processed_at TIMESTAMP
);

-- Create indexes
CREATE INDEX idx_ods_event_id ON ods.raw_events(event_id);
CREATE INDEX idx_ods_event_type ON ods.raw_events(event_type);
CREATE INDEX idx_ods_ingested_at ON ods.raw_events(ingested_at);

-- Grant default privileges
ALTER DEFAULT PRIVILEGES IN SCHEMA ods GRANT SELECT ON TABLES TO datauser;
ALTER DEFAULT PRIVILEGES IN SCHEMA staging GRANT SELECT ON TABLES TO datauser;
ALTER DEFAULT PRIVILEGES IN SCHEMA marts GRANT SELECT ON TABLES TO datauser;
