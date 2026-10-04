-- Daily training metrics, one row per calendar day (rest days included with zero load).
-- Recomputed in full on every run by pipeline/metrics/daily.py — see it for the formulas.
CREATE TABLE IF NOT EXISTS `training_performance.metrics` (
  date DATE NOT NULL,
  daily_trimp FLOAT64,          -- Banister TRIMP summed over the day's activities
  trimp_run FLOAT64,
  trimp_crossfit FLOAT64,
  trimp_other FLOAT64,
  ctl FLOAT64,                  -- Chronic Training Load (42-day EWMA of daily_trimp)
  atl FLOAT64,                  -- Acute Training Load (7-day EWMA of daily_trimp)
  tsb FLOAT64,                  -- Training Stress Balance (form): previous day's ctl - atl
  vdot FLOAT64,                 -- from a race or an interval session that day, if any
  vdot_source STRING,           -- race | interval
  computed_at TIMESTAMP NOT NULL
);
