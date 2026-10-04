-- Strava activities, rebuilt from a full snapshot on every pipeline run.
-- Deliberately excludes GPS/route fields (polyline, start/end latlng) — privacy decision:
-- route data is never stored, so it can never leak into a presentation layer.
-- Not partitioned/clustered: a few hundred rows, partitioning would only add overhead.
CREATE TABLE IF NOT EXISTS `training_performance.activities` (
  activity_id STRING NOT NULL,
  athlete_id STRING NOT NULL,
  name STRING,
  sport_type STRING,                 -- Run, TrailRun, HighIntensityIntervalTraining, ...
  workout_type INT64,                -- 1 = race (set in Strava as run type "Race")
  category STRING,                   -- run | crossfit | other
  start_date TIMESTAMP NOT NULL,     -- UTC
  start_date_local DATETIME,         -- athlete's wall-clock time
  timezone STRING,
  elapsed_time_s INT64,
  moving_time_s INT64,
  distance_m FLOAT64,
  has_heartrate BOOL,
  average_heartrate FLOAT64,
  max_heartrate FLOAT64,
  average_speed FLOAT64,             -- m/s
  max_speed FLOAT64,                 -- m/s
  total_elevation_gain FLOAT64,
  suffer_score FLOAT64,              -- Strava's Relative Effort, kept as a cross-check
  laps ARRAY<STRUCT<                 -- only for runs titled "interval"; used for VDOT
    lap_index INT64,
    distance_m FLOAT64,
    moving_time_s INT64,
    average_speed FLOAT64,
    average_heartrate FLOAT64
  >>,
  ingested_at TIMESTAMP NOT NULL
);
