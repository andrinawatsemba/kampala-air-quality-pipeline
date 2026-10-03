"""Data quality checks on the last 48 hours of real (non-forecast) data.

Exit code is 1 if any check fails, so a scheduler (like GitHub Actions) can flag it.
"""
import sys

import pandas as pd

from load import get_connection

TZ = "Africa/Kampala"
WINDOW_HOURS = 48
MAX_STALE_HOURS = 6     # newest real reading must be at most this old
MAX_NULL_SHARE = 0.10    # at most 10% missing values per column

# Believable limits for Kampala. Anything outside is probably a bad reading.
VALUE_RANGES = {
    "pm2_5": (0, 500),
    "pm10": (0, 600),
    "nitrogen_dioxide": (0, 500),
    "ozone": (0, 600),
    "temperature_2m": (5, 40),
    "relative_humidity_2m": (0, 100),
    "precipitation": (0, 100),
}


def load_recent() -> pd.DataFrame:
    sql = f"""
        SELECT * FROM air_quality_hourly
        WHERE is_forecast = false
          AND time >= (now() AT TIME ZONE '{TZ}') - interval '{WINDOW_HOURS} hours'
        ORDER BY time
    """
    with get_connection() as conn, conn.cursor() as cur:
        cur.execute(sql)
        columns = [c.name for c in cur.description]
        return pd.DataFrame(cur.fetchall(), columns=columns)


def check_freshness(df):
    if df.empty:
        return False, "no real readings in the last 48 hours"
    now = pd.Timestamp.now(tz=TZ).tz_localize(None)
    age = (now - df["time"].max()).total_seconds() / 3600
    return age <= MAX_STALE_HOURS, f"newest reading is {age:.1f} hours old (limit {MAX_STALE_HOURS})"


def check_no_gaps(df):
    if df.empty:
        return False, "no data to check"
    expected = pd.date_range(df["time"].min(), df["time"].max(), freq="h")
    missing = expected.difference(df["time"])
    return len(missing) == 0, f"{len(missing)} missing hours"


def check_nulls(df):
    if df.empty:
        return False, "no data to check"
    shares = df[list(VALUE_RANGES)].isna().mean()
    bad = shares[shares > MAX_NULL_SHARE]
    detail = "all columns OK" if bad.empty else "too many nulls in: " + ", ".join(bad.index)
    return bad.empty, detail


def check_ranges(df):
    problems = []
    for col, (low, high) in VALUE_RANGES.items():
        n_bad = int(((df[col] < low) | (df[col] > high)).sum())
        if n_bad:
            problems.append(f"{col}: {n_bad} values outside {low}-{high}")
    return not problems, "; ".join(problems) or "all values in range"


CHECKS = [
    ("Freshness", check_freshness),
    ("No missing hours", check_no_gaps),
    ("Null share", check_nulls),
    ("Value ranges", check_ranges),
]


def main() -> int:
    df = load_recent()
    failed = 0
    for name, check in CHECKS:
        passed, detail = check(df)
        print(f"[{'PASS' if passed else 'FAIL'}] {name}: {detail}")
        failed += not passed
    print(f"\n{len(CHECKS) - failed}/{len(CHECKS)} checks passed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
