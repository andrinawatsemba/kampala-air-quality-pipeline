"""Kampala air quality dashboard. Run from the project root: streamlit run dashboard/app.py"""
import sys
from decimal import Decimal
from pathlib import Path

import pandas as pd
import streamlit as st

sys.path.append(str(Path(__file__).resolve().parents[1] / "src"))
from load import get_connection  # noqa: E402

WHO_PM25_GUIDELINE = 15  # ug/m3, 24-hour average

st.set_page_config(page_title="Kampala Air Quality", page_icon="🌍", layout="wide")


@st.cache_data(ttl=300)
def run_query(sql: str) -> pd.DataFrame:
    with get_connection() as conn, conn.cursor() as cur:
        cur.execute(sql)
        df = pd.DataFrame(cur.fetchall(), columns=[c.name for c in cur.description])
    for col in df.columns:  # Postgres NUMERIC arrives as Decimal; charts need floats
        if len(df) and isinstance(df[col].iloc[0], Decimal):
            df[col] = df[col].astype(float)
    return df


st.title("🌍 Kampala Air Quality")
st.caption(
    "Hourly air quality and weather for Kampala from Open-Meteo. "
    "Note: air quality values come from a computer model, not ground sensors."
)

hourly = run_query(
    "SELECT time, pm2_5, pm10 FROM air_quality_hourly WHERE is_forecast = false ORDER BY time"
)
if hourly.empty:
    st.warning("No data yet. Run `python src/load.py` first.")
    st.stop()

latest = hourly.iloc[-1]
avg_24h = hourly.tail(24)["pm2_5"].mean()

col1, col2, col3 = st.columns(3)
col1.metric("Latest PM2.5 (ug/m3)", f"{latest['pm2_5']:.1f}")
col2.metric(
    "Last 24h average PM2.5",
    f"{avg_24h:.1f}",
    delta=f"{avg_24h - WHO_PM25_GUIDELINE:+.1f} vs WHO guideline ({WHO_PM25_GUIDELINE})",
    delta_color="inverse",
)
col3.metric("Hours of data", f"{len(hourly):,}")

st.subheader("Hourly PM2.5 and PM10")
st.line_chart(hourly.set_index("time")[["pm2_5", "pm10"]])

daily = run_query("SELECT * FROM daily_air_quality ORDER BY day")
left, right = st.columns(2)
with left:
    st.subheader("Daily average PM2.5")
    st.bar_chart(daily.set_index("day")["avg_pm2_5"])
with right:
    st.subheader("Worst air days")
    st.dataframe(run_query("SELECT * FROM worst_air_days"), hide_index=True)