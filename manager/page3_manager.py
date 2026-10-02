from datetime import datetime
import math

import pandas as pd

from manager.csv_manager import CSVManager

FIELDS = [
    "record_id", "year", "location", "sector", "subsector",
    "source_type", "pollutant", "emission_level", "asset_type",
]
SECTORS = ["buildings", "manufacturing", "mineral-extraction", "power", "transportation"]
TYPES = ["gadm-aggregation", "point-source"]
YEARS = [2024, 2025, 2026]


class PollutionSourceManager(CSVManager):
    def __init__(self, file_path="data/page3.csv"):
        super().__init__(file_path, FIELDS)

    def load_data(self):
        super().load_data()
        self._data["record_id"] = pd.to_numeric(self._data["record_id"], errors="coerce")
        self._data["year"] = pd.to_numeric(self._data["year"], errors="coerce")
        self._data["emission_level"] = pd.to_numeric(self._data["emission_level"], errors="coerce")

        if self._data[["record_id", "year", "emission_level"]].isna().any().any():
            raise ValueError("The processed CSV has invalid ID, year or emission values.")

        self._data["record_id"] = self._data["record_id"].astype(int)
        self._data["year"] = self._data["year"].astype(int)
        return self.show_assets(self._data)

    def show_assets(self, df):
        out = df.copy()
        out["asset_type"] = out["asset_type"].fillna("Unknown")
        out.loc[out["asset_type"].astype(str).str.strip() == "", "asset_type"] = "Unknown"
        return out

    def next_id(self):
        if self._data.empty:
            return 1
        return int(self._data["record_id"].max()) + 1

    def check(self, rec):
        if pd.isna(rec["location"]) or str(rec["location"]).strip() == "":
            raise ValueError("Location cannot be blank.")
        if pd.isna(rec["subsector"]) or str(rec["subsector"]).strip() == "":
            raise ValueError("Subsector cannot be blank.")
        if rec["year"] not in YEARS:
            raise ValueError("Year must be 2024, 2025 or 2026.")
        if rec["sector"] not in SECTORS:
            raise ValueError("Sector is not allowed.")
        if rec["source_type"] not in TYPES:
            raise ValueError("Source type is not allowed.")
        if rec["pollutant"] != "pm2_5":
            raise ValueError("Pollutant must be pm2_5.")

        try:
            emission = float(rec["emission_level"])
        except (TypeError, ValueError):
            raise ValueError("Emission level must be a number.")
        if not math.isfinite(emission) or emission < 0:
            raise ValueError("Emission must be a finite, non-negative number.")

    def is_duplicate(self, rec):
        same = self._data[
            (self._data["year"] == rec["year"])
            & (self._data["location"] == rec["location"])
            & (self._data["sector"] == rec["sector"])
            & (self._data["subsector"] == rec["subsector"])
            & (self._data["source_type"] == rec["source_type"])
        ]
        return not same.empty

    def create(self, rec):
        rec = dict(rec)
        self.check(rec)
        if self.is_duplicate(rec):
            raise ValueError("This record already exists.")
        rec["record_id"] = int(rec["record_id"])
        rec["year"] = int(rec["year"])
        rec["emission_level"] = float(rec["emission_level"])
        if rec["asset_type"] is None or str(rec["asset_type"]).strip() == "":
            rec["asset_type"] = pd.NA
        return super().create(rec)

    def update(self, record_id, changes):
        row = self._data.loc[self.validate_id(record_id)].to_dict()
        row.update(changes)
        self.check(row)
        changes = dict(changes)
        if changes.get("asset_type") is None or str(changes.get("asset_type", "")).strip() == "":
            changes["asset_type"] = pd.NA
        return super().update(record_id, changes)

    def filter_data(self, sectors, types, first_year, last_year, text):
        data = self._data
        data = data[data["sector"].isin(sectors)]
        data = data[data["source_type"].isin(types)]
        data = data[data["year"].between(first_year, last_year)]
        if text:
            data = data[data["location"].str.contains(text, case=False, regex=False, na=False)]
        return self.show_assets(data.reset_index(drop=True))

    def sort_data(self, df, column, ascending):
        return df.sort_values(column, ascending=ascending).reset_index(drop=True)

    def stats(self, df):
        if df.empty:
            return {"count": 0, "mean": None, "max": None, "min": None, "top": "-"}
        top = df.groupby("location")["emission_level"].sum().idxmax()
        return {
            "count": len(df),
            "mean": float(df["emission_level"].mean()),
            "max": float(df["emission_level"].max()),
            "min": float(df["emission_level"].min()),
            "top": top,
        }

    def by_sector(self, df):
        return df.groupby("sector")["emission_level"].sum().reset_index()

    def by_type(self, df):
        return df.groupby("source_type").size().reset_index(name="records")

    def top_locations(self, df, count):
        result = df.groupby("location")["emission_level"].mean().reset_index()
        return result.sort_values("emission_level", ascending=False).head(count)

    def by_year(self, df):
        return df.groupby(["year", "sector"])["emission_level"].sum().reset_index()

    def report(self, df, filters):
        summary = self.stats(df)
        lines = [
            "Pollution Sources Report",
            "Time: " + datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "Rows: " + str(summary["count"]),
            "Filters: " + filters,
            "Mean emission: " + str(summary["mean"]),
            "Minimum emission: " + str(summary["min"]),
            "Maximum emission: " + str(summary["max"]),
            "Top location: " + str(summary["top"]),
            "Total emission by sector:",
        ]
        for _, row in self.by_sector(df).iterrows():
            lines.append("  " + str(row["sector"]) + ": " + str(round(row["emission_level"], 2)))
        lines.append("Records by source type:")
        for _, row in self.by_type(df).iterrows():
            lines.append("  " + str(row["source_type"]) + ": " + str(row["records"]))
        return "\n".join(lines)
