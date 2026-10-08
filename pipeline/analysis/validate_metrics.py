"""Faz 3 validation: cross-check TRIMP against hrTSS and review interval sessions.

Reads the live `activities` table with Application Default Credentials and prints a
Markdown report. Usage (from pipeline/): .venv/bin/python -m analysis.validate_metrics
"""

import truststore

truststore.inject_into_ssl()

from collections import defaultdict  # noqa: E402
from datetime import date, datetime, timedelta  # noqa: E402
from statistics import correlation, median  # noqa: E402
from zoneinfo import ZoneInfo  # noqa: E402

from google.cloud import bigquery  # noqa: E402

from config import ACTIVITIES_TABLE, ATHLETE, LOAD_SERIES_START  # noqa: E402
from metrics.daily import activity_date, activity_trimp, seeded_load_series  # noqa: E402
from metrics.hrtss import hr_tss  # noqa: E402
from metrics.intervals import is_auto_lapped, select_work_laps, session_vdot  # noqa: E402

# Same bounds as the dashboard page (portfolio src/lib/training/derive.ts).
TSB_BOUNDS = (-30, -10, 5)
INTERVAL_REVIEW_FROM = date(2026, 10, 4)


def tsb_zone(tsb: float) -> str:
    fatigued, optimal, fresh = TSB_BOUNDS
    if tsb < fatigued:
        return "fatigued"
    if tsb < optimal:
        return "optimal"
    if tsb <= fresh:
        return "neutral"
    return "fresh"


def load_rows() -> list[dict]:
    query = f"SELECT * FROM `{ACTIVITIES_TABLE}`"
    rows = []
    for row in bigquery.Client().query(query).result():
        record = dict(row)
        record["start_date_local"] = record["start_date_local"].isoformat()
        record["laps"] = [dict(lap) for lap in record["laps"]]
        rows.append(record)
    return rows


def per_activity(rows: list[dict]) -> list[dict]:
    out = []
    for row in rows:
        if activity_date(row) < LOAD_SERIES_START:
            continue
        trimp = activity_trimp(row, ATHLETE)
        if trimp is None:
            continue
        tss = hr_tss(row["moving_time_s"] / 60, row["average_heartrate"], ATHLETE.lthr)
        out.append(
            {"date": activity_date(row), "category": row["category"], "trimp": trimp, "tss": tss}
        )
    return out


def daily_series(points: list[dict], key: str, today: date) -> list[dict]:
    totals: dict[date, float] = defaultdict(float)
    for p in points:
        totals[p["date"]] += p[key]
    days = [LOAD_SERIES_START + timedelta(i) for i in range((today - LOAD_SERIES_START).days + 1)]
    return seeded_load_series([totals.get(d, 0.0) for d in days])


def section_activity_agreement(points: list[dict]) -> list[str]:
    lines = ["## 1. TRIMP vs hrTSS per activity", ""]
    lines.append("| Category | Activities | Pearson r | Spearman ρ | Median TRIMP / hrTSS |")
    lines.append("|---|---:|---:|---:|---:|")
    groups = {"all": points} | {
        c: [p for p in points if p["category"] == c] for c in ("run", "crossfit", "other")
    }
    for name, group in groups.items():
        if len(group) < 3:
            continue
        trimp = [p["trimp"] for p in group]
        tss = [p["tss"] for p in group]
        ratio = median(t / s for t, s in zip(trimp, tss, strict=True) if s > 0)
        lines.append(
            f"| {name} | {len(group)} | {correlation(trimp, tss):.3f} | "
            f"{correlation(trimp, tss, method='ranked'):.3f} | {ratio:.2f} |"
        )
    return lines + [""]


def section_load_agreement(points: list[dict], today: date) -> list[str]:
    trimp_series = daily_series(points, "trimp", today)
    tss_series = daily_series(points, "tss", today)
    ctl_r = correlation([d["ctl"] for d in trimp_series], [d["ctl"] for d in tss_series])
    tsb_r = correlation([d["tsb"] for d in trimp_series], [d["tsb"] for d in tss_series])
    same_zone = sum(
        tsb_zone(a["tsb"]) == tsb_zone(b["tsb"])
        for a, b in zip(trimp_series, tss_series, strict=True)
    )
    zone_counts = {label: defaultdict(int) for label in ("TRIMP", "hrTSS")}
    for a, b in zip(trimp_series, tss_series, strict=True):
        zone_counts["TRIMP"][tsb_zone(a["tsb"])] += 1
        zone_counts["hrTSS"][tsb_zone(b["tsb"])] += 1
    last_t, last_s = trimp_series[-1], tss_series[-1]
    n = len(trimp_series)
    lines = [
        "## 2. Daily load series (CTL / ATL / TSB)",
        "",
        f"- Days compared: {n} ({LOAD_SERIES_START} → {today})",
        f"- CTL correlation (TRIMP-based vs hrTSS-based): r = {ctl_r:.3f}",
        f"- TSB correlation: r = {tsb_r:.3f}",
        f"- Same form zone on {same_zone}/{n} days ({same_zone / n:.0%})",
        f"- Latest day: TRIMP-based CTL {last_t['ctl']:.1f} / TSB {last_t['tsb']:.1f}; "
        f"hrTSS-based CTL {last_s['ctl']:.1f} / TSB {last_s['tsb']:.1f}",
        "",
        "| Zone | Days (TRIMP) | Days (hrTSS) |",
        "|---|---:|---:|",
    ]
    for zone in ("fatigued", "optimal", "neutral", "fresh"):
        lines.append(f"| {zone} | {zone_counts['TRIMP'][zone]} | {zone_counts['hrTSS'][zone]} |")
    return lines + [""]


def section_intervals(rows: list[dict]) -> list[str]:
    lines = [f"## 3. Interval sessions since {INTERVAL_REVIEW_FROM}", ""]
    sessions = [
        r
        for r in rows
        if r["category"] == "run"
        and "interval" in (r.get("name") or "").lower()
        and activity_date(r) >= INTERVAL_REVIEW_FROM
    ]
    if not sessions:
        return lines + ["No runs titled 'interval' since then.", ""]
    lines += [
        "| Date | Laps | Auto-lapped | Reps found | Reps ≥ 90% LTHR | Session VDOT |",
        "|---|---:|---|---:|---:|---:|",
    ]
    min_hr = ATHLETE.lthr * 0.90
    for r in sorted(sessions, key=activity_date):
        laps = r["laps"]
        reps = select_work_laps(laps)
        hard = [lap for lap in reps if (lap.get("average_heartrate") or 0) >= min_hr]
        value = session_vdot(laps, ATHLETE)
        lines.append(
            f"| {activity_date(r)} | {len(laps)} | {'yes' if is_auto_lapped(laps) else 'no'} | "
            f"{len(reps)} | {len(hard)} | {f'{value:.1f}' if value else '—'} |"
        )
    return lines + [""]


def main() -> None:
    today = datetime.now(ZoneInfo("Europe/Istanbul")).date()
    rows = load_rows()
    points = per_activity(rows)
    report = [
        f"# Metric validation — {today}",
        "",
        f"Activities with heart rate since {LOAD_SERIES_START}: {len(points)}. "
        f"hrTSS uses the average-heart-rate approximation with LTHR {ATHLETE.lthr:.0f}.",
        "",
    ]
    report += section_activity_agreement(points)
    report += section_load_agreement(points, today)
    report += section_intervals(rows)
    print("\n".join(report))


if __name__ == "__main__":
    main()
