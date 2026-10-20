"""Prepare data/health_impact.csv from the original Kaggle dataset.

Source: https://www.kaggle.com/datasets/khushikyad001/air-quality-weather-and-respiratory-health
Original file: air_quality_health_dataset.csv (26 columns, 3,000 rows)

Run this ONCE (it is not needed when the dashboard starts), from the project root:

    python scripts/prepare_health_data.py
    python scripts/prepare_health_data.py path/to/air_quality_health_dataset.csv

By default the script looks for data/raw/air_quality_health_dataset.csv.
The output is data/health_impact.csv with exactly these columns:
record_id, date, area, respiratory_cases, hospital_visits, aqi_category
"""
import argparse
import os
import sys
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT = PROJECT_ROOT / "data" / "raw" / "air_quality_health_dataset.csv"
DEFAULT_OUTPUT = PROJECT_ROOT / "data" / "health_impact.csv"

SOURCE_COLUMNS = ["date", "region", "AQI", "respiratory_admissions", "hospital_visits"]
OUTPUT_COLUMNS = ["record_id", "date", "area", "respiratory_cases", "hospital_visits", "aqi_category"]

# US EPA style categories, as in the project plan (upper bound of each band, on the rounded AQI).
AQI_BINS = [-np.inf, 50, 100, 150, 200, 300, np.inf]
AQI_LABELS = [
    "Good",
    "Moderate",
    "Unhealthy for Sensitive Groups",
    "Unhealthy",
    "Very Unhealthy",
    "Hazardous",
]


def whole_count(series, name):
    """Convert a count column to nullable integers. Missing values stay missing (never 0)."""
    nums = pd.to_numeric(series, errors="coerce")
    bad_text = nums.isna() & series.notna()
    if bad_text.any():
        raise ValueError(f"Column '{name}' has {int(bad_text.sum())} non-numeric value(s).")
    present = nums.dropna()
    if ((present % 1) != 0).any() or (present < 0).any():
        raise ValueError(f"Column '{name}' must contain non-negative whole numbers.")
    return nums.astype("Int64")


def build_health_table(raw):
    """Turn the raw Kaggle DataFrame into the six-column health table."""
    missing = [c for c in SOURCE_COLUMNS if c not in raw.columns]
    if missing:
        raise ValueError("Original file is missing column(s): " + ", ".join(missing))

    df = pd.DataFrame()

    # Dates must be real dates; saved as YYYY-MM-DD.
    dates = pd.to_datetime(raw["date"], format="%Y-%m-%d", errors="coerce")
    if dates.isna().any():
        raise ValueError(f"{int(dates.isna().sum())} row(s) have an invalid or missing date.")
    df["date"] = dates.dt.strftime("%Y-%m-%d")

    df["area"] = raw["region"].astype(str).str.strip()
    df["respiratory_cases"] = whole_count(raw["respiratory_admissions"], "respiratory_admissions")
    df["hospital_visits"] = whole_count(raw["hospital_visits"], "hospital_visits")

    # AQI is rounded half-up to a whole number first, then categorised.
    aqi = pd.to_numeric(raw["AQI"], errors="coerce")
    if aqi.isna().any():
        raise ValueError(f"{int(aqi.isna().sum())} row(s) have a missing or non-numeric AQI, "
                         "so aqi_category cannot be derived. Nothing was guessed.")
    if (aqi < 0).any():
        raise ValueError("AQI contains negative values.")
    rounded = np.floor(aqi + 0.5)
    df["aqi_category"] = pd.cut(rounded, bins=AQI_BINS, labels=AQI_LABELS).astype(str)

    df.insert(0, "record_id", range(1, len(df) + 1))
    return df[OUTPUT_COLUMNS], aqi


def validate(df):
    """Final checks on the prepared table."""
    assert list(df.columns) == OUTPUT_COLUMNS, "wrong columns/order"
    assert df["record_id"].is_unique, "record_id not unique"
    assert df["record_id"].min() == 1 and df["record_id"].max() == len(df), "record_id not 1..n"
    assert pd.to_datetime(df["date"], format="%Y-%m-%d", errors="coerce").notna().all(), "bad dates"
    assert df["area"].str.len().gt(0).all(), "empty area"
    assert df["aqi_category"].isin(AQI_LABELS).all(), "bad AQI category"


def write_csv_safely(df, path):
    """Write to a temp file, then replace the real file (same idea as CSVManager)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", suffix=".csv", dir=path.parent, delete=False,
                                     encoding="utf-8", newline="") as tf:
        tmp = Path(tf.name)
        df.to_csv(tf, index=False)
    os.replace(tmp, path)


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("input", nargs="?", default=str(DEFAULT_INPUT), help="original Kaggle CSV")
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT), help="where to write health_impact.csv")
    args = parser.parse_args()

    src, dst = Path(args.input), Path(args.output)
    if not src.exists():
        sys.exit(f"Original dataset not found: {src}\n"
                 "Download it from Kaggle and place it there, or pass its path as an argument.")

    raw = pd.read_csv(src)
    print(f"Read {len(raw)} rows and {len(raw.columns)} columns from {src}")
    if len(raw) != 3000 or len(raw.columns) != 26:
        print("WARNING: the plan expects 3000 rows and 26 columns; check you have the right file.")

    df, aqi = build_health_table(raw)
    validate(df)

    print(f"AQI range: {aqi.min():.1f} to {aqi.max():.1f}")
    print("Rows per category:")
    print(df["aqi_category"].value_counts().reindex(AQI_LABELS).dropna().astype(int).to_string())
    print("Missing values per column:", df.isna().sum().to_dict())

    write_csv_safely(df, dst)
    print(f"Saved {dst} ({len(df)} rows, {len(df.columns)} columns)")


if __name__ == "__main__":
    main()
