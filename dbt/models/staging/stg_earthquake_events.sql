{{ config(
  materialized = 'view',
  schema = 'staging',
  tags = ['staging', 'daily']
) }}

-- Staging model for raw earthquake events
-- Cleans and normalizes raw event data

SELECT
  event_id,
  event_type,
  (event_data->>'magnitude')::FLOAT AS magnitude,
  (event_data->>'place') AS place,
  (event_data->>'latitude')::FLOAT AS latitude,
  (event_data->>'longitude')::FLOAT AS longitude,
  (event_data->>'depth')::FLOAT AS depth,
  CAST(event_data->>'time' AS TIMESTAMP) AS event_time,
  ingested_at,
  CURRENT_TIMESTAMP AS dbt_loaded_at
FROM {{ source('raw', 'raw_events') }}
WHERE event_id IS NOT NULL
  AND event_type IS NOT NULL
