"""Fetch hourly air quality + weather for Kampala from Open-Meteo (no API key needed)."""
import logging

import pandas as pd
import requests

LAT, LON = 0.3476, 32.5825  # Kampala
TIMEZONE = "Africa/Kampala"
AIR_URL = "https://air-quality-api.open-meteo.com/v1/air-quality"
WEATHER_URL = "https://api.open-meteo.com/v1/forecast"

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)


def _fetch_hourly(url: str, variables: list[str], past_days: int) -> pd.DataFrame:
    """Call one Open-Meteo endpoint and return its hourly data as a DataFrame."""
    params = {
        "latitude": LAT,
        "longitude": LON,
        "hourly": ",".join(variables),
        "past_days": past_days,
        "forecast_days": 1,
        "timezone": TIMEZONE,
    }
    response = requests.get(url, params=params, timeout=30)
    response.raise_for_status()  # stop loudly if the API fails
    df = pd.DataFrame(response.json()["hourly"])
    df["time"] = pd.to_datetime(df["time"])
    return df


def fetch_kampala_data(past_days: int = 2) -> pd.DataFrame:
    """Air quality + weather in one table, one row per hour."""
    air = _fetch_hourly(AIR_URL, ["pm2_5", "pm10", "nitrogen_dioxide", "ozone"], past_days)
    weather = _fetch_hourly(
        WEATHER_URL, ["temperature_2m", "relative_humidity_2m", "precipitation"], past_days
    )
    merged = air.merge(weather, on="time", how="inner")
    log.info("Fetched %d hourly rows (%s to %s)", len(merged), merged["time"].min(), merged["time"].max())
    return merged


if __name__ == "__main__":
    data = fetch_kampala_data()
    print(data.head())
    print(data.dtypes)
    print("Missing values per column:\n", data.isna().sum())