# Case study — Faz 3 genişletmesi (Ahmet onayladı, 2026-10-11)

Sayfadaki "How it's built" bölümüne (`Portfolio_Website_Project/src/components/training/HowItsBuilt.tsx`)
eklenecek metin. INTRO, The metrics ve Architecture bölümleri 2026-10-04'te onaylandı, değişmiyor.
Sıra: Key decisions → Metrics and their limits → **How I checked the numbers (yeni)** → What real
data revealed (genişletildi) → **The same data in Looker Studio (yeni)**. ("What's next" Ahmet'in kararıyla çıkarıldı.)
Kaynak: `docs/validation-2026-10-08.md`, CLAUDE.md "Metrikler".

---

## Key decisions — iki cümle eklendi

A full snapshot on every run instead of incremental merges, so edited or deleted activities are
always picked up. A separate least-privilege service account for each job. A static JSON export
instead of an API layer. Route and GPS data are never stored, and nothing public names an activity
except races. If the nightly run fails, a Cloud Monitoring alert emails me.

## Metrics and their limits — değişmedi

## How I checked the numbers — YENİ

A metric I can't check is just a number. I recomputed every session's load with a second,
independent model, heart-rate TSS based on my lactate-threshold heart rate, and compared the two.
They agree closely: r = 0.955 per activity (0.975 for runs, 0.951 for CrossFit), and on 88% of days
both put me in the same form zone, so the zone thresholds on this page hold for TRIMP.

For running fitness, my latest interval session (50.9), tempo run (51.7) and race (51.2) land
within a point of each other. Garmin's VO2max reads about 3 points higher after the same race. That
is expected: Garmin estimates physiology, VDOT measures race performance, which is why this page
calls it running fitness rather than VO2max.

## What real data revealed — genişletildi

Automatic 1 km laps looked like intervals and had to be filtered out; requiring at least 90% of
lactate-threshold heart rate separates real interval work from steady running. Short reps are left
out on purpose: 400–800 m repeats are run faster than VO2max pace and would inflate the estimate.
A single 210 bpm reading on a HIIT session was an optical-sensor spike, so maximum
heart rate is set from the highest plausible value instead.

## The same data in Looker Studio — YENİ

The same BigQuery tables also feed a Looker Studio report, a second presentation layer built with
a standard BI tool. It connects only to reporting views that expose safe columns, with no activity
names or ids, so the privacy rules hold however the report is edited, and viewers cannot download
the data. Where this page shows where I stand today, the report summarises whatever period you
pick.
