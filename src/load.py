"""Load the hourly Kampala data into PostgreSQL. Safe to run many times (no duplicates)."""
import logging
import os

import pandas as pd
import psycopg2
from psycopg2.extras import execute_values

from ingest import fetch_kampala_data

log = logging.getLogger(__name__)

COLUMNS = [
    "time", "pm2_5", "pm10", "nitrogen_dioxide", "ozone",
    "temperature_2m", "relative_humidity_2m", "precipitation", "is_forecast",
]


def get_connection():
    # Local dev defaults match docker-compose.yml. Real secrets go in environment variables.
    return psycopg2.connect(
        host=os.getenv("PGHOST", "localhost"),
        port=os.getenv("PGPORT", "5432"),
        dbname=os.getenv("PGDATABASE", "airquality"),
        user=os.getenv("PGUSER", "pipeline"),
        password=os.getenv("PGPASSWORD", "pipeline_dev"),
    )


def load(df: pd.DataFrame) -> int:
    """Insert rows. If an hour already exists, update it (forecast rows become real readings)."""
    data = df[COLUMNS].astype(object).where(df[COLUMNS].notna(), None)  # NaN -> NULL
    rows = [tuple(r) for r in data.itertuples(index=False, name=None)]

    updates = ", ".join(f"{c} = EXCLUDED.{c}" for c in COLUMNS[1:])
    sql = f"""
        INSERT INTO air_quality_hourly ({", ".join(COLUMNS)})
        VALUES %s
        ON CONFLICT (time) DO UPDATE SET {updates}, loaded_at = now()
    """
    with get_connection() as conn, conn.cursor() as cur:
        execute_values(cur, sql, rows)
    log.info("Upserted %d rows", len(rows))
    return len(rows)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    load(fetch_kampala_data())