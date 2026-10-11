-- Reporting views for the Looker Studio report (owner's credentials).
-- The report connects to these views only, never to the base tables, so the same privacy rules
-- as the public dashboard.json hold no matter how the report is edited: no activity ids or
-- names (only race names, which already appear as VDOT labels on the page), no athlete id,
-- no laps. GPS/route data is not stored at all.
-- Views read the tables at query time, so the nightly WRITE_TRUNCATE reload keeps them current.
-- Apply: bq query --use_legacy_sql=false < pipeline/schema/reporting_views.sql

-- Daily training load from the start of heart-rate coverage (LOAD_SERIES_START in config.py);
-- before it CTL/ATL/TSB are NULL.
CREATE OR REPLACE VIEW `training_performance.rpt_daily_load` AS
SELECT
  date,
  DATE_TRUNC(date, WEEK(MONDAY)) AS week_start,
  ROUND(daily_trimp, 1) AS trimp,
  ROUND(trimp_run, 1) AS trimp_run,
  ROUND(trimp_crossfit, 1) AS trimp_crossfit,
  ROUND(trimp_other, 1) AS trimp_other,
  ROUND(ctl, 1) AS fitness_ctl,
  ROUND(atl, 1) AS fatigue_atl,
  ROUND(tsb, 1) AS form_tsb,
  -- Same zones and labels as the portfolio page (src/lib/training/derive.ts, TSB_BOUNDS).
  CASE
    WHEN tsb < -30 THEN 'Fatigued'
    WHEN tsb < -10 THEN 'Optimal training'
    WHEN tsb <= 5 THEN 'Neutral'
    ELSE 'Fresh'
  END AS form_zone
FROM `training_performance.metrics`
WHERE ctl IS NOT NULL;

-- One row per activity, without identifying fields.
CREATE OR REPLACE VIEW `training_performance.rpt_activities` AS
SELECT
  DATE(start_date_local) AS activity_date,
  DATE_TRUNC(DATE(start_date_local), WEEK(MONDAY)) AS week_start,
  EXTRACT(HOUR FROM start_date_local) AS start_hour,
  category,
  sport_type,
  CASE
    WHEN category != 'run' THEN NULL
    WHEN workout_type = 1 THEN 'Race'
    WHEN workout_type = 3 THEN 'Workout'
    ELSE 'Easy / long'
  END AS run_type,
  ROUND(moving_time_s / 60, 1) AS moving_min,
  ROUND(elapsed_time_s / 60, 1) AS elapsed_min,
  ROUND(distance_m / 1000, 2) AS distance_km,
  IF(category = 'run' AND distance_m > 0,
     ROUND(moving_time_s / 60 / (distance_m / 1000), 2), NULL) AS pace_min_per_km,
  has_heartrate,
  ROUND(average_heartrate) AS avg_hr,
  ROUND(total_elevation_gain) AS elevation_gain_m
FROM `training_performance.activities`;

-- Running fitness (VDOT) points, labelled like the page: races carry their name.
CREATE OR REPLACE VIEW `training_performance.rpt_vdot` AS
SELECT
  m.date,
  ROUND(m.vdot, 1) AS vdot,
  m.vdot_source,
  IF(m.vdot_source = 'race', r.name, NULL) AS race_name
FROM `training_performance.metrics` AS m
LEFT JOIN (
  SELECT DATE(start_date_local) AS date, ANY_VALUE(name) AS name
  FROM `training_performance.activities`
  WHERE workout_type = 1
  GROUP BY date
) AS r USING (date)
WHERE m.vdot IS NOT NULL;
