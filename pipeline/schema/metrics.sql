-- Daily computed training metrics. One row per calendar day.
-- Populated by pipeline/metrics/*.py — see those for the formulas.
CREATE TABLE IF NOT EXISTS `sports_coaching.metrics` (
  date DATE NOT NULL,
  daily_trimp FLOAT64,          -- sum of that day's Banister TRIMP across activities
  ctl FLOAT64,                  -- Chronic Training Load (42-day EWMA of daily_trimp)
  atl FLOAT64,                  -- Acute Training Load (7-day EWMA of daily_trimp)
  tsb FLOAT64,                  -- Training Stress Balance (form) — prior day's ctl - atl
  vdot FLOAT64,                 -- best VDOT estimate from that day's qualifying run, if any
  estimated_vo2max FLOAT64,
  computed_at TIMESTAMP NOT NULL
)
PARTITION BY date;
