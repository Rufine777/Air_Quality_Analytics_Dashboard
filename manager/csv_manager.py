from pathlib import Path
import os
import tempfile

import pandas as pd


class CSVManager:

    def __init__(self, file_path, cols=None):
        self.file_path = Path(file_path)
        self.cols = list(cols or [])
        self._data = pd.DataFrame()

    @property
    def data(self):
        return self._data.copy()

    def load_data(self):
        df = None
        try:
            if not self.file_path.exists():
                raise FileNotFoundError(f"CSV file not found: {self.file_path}")
            df = pd.read_csv(self.file_path)
        except pd.errors.EmptyDataError as e:
            raise ValueError(f"CSV file is empty (no header row): {self.file_path}") from e
        except pd.errors.ParserError as e:
            raise ValueError(f"Could not parse CSV file: {self.file_path}") from e
        else:
            self._validate_columns(df)
            self._data = df
        finally:
            pass
        return self.data

    def save_data(self):
        self.file_path.parent.mkdir(parents=True, exist_ok=True)
        tp = None
        try:
            with tempfile.NamedTemporaryFile(
                mode="w",
                suffix=".csv",
                prefix="." + self.file_path.stem + "_",
                dir=self.file_path.parent,
                delete=False,
                encoding="utf-8",
                newline="",
            ) as tf:
                tp = Path(tf.name)
                self._data.to_csv(tf, index=False)
            os.replace(tp, self.file_path)
        except (OSError, IOError) as e:
            raise OSError(f"Could not safely save CSV file: {self.file_path}") from e
        else:
            ok = True
        finally:
            if tp is not None and tp.exists():
                try:
                    tp.unlink()
                except OSError:
                    pass
        return ok

    def create(self, rec):
        if not isinstance(rec, dict):
            raise TypeError("Record must be provided as a dictionary.")

        self._validate_record_id(rec)

        if len(self._data.columns) > 0:
            self._validate_record_columns(rec)

        row = pd.DataFrame([rec])

        if len(self._data) == 0:
            if len(self._data.columns) > 0:
                row = row[list(self._data.columns)]
            self._data = row
        else:
            self._data = pd.concat([self._data, row], ignore_index=True)

        self.save_data()
        return row.iloc[0].copy()

    def read(self):
        return self._data.copy()

    def update(self, rid, upd):
        i = self.validate_id(rid)

        if not isinstance(upd, dict):
            raise TypeError("Updates must be provided as a dictionary.")

        if len(upd) == 0:
            raise ValueError("No values were provided for update.")

        for c in upd:
            if c == "record_id":
                raise ValueError("record_id cannot be changed.")
            if c not in self._data.columns:
                raise ValueError(f"Unknown column: {c}")

        for c, v in upd.items():
            self._data.at[i, c] = v

        self.save_data()
        return self._data.loc[i].copy()

    def delete(self, rid):
        i = self.validate_id(rid)

        old = self._data.loc[i].copy()
        self._data = self._data.drop(i).reset_index(drop=True)

        self.save_data()
        return old

    def validate_id(self, rid):
        if "record_id" not in self._data.columns:
            raise ValueError("CSV must contain a 'record_id' column.")

        m = self._data[self._data["record_id"] == rid].index

        if len(m) == 0:
            raise ValueError(f"No record found with record_id: {rid}")

        return m[0]

    def _validate_columns(self, df):
        if len(self.cols) == 0:
            return

        miss = []
        for c in self.cols:
            if c not in df.columns:
                miss.append(c)

        if len(miss) > 0:
            raise ValueError("CSV is missing required columns: " + ", ".join(miss))

    def _validate_record_columns(self, rec):
        miss = []
        for c in self._data.columns:
            if c not in rec:
                miss.append(c)

        extra = []
        for c in rec:
            if c not in self._data.columns:
                extra.append(c)

        if len(miss) > 0:
            raise ValueError("Record is missing columns: " + ", ".join(miss))
        if len(extra) > 0:
            raise ValueError("Record has unknown columns: " + ", ".join(extra))

    def _validate_record_id(self, rec):
        if "record_id" not in rec:
            raise ValueError("record_id is required.")

        if "record_id" in self._data.columns:
            if rec["record_id"] in self._data["record_id"].values:
                raise ValueError(f"Duplicate record_id: {rec['record_id']}")