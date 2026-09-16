-- Raw Strava activities. One row per activity.
-- Deliberately excludes GPS/route fields (polyline, start/end latlng) — privacy
-- decision: route data is never stored, so it can never leak into a presentation layer.
CREATE TABLE IF NOT EXISTS `sports_coaching.activities` (
  activity_id STRING NOT NULL,       -- Strava activity id
  athlete_id STRING NOT NULL,        -- Strava athlete id
  name STRING,
  type STRING,                       -- Run, WeightTraining, Workout, etc.
  start_date TIMESTAMP NOT NULL,     -- UTC
  start_date_local TIMESTAMP,
  timezone STRING,
  elapsed_time_s INT64,
  moving_time_s INT64,
  distance_m FLOAT64,
  average_heartrate FLOAT64,
  max_heartrate FLOAT64,
  average_speed FLOAT64,             -- m/s
  max_speed FLOAT64,                 -- m/s
  total_elevation_gain FLOAT64,
  suffer_score FLOAT64,              -- Strava's own Relative Effort, kept as a cross-check
  ingested_at TIMESTAMP NOT NULL
)
PARTITION BY DATE(start_date)
CLUSTER BY athlete_id, type;
