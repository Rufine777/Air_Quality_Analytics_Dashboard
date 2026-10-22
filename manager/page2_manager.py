from datetime import datetime
import math
import pandas as pd

from manager.csv_manager import CSVManager

WEATHER_FIELDS = [
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

INDIAN_CITIES = [
    "Ahmedabad",
    "Bangalore",
    "Chennai",
    "Delhi",
    "Hyderabad",
    "Jaipur",
    "Kolkata",
    "Lucknow",
    "Mumbai",
    "Pune",
]

WMO_CODE_MAP = {
    0: "Clear sky",
    1: "Mainly clear",
    2: "Partly cloudy",
    3: "Overcast",
    45: "Fog",
    48: "Depositing rime fog",
    51: "Light drizzle",
    53: "Moderate drizzle",
    55: "Dense drizzle",
    61: "Slight rain",
    63: "Moderate rain",
    65: "Heavy rain",
    71: "Slight snow",
    73: "Moderate snow",
    75: "Heavy snow",
    80: "Slight rain showers",
    81: "Moderate rain showers",
    82: "Violent rain showers",
    95: "Thunderstorm",
    96: "Thunderstorm with slight hail",
    99: "Thunderstorm with heavy hail",
}


class WeatherManager(CSVManager):
    """
    Manager for weather condition records.
    Extends the team's shared CSVManager base class.
    """

    def __init__(self, file_path="data/page2.csv"):
        super().__init__(file_path, WEATHER_FIELDS)

    def load_data(self):
        """
        Loads CSV data with full try/except/else/finally handling and parses numeric columns.
        """
        try:
            super().load_data()
        except Exception:
            raise
        else:
            # Enforce clean data types
            self._data["record_id"] = pd.to_numeric(self._data["record_id"], errors="coerce")
            self._data["temp_max"] = pd.to_numeric(self._data["temp_max"], errors="coerce")
            self._data["temp_min"] = pd.to_numeric(self._data["temp_min"], errors="coerce")
            self._data["feels_like"] = pd.to_numeric(self._data["feels_like"], errors="coerce")
            self._data["rainfall"] = pd.to_numeric(self._data["rainfall"], errors="coerce")
            self._data["precipitation"] = pd.to_numeric(self._data["precipitation"], errors="coerce")
            self._data["weather_code"] = pd.to_numeric(self._data["weather_code"], errors="coerce")
            self._data["wind_speed"] = pd.to_numeric(self._data["wind_speed"], errors="coerce")
            self._data["wind_gusts"] = pd.to_numeric(self._data["wind_gusts"], errors="coerce")
            self._data["wind_direction"] = pd.to_numeric(self._data["wind_direction"], errors="coerce")

            # Validate record_id has no NaNs
            if self._data["record_id"].isna().any():
                raise ValueError("Encountered invalid or non-numeric record_id values in CSV.")

            self._data["record_id"] = self._data["record_id"].astype(int)
            self._data["weather_code"] = self._data["weather_code"].fillna(0).astype(int)
            self._data["wind_direction"] = self._data["wind_direction"].fillna(0).astype(int)
            return self.data
        finally:
            pass

    def next_id(self):
        """
        Returns the next available integer record_id.
        """
        if self._data.empty or "record_id" not in self._data.columns:
            return 1
        return int(self._data["record_id"].max()) + 1

    def validate_record(self, rec, is_new=True):
        """
        Validates record fields and enforces business rules for weather measurements.
        Returns a sanitized dictionary with proper types.
        """
        if not isinstance(rec, dict):
            raise TypeError("Record must be provided as a dictionary.")

        # City check
        city = str(rec.get("city", "")).strip()
        if not city:
            raise ValueError("City name cannot be blank.")

        # Date check
        raw_date = str(rec.get("date", "")).strip()
        if not raw_date:
            raise ValueError("Observation date cannot be blank.")
        try:
            parsed_date = datetime.strptime(raw_date, "%Y-%m-%d")
            formatted_date = parsed_date.strftime("%Y-%m-%d")
        except ValueError as e:
            raise ValueError(f"Invalid date format '{raw_date}'. Expected YYYY-MM-DD.") from e

        # Numeric validations helper
        def parse_float(val, name, min_val=None, max_val=None):
            try:
                num = float(val)
            except (TypeError, ValueError) as err:
                raise ValueError(f"{name} must be a valid number.") from err
            if not math.isfinite(num):
                raise ValueError(f"{name} must be a finite number.")
            if min_val is not None and num < min_val:
                raise ValueError(f"{name} cannot be less than {min_val}.")
            if max_val is not None and num > max_val:
                raise ValueError(f"{name} cannot exceed {max_val}.")
            return round(num, 2)

        def parse_int(val, name, min_val=None, max_val=None):
            try:
                num = int(val)
            except (TypeError, ValueError) as err:
                raise ValueError(f"{name} must be an integer.") from err
            if min_val is not None and num < min_val:
                raise ValueError(f"{name} cannot be less than {min_val}.")
            if max_val is not None and num > max_val:
                raise ValueError(f"{name} cannot exceed {max_val}.")
            return num

        temp_max = parse_float(rec.get("temp_max"), "Maximum temperature", min_val=-30, max_val=60)
        temp_min = parse_float(rec.get("temp_min"), "Minimum temperature", min_val=-40, max_val=50)
        if temp_max < temp_min:
            raise ValueError(
                f"Maximum temperature ({temp_max}°C) cannot be less than minimum temperature ({temp_min}°C)."
            )

        feels_like = parse_float(rec.get("feels_like"), "Apparent temperature", min_val=-40, max_val=65)
        rainfall = parse_float(rec.get("rainfall"), "Rainfall", min_val=0)
        precipitation = parse_float(rec.get("precipitation"), "Precipitation", min_val=0)
        weather_code = parse_int(rec.get("weather_code", 0), "Weather code", min_val=0, max_val=100)
        wind_speed = parse_float(rec.get("wind_speed"), "Wind speed", min_val=0)
        wind_gusts = parse_float(rec.get("wind_gusts"), "Wind gusts", min_val=0)
        wind_direction = parse_int(rec.get("wind_direction", 0), "Wind direction", min_val=0, max_val=360)

        cleaned = {
            "city": city,
            "date": formatted_date,
            "temp_max": temp_max,
            "temp_min": temp_min,
            "feels_like": feels_like,
            "rainfall": rainfall,
            "precipitation": precipitation,
            "weather_code": weather_code,
            "wind_speed": wind_speed,
            "wind_gusts": wind_gusts,
            "wind_direction": wind_direction,
        }

        if is_new:
            if "record_id" in rec and rec["record_id"] is not None:
                cleaned["record_id"] = parse_int(rec["record_id"], "record_id", min_val=1)
            else:
                cleaned["record_id"] = self.next_id()

        return cleaned

    def is_duplicate(self, city, date_str, exclude_id=None):
        """
        Checks whether a record for the specified city and date already exists.
        """
        if self._data.empty:
            return False
        mask = (self._data["city"].str.lower() == str(city).strip().lower()) & (
            self._data["date"].astype(str) == str(date_str).strip()
        )
        if exclude_id is not None:
            mask = mask & (self._data["record_id"] != int(exclude_id))
        return not self._data[mask].empty

    def create(self, rec):
        """
        Validates, checks for duplicates, and adds a new weather observation record.
        Returns the created record.
        """
        validated = self.validate_record(rec, is_new=True)
        if self.is_duplicate(validated["city"], validated["date"]):
            raise ValueError(
                f"A record for city '{validated['city']}' on date '{validated['date']}' already exists."
            )
        return super().create(validated)

    def read(self):
        """
        Returns a fresh copy of the current weather data.
        """
        return super().read()

    def update(self, record_id, changes):
        """
        Updates an existing weather record by record_id after validation.
        Returns the updated record.
        """
        idx = self.validate_id(record_id)
        current = self._data.loc[idx].to_dict()
        current.update(changes)

        validated = self.validate_record(current, is_new=False)
        if self.is_duplicate(validated["city"], validated["date"], exclude_id=record_id):
            raise ValueError(
                f"Another record for city '{validated['city']}' on date '{validated['date']}' already exists."
            )

        # Update columns
        validated_changes = {k: v for k, v in validated.items() if k != "record_id"}
        return super().update(record_id, validated_changes)

    def delete(self, record_id):
        """
        Deletes a weather record by record_id.
        Returns the deleted record.
        """
        return super().delete(record_id)

    def filter_data(self, cities=None, start_date=None, end_date=None, temp_range=None, search_text=None):
        """
        Filters the dataset based on city, date range, temperature range, and text search.
        Returns a filtered DataFrame.
        """
        df = self._data.copy()
        if df.empty:
            return df

        if cities:
            df = df[df["city"].isin(cities)]

        if start_date:
            s_str = start_date.strftime("%Y-%m-%d") if hasattr(start_date, "strftime") else str(start_date)
            df = df[df["date"].astype(str) >= s_str]

        if end_date:
            e_str = end_date.strftime("%Y-%m-%d") if hasattr(end_date, "strftime") else str(end_date)
            df = df[df["date"].astype(str) <= e_str]

        if temp_range and len(temp_range) == 2:
            t_min, t_max = temp_range
            df = df[(df["temp_max"] >= t_min) & (df["temp_max"] <= t_max)]

        if search_text:
            query = str(search_text).strip()
            if query:
                df = df[
                    df["city"].str.contains(query, case=False, regex=False, na=False)
                    | df["date"].astype(str).str.contains(query, case=False, regex=False, na=False)
                ]

        return df.reset_index(drop=True)

    def sort_data(self, df, column, ascending=True):
        """
        Sorts the given DataFrame by the specified column.
        """
        if df.empty or column not in df.columns:
            return df
        return df.sort_values(by=column, ascending=ascending).reset_index(drop=True)

    def summary_stats(self, df=None):
        """
        Computes the mandatory 9 summary statistics using Pandas and NumPy:
        1. Mean maximum temperature
        2. Mean minimum temperature
        3. Mean apparent temperature
        4. Total rainfall
        5. Total precipitation
        6. Maximum wind speed
        7. Maximum wind gust
        8. Number of records
        9. City with the highest average temperature
        """
        target = self._data if df is None else df
        if target.empty:
            return {
                "count": 0,
                "mean_temp_max": None,
                "mean_temp_min": None,
                "mean_feels_like": None,
                "total_rainfall": 0.0,
                "total_precipitation": 0.0,
                "max_wind_speed": None,
                "max_wind_gust": None,
                "top_temp_city": "—",
            }

        # Explicitly handle missing numerical values (exclude from calculation)
        clean_temp = target.dropna(subset=["temp_max", "temp_min", "feels_like"])
        clean_rain = target.dropna(subset=["rainfall", "precipitation"])
        clean_wind = target.dropna(subset=["wind_speed", "wind_gusts"])

        mean_temp_max = float(clean_temp["temp_max"].mean()) if not clean_temp.empty else None
        mean_temp_min = float(clean_temp["temp_min"].mean()) if not clean_temp.empty else None
        mean_feels_like = float(clean_temp["feels_like"].mean()) if not clean_temp.empty else None

        total_rainfall = float(clean_rain["rainfall"].sum()) if not clean_rain.empty else 0.0
        total_precipitation = float(clean_rain["precipitation"].sum()) if not clean_rain.empty else 0.0

        max_wind_speed = float(clean_wind["wind_speed"].max()) if not clean_wind.empty else None
        max_wind_gust = float(clean_wind["wind_gusts"].max()) if not clean_wind.empty else None

        top_city = "—"
        if not clean_temp.empty:
            city_avg = clean_temp.groupby("city")["temp_max"].mean()
            if not city_avg.empty:
                top_city = str(city_avg.idxmax())

        return {
            "count": len(target),
            "mean_temp_max": round(mean_temp_max, 2) if mean_temp_max is not None else None,
            "mean_temp_min": round(mean_temp_min, 2) if mean_temp_min is not None else None,
            "mean_feels_like": round(mean_feels_like, 2) if mean_feels_like is not None else None,
            "total_rainfall": round(total_rainfall, 2),
            "total_precipitation": round(total_precipitation, 2),
            "max_wind_speed": round(max_wind_speed, 2) if max_wind_speed is not None else None,
            "max_wind_gust": round(max_wind_gust, 2) if max_wind_gust is not None else None,
            "top_temp_city": top_city,
        }

    def city_temperature_averages(self, df):
        """
        Returns average temperatures grouped by city.
        """
        if df.empty:
            return pd.DataFrame(columns=["city", "avg_max_temp", "avg_min_temp", "avg_feels_like"])
        grouped = df.groupby("city").agg(
            avg_max_temp=("temp_max", "mean"),
            avg_min_temp=("temp_min", "mean"),
            avg_feels_like=("feels_like", "mean"),
        ).round(2).reset_index()
        return grouped.sort_values(by="avg_max_temp", ascending=False)

    def city_wind_averages(self, df):
        """
        Returns average wind metrics grouped by city.
        """
        if df.empty:
            return pd.DataFrame(columns=["city", "avg_wind_speed", "max_wind_gust"])
        grouped = df.groupby("city").agg(
            avg_wind_speed=("wind_speed", "mean"),
            max_wind_gust=("wind_gusts", "max"),
        ).round(2).reset_index()
        return grouped.sort_values(by="avg_wind_speed", ascending=False)

    def export_report(self, df=None, filters_desc="None"):
        """
        Generates and returns a downloadable plain text summary report.
        """
        target = self._data if df is None else df
        stats = self.summary_stats(target)
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        lines = [
            "=" * 60,
            "        WEATHER CONDITIONS & ENVIRONMENTAL ANALYTICS REPORT",
            "=" * 60,
            f"Generated At    : {timestamp}",
            f"Total Records   : {stats['count']}",
            f"Active Filters  : {filters_desc}",
            "-" * 60,
            "SUMMARY STATISTICS:",
            f"  • Mean Maximum Temperature : {stats['mean_temp_max']} °C" if stats['mean_temp_max'] is not None else "  • Mean Maximum Temperature : N/A",
            f"  • Mean Minimum Temperature : {stats['mean_temp_min']} °C" if stats['mean_temp_min'] is not None else "  • Mean Minimum Temperature : N/A",
            f"  • Mean Apparent Temperature: {stats['mean_feels_like']} °C" if stats['mean_feels_like'] is not None else "  • Mean Apparent Temperature: N/A",
            f"  • Total Rainfall           : {stats['total_rainfall']} mm",
            f"  • Total Precipitation      : {stats['total_precipitation']} mm",
            f"  • Maximum Wind Speed       : {stats['max_wind_speed']} km/h" if stats['max_wind_speed'] is not None else "  • Maximum Wind Speed       : N/A",
            f"  • Maximum Wind Gust        : {stats['max_wind_gust']} km/h" if stats['max_wind_gust'] is not None else "  • Maximum Wind Gust        : N/A",
            f"  • Hottest City (Average)   : {stats['top_temp_city']}",
            "-" * 60,
            "CITY-WISE TEMPERATURE OVERVIEW:",
        ]

        if not target.empty:
            city_stats = self.city_temperature_averages(target)
            for _, row in city_stats.iterrows():
                lines.append(
                    f"  {row['city']:<15} | Avg Max: {row['avg_max_temp']:>5.1f}°C | "
                    f"Avg Min: {row['avg_min_temp']:>5.1f}°C | Feels Like: {row['avg_feels_like']:>5.1f}°C"
                )
        else:
            lines.append("  No records available.")

        lines.append("=" * 60)
        return "\n".join(lines)
