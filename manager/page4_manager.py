"""Page 4 (Health Impact) data manager.

HealthImpactManager extends the team's shared CSVManager:
  * CSVManager  -> how to manage *a* CSV (protected _data, load, safe temp-file save,
                   generic create/read/update/delete, record_id checks)
  * this class  -> the health-specific rules: validation of dates, counts, area and
                   AQI category, filtering/searching/sorting, statistics, chart data
                   and the text report.

The Streamlit page only talks to this class; it never edits the CSV itself.
"""
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path

import numpy as np
import pandas as pd

from manager.csv_manager import CSVManager

# Resolved from this file's location, so it works from any working directory.
DEFAULT_FILE = Path(__file__).resolve().parents[1] / "data" / "page4.csv"

FIELDS = ["record_id", "date", "area", "respiratory_cases", "hospital_visits", "aqi_category"]
EDITABLE_FIELDS = FIELDS[1:]  # everything except record_id
COUNT_FIELDS = ["respiratory_cases", "hospital_visits"]
AQI_CATEGORIES = [
    "Good",
    "Moderate",
    "Unhealthy for Sensitive Groups",
    "Unhealthy",
    "Very Unhealthy",
    "Hazardous",
]
DATE_FORMAT = "%Y-%m-%d"

LABELS = {
    "record_id": "Record ID",
    "date": "Date",
    "area": "Area",
    "respiratory_cases": "Respiratory cases",
    "hospital_visits": "Hospital visits",
    "aqi_category": "AQI category",
}


# --------------------------------------------------------------------------
# Single-value validators. Each returns the cleaned value or raises ValueError.
# --------------------------------------------------------------------------
def _is_missing(value):
    return value is None or value is pd.NA or value is pd.NaT or (isinstance(value, float) and np.isnan(value))


def _whole_number(value, label):
    """Parse a whole number (5, 5.0, '5' are fine; 5.5, 'abc', True are not)."""
    if _is_missing(value) or (isinstance(value, str) and value.strip() == ""):
        raise ValueError(f"{label} is required.")
    if isinstance(value, (bool, np.bool_)):
        raise ValueError(f"{label} must be a whole number.")
    try:
        number = Decimal(str(value).strip())
    except InvalidOperation:
        raise ValueError(f"{label} must be a whole number.") from None
    if not number.is_finite() or number != number.to_integral_value():
        raise ValueError(f"{label} must be a whole number.")
    return int(number)


def clean_record_id(value):
    rid = _whole_number(value, "Record ID")
    if rid < 1:
        raise ValueError("Record ID must be a positive whole number.")
    return rid


def clean_date(value):
    """Accept a date/datetime or a 'YYYY-MM-DD' string; return 'YYYY-MM-DD'."""
    if _is_missing(value):
        raise ValueError("Date is required.")
    if isinstance(value, datetime):  # check before date: datetime is a subclass of date
        return value.date().isoformat()
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, str):
        try:
            return datetime.strptime(value.strip(), DATE_FORMAT).date().isoformat()
        except ValueError:
            pass
    raise ValueError("Date must be a valid calendar date in YYYY-MM-DD format.")


def clean_area(value):
    if not isinstance(value, str) or value.strip() == "":
        raise ValueError("Area cannot be empty.")
    return value.strip()


def clean_count(value, label):
    n = _whole_number(value, label)
    if n < 0:
        raise ValueError(f"{label} cannot be negative.")
    return n


def clean_category(value):
    if not isinstance(value, str) or value.strip() not in AQI_CATEGORIES:
        raise ValueError("AQI category must be one of: " + ", ".join(AQI_CATEGORIES) + ".")
    return value.strip()


_CLEANERS = {
    "date": clean_date,
    "area": clean_area,
    "respiratory_cases": lambda v: clean_count(v, LABELS["respiratory_cases"]),
    "hospital_visits": lambda v: clean_count(v, LABELS["hospital_visits"]),
    "aqi_category": clean_category,
}


def _fmt(value, digits=2):
    """Format a statistic for the report; None means it could not be calculated."""
    if value is None:
        return "N/A"
    if isinstance(value, (int, np.integer)):
        return f"{int(value):,}"
    return f"{value:,.{digits}f}"


class HealthImpactManager(CSVManager):
    def __init__(self, file_path=DEFAULT_FILE):
        super().__init__(file_path, FIELDS)

    # ------------------------------------------------------------------
    # Loading
    # ------------------------------------------------------------------
    def load_data(self):
        """Load the CSV through CSVManager, then check and tidy the health columns."""
        previous = self._data
        try:
            raw = super().load_data()  # missing file / empty file / bad parse / missing columns
            cleaned = self._prepare_loaded(raw)
        except (FileNotFoundError, ValueError):
            self._data = previous  # never keep half-loaded data
            raise
        else:
            self._data = cleaned
        return self.data

    def _prepare_loaded(self, df):
        extra = [c for c in df.columns if c not in FIELDS]
        if extra:
            raise ValueError("CSV has unexpected columns: " + ", ".join(extra))
        df = df[FIELDS].copy()

        # record_id: whole, positive, unique
        ids = pd.to_numeric(df["record_id"], errors="coerce")
        if ids.isna().any() or ((ids % 1) != 0).any() or (ids < 1).any():
            raise ValueError("record_id must contain positive whole numbers with no blanks.")
        if ids.duplicated().any():
            raise ValueError("record_id contains duplicate values.")
        df["record_id"] = ids.astype("int64")

        # date: strict YYYY-MM-DD, re-saved in that same format
        parsed = pd.to_datetime(df["date"], format=DATE_FORMAT, errors="coerce")
        if parsed.isna().any():
            raise ValueError(f"{int(parsed.isna().sum())} row(s) have a missing or invalid date (expected YYYY-MM-DD).")
        df["date"] = parsed.dt.strftime(DATE_FORMAT)

        # area: text, not blank
        if df["area"].isna().any() or (df["area"].astype(str).str.strip() == "").any():
            raise ValueError("area cannot be blank.")
        df["area"] = df["area"].astype(str).str.strip()

        # counts: whole, non-negative. A blank stays missing (<NA>) - it is NOT turned into 0.
        for col in COUNT_FIELDS:
            nums = pd.to_numeric(df[col], errors="coerce")
            if (nums.isna() & df[col].notna()).any():
                raise ValueError(f"{col} contains non-numeric values.")
            present = nums.dropna()
            if ((present % 1) != 0).any() or (present < 0).any():
                raise ValueError(f"{col} must contain non-negative whole numbers.")
            df[col] = nums.astype("Int64")

        # aqi_category: only the six accepted names
        if not df["aqi_category"].isin(AQI_CATEGORIES).all():
            raise ValueError("aqi_category contains values that are not valid AQI categories.")
        return df.reset_index(drop=True)

    def _require_loaded(self):
        if list(self._data.columns) != FIELDS:
            raise ValueError("Data is not loaded. Call load_data() first.")

    def _write(self, action, *args):
        """Run a CSVManager write. If anything fails, put the in-memory data back as it was."""
        snapshot = self._data.copy()
        try:
            result = action(*args)
        except Exception:
            self._data = snapshot
            raise
        self._data["record_id"] = self._data["record_id"].astype("int64")
        for col in COUNT_FIELDS:
            self._data[col] = self._data[col].astype("Int64")
        return result

    def next_id(self):
        if self._data.empty:
            return 1
        return int(self._data["record_id"].max()) + 1

    # ------------------------------------------------------------------
    # Create / Read / Update / Delete
    # ------------------------------------------------------------------
    def create(self, rec):
        """Validate a new record, then let CSVManager add it and save. record_id is optional."""
        if not isinstance(rec, dict):
            raise TypeError("Record must be provided as a dictionary.")
        self._require_loaded()
        unknown = [k for k in rec if k not in FIELDS]
        if unknown:
            raise ValueError("Unknown field(s): " + ", ".join(unknown))

        rid = self.next_id() if _is_missing(rec.get("record_id")) else clean_record_id(rec["record_id"])
        clean = {"record_id": rid}
        for col in EDITABLE_FIELDS:
            clean[col] = _CLEANERS[col](rec.get(col))
        # CSVManager.create rejects a duplicate record_id and saves safely.
        return self._write(super().create, clean)

    def read(self, areas=None, categories=None, start_date=None, end_date=None,
             search=None, sort_by=None, ascending=True):
        """Return a copy of the data, optionally filtered, searched and sorted.

        None means "no filter" for that argument. An empty list for areas/categories
        means "nothing selected", so no rows match. The stored data is never changed.
        """
        df = self._data.copy()
        if areas is not None:
            df = df[df["area"].isin(list(areas))]
        if categories is not None:
            df = df[df["aqi_category"].isin(list(categories))]

        start = clean_date(start_date) if start_date is not None else None
        end = clean_date(end_date) if end_date is not None else None
        if start and end and start > end:
            raise ValueError("Start date must not be after end date.")
        # Dates are stored as YYYY-MM-DD text, so text comparison is date comparison.
        if start:
            df = df[df["date"] >= start]
        if end:
            df = df[df["date"] <= end]

        term = (search or "").strip()
        if term:
            hit = pd.Series(False, index=df.index)
            for col in df.columns:
                text = df[col].astype("string").fillna("")
                hit |= text.str.contains(term, case=False, regex=False).fillna(False).astype(bool)
            df = df[hit]

        if sort_by is not None:
            if sort_by not in FIELDS:
                raise ValueError(f"Cannot sort by unknown column: {sort_by}")
            df = df.sort_values(sort_by, ascending=ascending, kind="stable", na_position="last")
        return df.reset_index(drop=True)

    def update(self, record_id, changes):
        """Change fields of one record. Only the supplied fields are validated; the ID is fixed."""
        if not isinstance(changes, dict):
            raise TypeError("Updates must be provided as a dictionary.")
        self._require_loaded()
        rid = clean_record_id(record_id)
        self.validate_id(rid)  # CSVManager: "No record found with record_id ..."

        changes = dict(changes)
        if "record_id" in changes:
            if not _is_missing(changes["record_id"]) and clean_record_id(changes["record_id"]) != rid:
                raise ValueError("record_id cannot be changed.")
            del changes["record_id"]
        unknown = [k for k in changes if k not in EDITABLE_FIELDS]
        if unknown:
            raise ValueError("Unknown field(s): " + ", ".join(unknown))
        if not changes:
            raise ValueError("No values were provided for update.")

        clean = {col: _CLEANERS[col](value) for col, value in changes.items()}
        return self._write(super().update, rid, clean)

    def delete(self, record_id):
        """Remove one record (CSVManager rewrites the CSV safely). Returns the deleted row."""
        self._require_loaded()
        rid = clean_record_id(record_id)
        self.validate_id(rid)
        return self._write(super().delete, rid)

    # ------------------------------------------------------------------
    # Statistics, chart data and report
    # ------------------------------------------------------------------
    def summary_stats(self, df=None):
        """Statistics for df (default: all data). Missing health values are skipped, not zeroed.

        A statistic that cannot be calculated (e.g. no rows) is returned as None.
        """
        df = self._data if df is None else df
        stats = {
            "records": int(len(df)),
            "total_respiratory": None, "total_hospital": None,
            "avg_respiratory": None, "avg_hospital": None,
            "min_respiratory": None, "max_respiratory": None,
            "top_area": None, "top_area_cases": None, "common_category": None,
            "missing_respiratory": 0, "missing_hospital": 0,
        }
        if df.empty:
            return stats

        resp = df["respiratory_cases"].to_numpy(dtype=float, na_value=np.nan)
        hosp = df["hospital_visits"].to_numpy(dtype=float, na_value=np.nan)
        resp_ok, hosp_ok = resp[~np.isnan(resp)], hosp[~np.isnan(hosp)]
        stats["missing_respiratory"] = int(np.isnan(resp).sum())
        stats["missing_hospital"] = int(np.isnan(hosp).sum())

        if resp_ok.size:
            stats.update(total_respiratory=int(resp_ok.sum()), avg_respiratory=float(np.mean(resp_ok)),
                         min_respiratory=int(np.min(resp_ok)), max_respiratory=int(np.max(resp_ok)))
            # group-by on area: the area with the largest total of respiratory cases
            by_area = df.assign(_r=resp).groupby("area")["_r"].sum(min_count=1).dropna()
            if not by_area.empty:
                stats["top_area"] = str(by_area.idxmax())
                stats["top_area_cases"] = int(by_area.max())
        if hosp_ok.size:
            stats.update(total_hospital=int(hosp_ok.sum()), avg_hospital=float(np.mean(hosp_ok)))

        counts = df["aqi_category"].value_counts().sort_index()  # sorted names make ties deterministic
        if not counts.empty:
            stats["common_category"] = str(counts.idxmax())
        return stats

    def average_by_area(self, df, column):
        """Average of a count column per area (rows with a missing value are left out)."""
        out = df.assign(_v=df[column].astype(float)).groupby("area")["_v"].mean().dropna()
        return out.rename(column).round(2).reset_index()

    def total_cases_by_date(self, df):
        """Total respiratory cases for each date, in date order."""
        out = df.assign(_v=df["respiratory_cases"].astype(float)).groupby("date")["_v"].sum(min_count=1).dropna()
        out = out.rename("respiratory_cases").reset_index()
        out["date"] = pd.to_datetime(out["date"], format=DATE_FORMAT)
        return out.sort_values("date").reset_index(drop=True)

    def average_cases_by_category(self, df):
        """Average respiratory cases per AQI category, in AQI order (Good -> Hazardous)."""
        cat = pd.Categorical(df["aqi_category"], categories=AQI_CATEGORIES, ordered=True)
        out = df.assign(_v=df["respiratory_cases"].astype(float), _c=cat).groupby("_c", observed=True)["_v"].mean().dropna()
        out = out.rename("respiratory_cases").round(2).reset_index().rename(columns={"_c": "aqi_category"})
        out["aqi_category"] = out["aqi_category"].astype(str)
        return out

    def export_report(self, df=None, filters=None):
        """Plain-text report for df (pass the filtered rows). filters: dict (or text) of active filters."""
        df = self._data if df is None else df
        s = self.summary_stats(df)
        if isinstance(filters, dict) and filters:
            filter_lines = [f"  - {name}: {value}" for name, value in filters.items()]
        elif filters:
            filter_lines = [f"  - {filters}"]
        else:
            filter_lines = ["  - None (all records)"]

        lines = [
            "Health Impact Report",
            "====================",
            "Generated: " + datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            f"Rows matching the current filters: {s['records']:,}",
            "Active filters:",
            *filter_lines,
            "",
            "Health statistics (missing values are excluded, never counted as 0)",
            f"  Total respiratory cases:   {_fmt(s['total_respiratory'])}",
            f"  Total hospital visits:     {_fmt(s['total_hospital'])}",
            f"  Average respiratory cases: {_fmt(s['avg_respiratory'])}",
            f"  Average hospital visits:   {_fmt(s['avg_hospital'])}",
            f"  Minimum respiratory cases: {_fmt(s['min_respiratory'])}",
            f"  Maximum respiratory cases: {_fmt(s['max_respiratory'])}",
            "  Area with most respiratory cases: "
            + ("N/A" if s["top_area"] is None else f"{s['top_area']} ({_fmt(s['top_area_cases'])} cases)"),
            f"  Most common AQI category:  {s['common_category'] or 'N/A'}",
        ]
        if s["missing_respiratory"] or s["missing_hospital"]:
            lines += [
                "",
                "Data quality note",
                f"  Rows with missing respiratory cases (excluded): {s['missing_respiratory']}",
                f"  Rows with missing hospital visits (excluded):   {s['missing_hospital']}",
            ]
        return "\n".join(lines)
