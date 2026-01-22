{{ config(
  materialized = 'table',
  schema = 'marts',
  tags = ['marts', 'daily', 'business_ready']
) }}

-- Business ready mart for earthquake analytics
-- Aggregated and enriched earthquake data for BI consumption

SELECT
  DATE(event_time) AS event_date,
  event_type,
  CASE
    WHEN magnitude < 2 THEN 'Micro'
    WHEN magnitude < 4 THEN 'Minor'
    WHEN magnitude < 5 THEN 'Light'
    WHEN magnitude < 6 THEN 'Moderate'
    WHEN magnitude < 7 THEN 'Strong'
    WHEN magnitude < 8 THEN 'Major'
    ELSE 'Great'
  END AS magnitude_category,
  COUNT(*) AS event_count,
  AVG(magnitude) AS avg_magnitude,
  MAX(magnitude) AS max_magnitude,
  MIN(magnitude) AS min_magnitude,
  COUNT(DISTINCT place) AS distinct_locations,
  CURRENT_TIMESTAMP AS metric_timestamp
FROM {{ ref('dim_earthquake_events') }}
WHERE event_time >= CURRENT_DATE - INTERVAL '1 year'
GROUP BY 1, 2, 3
ORDER BY event_date DESC, event_count DESC
