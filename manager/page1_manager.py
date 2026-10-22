from datetime import datetime

import pandas as pd

from manager.csv_manager import CSVManager

FIELDS = [
    "record_id", "Country", "City", "AQI Value", "AQI Category",
    "CO AQI Value", "CO AQI Category", "Ozone AQI Value", "Ozone AQI Category",
    "NO2 AQI Value", "NO2 AQI Category", "PM2.5 AQI Value", "PM2.5 AQI Category",
]
AQI_CATEGORIES = [
    "Good", "Moderate", "Unhealthy for Sensitive Groups",
    "Unhealthy", "Very Unhealthy", "Hazardous",
]
AQI_VALUE_FIELDS = [
    "AQI Value", "CO AQI Value", "Ozone AQI Value", "NO2 AQI Value", "PM2.5 AQI Value",
]
AQI_CATEGORY_FIELDS = [
    "AQI Category", "CO AQI Category", "Ozone AQI Category", "NO2 AQI Category", "PM2.5 AQI Category",
]


class PollutantRecordManager(CSVManager):
    """
    Manager for global pollutant/AQI readings.
    Extends the team's shared CSVManager base class.
    """

    def __init__(self, file_path="data/page1.csv"):
        super().__init__(file_path, FIELDS)

    def load_data(self):
        """
        Loads CSV data and enforces numeric types on record_id and the 5 AQI value columns.
        Country/City are left as-is since missing values there are legitimate.
        """
        super().load_data()

        self._data["record_id"] = pd.to_numeric(self._data["record_id"], errors="coerce")
        for col in AQI_VALUE_FIELDS:
            self._data[col] = pd.to_numeric(self._data[col], errors="coerce")

        check_cols = ["record_id"] + AQI_VALUE_FIELDS
        if self._data[check_cols].isna().any().any():
            raise ValueError("The CSV contains invalid (non-numeric) record_id or AQI value entries.")

        self._data["record_id"] = self._data["record_id"].astype(int)
        for col in AQI_VALUE_FIELDS:
            self._data[col] = self._data[col].astype(int)

        return self.data

    def next_id(self):
        """
        Returns the next available integer record_id.
        """
        if self._data.empty or "record_id" not in self._data.columns:
            return 1
        return int(self._data["record_id"].max()) + 1

    def validate_record(self, rec, is_new=True):
        """
        Validates record fields and returns a sanitized dictionary with proper types.
        """
        if not isinstance(rec, dict):
            raise TypeError("Record must be provided as a dictionary.")

        city = str(rec.get("City", "")).strip()
        if not city:
            raise ValueError("City cannot be blank.")

        country_raw = rec.get("Country")
        country = "" if country_raw is None else str(country_raw).strip()
        if country.lower() in ("", "nan", "none"):
            country = pd.NA

        def parse_aqi_value(val, name):
            try:
                num = int(val)
            except (TypeError, ValueError) as err:
                raise ValueError(f"{name} must be a whole number.") from err
            if num < 0:
                raise ValueError(f"{name} cannot be negative.")
            return num

        def parse_category(val, name):
            cat = str(val).strip() if val is not None else ""
            if cat not in AQI_CATEGORIES:
                raise ValueError(f"{name} must be one of: {', '.join(AQI_CATEGORIES)}.")
            return cat

        cleaned = {
            "City": city,
            "Country": country,
        }
        for field in AQI_VALUE_FIELDS:
            cleaned[field] = parse_aqi_value(rec.get(field), field)
        for field in AQI_CATEGORY_FIELDS:
            cleaned[field] = parse_category(rec.get(field), field)

        if is_new:
            if rec.get("record_id") is not None:
                cleaned["record_id"] = int(rec["record_id"])
            else:
                cleaned["record_id"] = self.next_id()

        return cleaned

    def is_duplicate(self, country, city, exclude_id=None):
        """
        Case-insensitive duplicate check on (Country, City). Missing Country is treated
        as equal to missing Country.
        """
        if self._data.empty:
            return False

        city_norm = str(city).strip().lower()
        is_country_missing = country is None or pd.isna(country) or str(country).strip() == ""

        data_country = self._data["Country"]
        data_city_norm = self._data["City"].astype(str).str.strip().str.lower()

        if is_country_missing:
            country_mask = data_country.isna()
        else:
            country_norm = str(country).strip().lower()
            country_mask = data_country.astype(str).str.strip().str.lower() == country_norm

        mask = country_mask & (data_city_norm == city_norm)

        if exclude_id is not None:
            mask = mask & (self._data["record_id"] != int(exclude_id))

        return not self._data[mask].empty

    def create(self, rec):
        """
        Validates, checks for duplicates, and adds a new pollutant reading record.
        """
        validated = self.validate_record(rec, is_new=True)
        if self.is_duplicate(validated["Country"], validated["City"]):
            raise ValueError(
                f"A record for Country='{validated['Country']}' and City='{validated['City']}' already exists."
            )
        return super().create(validated)

    def read(self):
        """
        Returns a fresh copy of the current pollutant data.
        """
        return super().read()

    def update(self, record_id, changes):
        """
        Updates an existing pollutant record by record_id after re-validation.
        """
        idx = self.validate_id(record_id)
        current = self._data.loc[idx].to_dict()
        current.update(changes)

        validated = self.validate_record(current, is_new=False)
        if self.is_duplicate(validated["Country"], validated["City"], exclude_id=record_id):
            raise ValueError(
                f"Another record for Country='{validated['Country']}' and City='{validated['City']}' already exists."
            )

        return super().update(record_id, validated)

    def delete(self, record_id):
        """
        Deletes a pollutant record by record_id.
        """
        return super().delete(record_id)

    def filter_data(self, countries=None, categories=None, aqi_range=None, search_text=None):
        """
        Filters the dataset based on country, AQI category, AQI value range, and text search.
        Returns a filtered DataFrame.
        """
        df = self._data.copy()
        if df.empty:
            return df

        if countries:
            df = df[df["Country"].isin(countries)]

        if categories:
            df = df[df["AQI Category"].isin(categories)]

        if aqi_range and len(aqi_range) == 2:
            lo, hi = aqi_range
            df = df[df["AQI Value"].between(lo, hi)]

        if search_text:
            query = str(search_text).strip()
            if query:
                df = df[
                    df["Country"].astype(str).str.contains(query, case=False, regex=False, na=False)
                    | df["City"].astype(str).str.contains(query, case=False, regex=False, na=False)
                ]

        return df.reset_index(drop=True)

    def sort_data(self, df, column, ascending=True):
        """
        Sorts the given DataFrame by the specified column.
        """
        if df.empty or column not in df.columns:
            return df
        return df.sort_values(column, ascending=ascending).reset_index(drop=True)

    def summary_stats(self, df):
        """
        Computes the 4 mandatory summary statistics:
        1. Record count
        2. Mean AQI value
        3. Mean PM2.5 AQI value
        4. Country with the highest mean AQI value (missing Country excluded)
        """
        if df.empty:
            return {
                "count": 0,
                "mean_aqi": None,
                "mean_pm25": None,
                "top_country": "—",
            }

        known_country_df = df.dropna(subset=["Country"])
        top_country = "—"
        if not known_country_df.empty:
            country_avg = known_country_df.groupby("Country")["AQI Value"].mean()
            if not country_avg.empty:
                top_country = str(country_avg.idxmax())

        return {
            "count": len(df),
            "mean_aqi": round(float(df["AQI Value"].mean()), 2),
            "mean_pm25": round(float(df["PM2.5 AQI Value"].mean()), 2),
            "top_country": top_country,
        }

    def country_averages(self, df, metric, top_n):
        """
        Returns the top-N countries by mean of the given metric, excluding missing Country.
        """
        if df.empty:
            return pd.DataFrame(columns=["Country", metric])
        known = df.dropna(subset=["Country"])
        if known.empty:
            return pd.DataFrame(columns=["Country", metric])
        grouped = known.groupby("Country")[metric].mean().round(2).reset_index()
        return grouped.sort_values(metric, ascending=False).head(top_n)

    def category_distribution(self, df):
        """
        Returns AQI Category counts for the current filtered view (includes missing-Country rows).
        """
        if df.empty:
            return pd.DataFrame(columns=["category", "count"])
        result = df["AQI Category"].value_counts().reset_index()
        result.columns = ["category", "count"]
        return result

    def export_report(self, df, filters_desc="None"):
        """
        Generates and returns a downloadable plain text summary report.
        """
        stats = self.summary_stats(df)
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        lines = [
            "=" * 60,
            "            POLLUTANT READINGS ANALYTICS REPORT",
            "=" * 60,
            f"Generated At    : {timestamp}",
            f"Total Records   : {stats['count']}",
            f"Active Filters  : {filters_desc}",
            "-" * 60,
            "SUMMARY STATISTICS:",
            f"  • Mean AQI Value       : {stats['mean_aqi']}" if stats["mean_aqi"] is not None else "  • Mean AQI Value       : N/A",
            f"  • Mean PM2.5 AQI Value : {stats['mean_pm25']}" if stats["mean_pm25"] is not None else "  • Mean PM2.5 AQI Value : N/A",
            f"  • Top Country (by Mean AQI, excl. missing) : {stats['top_country']}",
            "-" * 60,
            "TOP COUNTRY AVERAGES (AQI Value):",
        ]

        if not df.empty:
            top_countries = self.country_averages(df, "AQI Value", 10)
            if top_countries.empty:
                lines.append("  No country data available.")
            else:
                for _, row in top_countries.iterrows():
                    lines.append(f"  {row['Country']:<30} | Avg AQI: {row['AQI Value']:>6.2f}")
        else:
            lines.append("  No records available.")

        lines.append("=" * 60)
        return "\n".join(lines)
