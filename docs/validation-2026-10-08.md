# Metric validation — 2026-10-08

Activities with heart rate since 2025-11-01: 206. hrTSS uses the average-heart-rate approximation with LTHR 165.

## 1. TRIMP vs hrTSS per activity

| Category | Activities | Pearson r | Spearman ρ | Median TRIMP / hrTSS |
|---|---:|---:|---:|---:|
| all | 206 | 0.955 | 0.947 | 1.09 |
| run | 91 | 0.975 | 0.941 | 1.16 |
| crossfit | 96 | 0.951 | 0.929 | 1.05 |
| other | 19 | 0.984 | 0.979 | 0.90 |

## 2. Daily load series (CTL / ATL / TSB)

- Days compared: 342 (2025-11-01 → 2026-10-08)
- CTL correlation (TRIMP-based vs hrTSS-based): r = 0.959
- TSB correlation: r = 0.973
- Same form zone on 302/342 days (88%)
- Latest day: TRIMP-based CTL 48.6 / TSB -15.6; hrTSS-based CTL 43.9 / TSB -13.8

| Zone | Days (TRIMP) | Days (hrTSS) |
|---|---:|---:|
| fatigued | 4 | 1 |
| optimal | 76 | 68 |
| neutral | 148 | 167 |
| fresh | 114 | 106 |

## 3. Interval sessions since 2026-10-04

No runs titled 'interval' since then.

## 4. VDOT vs Garmin VO2max

Garmin values are read approximately from the Garmin Connect 6-month VO2max chart
(2026-04-10 → 2026-10-08); the latest value (59) is exact.

| Moment | Our VDOT | Garmin VO2max |
|---|---:|---:|
| Runtalya 2026 half marathon (2026-04-05) | 51.2 (race) | ≈ 54–55 (first readings after the race) |
| Mid-May peak | — | ≈ 58.5 |
| August low | — | ≈ 54.5 |
| 2026-10-08 | 51.2 (latest, from April) | 59 |

- **Systematic offset.** Garmin reads about 3 points above race-based VDOT right after the same
  race. Expected: Garmin/Firstbeat estimates physiological VO2max from the heart-rate–pace
  relationship, while Daniels VDOT is an *effective* VO2max derived from race performance, so
  running economy, pacing and conditions pull it down. VDOT should be labelled as such, not as
  "VO2max".
- **Freshness.** VDOT only moves at a tagged race or a qualifying interval session; the latest point
  is six months old. Garmin's continuous estimate shows a rise to 59 that VDOT cannot confirm until
  the next race or interval session.
- **Noise.** Garmin's estimate swings ~4–5 points within the six months and ~2 points within weeks;
  VDOT is sparse but stable. The two are complementary rather than contradictory.

## 5. Workout rules on real sessions (added 2026-10-08, late)

Interval and tempo sessions are now recognised by the Strava run type "Workout" instead of the word
"interval" in the title, and tempo runs count towards VDOT. A scan of 89 untagged heart-rate runs
since 2025-11-01 (`pipeline/analysis/find_workout_candidates.py`) and the first tagged sessions give:

| Date | Session | Read as | VDOT | Verdict |
|---|---|---|---:|---|
| 2025-12-05 | 5 × 3 min, watch structured workout, rep HR 148–160 | interval | 47.5 | qualifies (not tagged yet) |
| 2026-03-27 | 6 × ~4 min, watch structured workout, rep HR 153–161 | interval | 46.5 | qualifies (not tagged yet) |
| 2026-09-29 | LTHR test: 10 + 20 min, last 20 min HR 165 | tempo | 53.2 | **reads ~2.4 high**: a 30-min all-out effort scored as one-hour pace; as a 30-min race it would be ≈ 50.8. Kept as tempo by Ahmet's decision |
| 2026-10-02 | 5 × ~3.8 min @ 3:38–3:52, rep HR 149–158 | interval | 50.9 | qualifies |
| 2026-10-06 | 2 × 15 min @ 4:06–4:07, HR 160–161 | tempo | 51.7 | qualifies |
| 2026-01-09, 2026-01-16 | 5 × 3 min, rep HR 128–148 | interval | — | correctly rejected: below 90% LTHR |
| 2026-04-26 | trail race, steep climbs | — | — | correctly rejected |

The recent interval (50.9) and tempo (51.7) agree with each other and with the last race (51.2, April),
which supports both conversions (I pace ≈ vVO2max, T pace ≈ one-hour race pace) and the effort gates
(≥ 90% LTHR for reps, ≥ 95% for tempo). Sessions recorded as watch structured workouts get one lap
per step, so they work as well as manually lapped ones.

Also changed the same evening: form (TSB) is now the **same day's** CTL − ATL rather than the previous
day's (TrainingPeaks convention), so the form, fitness and fatigue shown for one day always add up.
Sections 1–2 compared TRIMP and hrTSS under one shared convention, so their conclusions are unaffected.

## Conclusions

1. TRIMP and hrTSS agree closely (r ≈ 0.95–0.98), and their scales are within ~10% of each other, so
   the TSS-calibrated form zones on the dashboard are a reasonable fit for TRIMP-based form.
2. CrossFit/HIIT agreement (r = 0.951) is slightly below running (0.975), consistent with TRIMP
   being an approximation for interval-type strength work.
3. VDOT is honest but sparse and sits below Garmin's VO2max by design; present it as race-based VDOT.
4. Interval and tempo rules behave sensibly on real sessions (section 5); the one known bias is a
   30-minute threshold test scored as tempo (~2.4 high).

