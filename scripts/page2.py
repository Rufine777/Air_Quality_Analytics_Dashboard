import io
import os
from pathlib import Path
import urllib.request
import zipfile
import numpy as np
import pandas as pd

RAW_PATH = Path("/tmp/weather_raw/india_2000_2024_daily_weather.csv")
OUTPUT_PATH = Path("data/page2.csv")
KAGGLE_URL = (
    "https://www.kaggle.com/api/v1/datasets/download/developerghost/climate-in-india-daily-weather-data-2000-2024"
)


def ensure_raw_file():
    if RAW_PATH.exists():
        return RAW_PATH

    print("Raw weather dataset not found in /tmp. Downloading from Kaggle...")
    req = urllib.request.Request(KAGGLE_URL, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req) as resp:
        content = resp.read()

    RAW_PATH.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(io.BytesIO(content)) as z:
        z.extractall(RAW_PATH.parent)

    print(f"Extracted raw weather dataset to {RAW_PATH}")
    return RAW_PATH


def preprocess():
    raw_file = ensure_raw_file()
    df = pd.read_csv(raw_file)
    print(f"Read {len(df)} rows from raw dataset.")

    subset = df[df["date"] >= "2022-01-01"].copy()
    subset = subset.sort_values(["city", "date"]).reset_index(drop=True)
    print(f"Trimmed to {len(subset)} rows covering {subset['city'].nunique()} cities from {subset['date'].min()} to {subset['date'].max()}.")

    subset = subset.rename(
        columns={
            "temperature_2m_max": "temp_max",
            "temperature_2m_min": "temp_min",
            "apparent_temperature_max": "feels_like",
            "rain_sum": "rainfall",
            "precipitation_sum": "precipitation",
            "weather_code": "weather_code",
            "wind_speed_10m_max": "wind_speed",
            "wind_gusts_10m_max": "wind_gusts",
            "wind_direction_10m_dominant": "wind_direction",
        }
    )

    print("Missing values in subset:")
    print(subset.isna().sum())

    subset.insert(0, "record_id", range(1, len(subset) + 1))

    cols = [
        "record_id",
        "city",
        "date",
        "temp_max",
        "temp_min",
        "feels_like",
        "rainfall",
        "precipitation",
        "weather_code",
        "wind_speed",
        "wind_gusts",
        "wind_direction",
    ]
    subset = subset[cols]

    subset["record_id"] = subset["record_id"].astype(int)
    subset["temp_max"] = subset["temp_max"].astype(float).round(1)
    subset["temp_min"] = subset["temp_min"].astype(float).round(1)
    subset["feels_like"] = subset["feels_like"].astype(float).round(1)
    subset["rainfall"] = subset["rainfall"].astype(float).round(1)
    subset["precipitation"] = subset["precipitation"].astype(float).round(1)
    subset["weather_code"] = subset["weather_code"].astype(int)
    subset["wind_speed"] = subset["wind_speed"].astype(float).round(1)
    subset["wind_gusts"] = subset["wind_gusts"].astype(float).round(1)
    subset["wind_direction"] = subset["wind_direction"].astype(int)

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    subset.to_csv(OUTPUT_PATH, index=False)
    print(f"Saved {OUTPUT_PATH} with {len(subset)} rows and {len(subset.columns)} columns.")


if __name__ == "__main__":
    preprocess()
