{{ config(
  materialized = 'table',
  schema = 'ods',
  indexes=[
    {'columns': ['event_id'], 'unique': True},
    {'columns': ['event_type']},
    {'columns': ['magnitude']}
  ],
  tags = ['ods', 'daily']
) }}

-- ODS (Operational Data Store) layer
-- Normalized earthquake events table

SELECT
  {{ dbt_utils.generate_surrogate_key(['event_id']) }} AS event_sk,
  event_id,
  event_type,
  magnitude,
  place,
  latitude,
  longitude,
  depth,
  event_time,
  CURRENT_DATE AS load_date,
  CURRENT_TIMESTAMP AS load_timestamp,
  ingested_at
FROM {{ ref('stg_earthquake_events') }}
