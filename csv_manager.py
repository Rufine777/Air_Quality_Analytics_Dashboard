from pathlib import Path
import os
import tempfile

import pandas as pd


class CSVManager:
#    Shared base class for managing CSV-backed datasets.

    def __init__(self, file_path, required_columns=None):
        self.file_path = Path(file_path)
        self.required_columns = list(required_columns or [])
        self._data = pd.DataFrame()

    @property
    def data(self):
        return self._data

    def load_data(self):
        if not self.file_path.exists():
            raise FileNotFoundError(
                f"CSV file not found: {self.file_path}"
            )

        try:
            data = pd.read_csv(self.file_path)
        except pd.errors.EmptyDataError as exc:
            raise ValueError(
                f"CSV file is empty: {self.file_path}"
            ) from exc
        except pd.errors.ParserError as exc:
            raise ValueError(
                f"Could not parse CSV file: {self.file_path}"
            ) from exc

        if data.empty:
            raise ValueError(
                f"CSV file contains no records: {self.file_path}"
            )

        self._validate_columns(data)

        self._data = data
        return self._data

    def save_data(self):
#        The data is first written to a temporary file in the same directory and then atomically replaces the original file.
        self.file_path.parent.mkdir(parents=True, exist_ok=True)

        temp_path = None

        try:
            with tempfile.NamedTemporaryFile(
                mode="w",
                suffix=".csv",
                prefix=f".{self.file_path.stem}_",
                dir=self.file_path.parent,
                delete=False,
                encoding="utf-8",
                newline="",
            ) as temp_file:
                temp_path = Path(temp_file.name)
                self._data.to_csv(temp_file, index=False)

            os.replace(temp_path, self.file_path)

        except (OSError, IOError) as exc:
            raise OSError(
                f"Could not safely save CSV file: {self.file_path}"
            ) from exc

        finally:
            if temp_path is not None and temp_path.exists():
                try:
                    temp_path.unlink()
                except OSError:
                    pass

        return True

    def create(self, record):
#        Add one record to the DataFrame and save it.
        if not isinstance(record, dict):
            raise TypeError("Record must be provided as a dictionary.")

        self._validate_record_id(record)

        new_row = pd.DataFrame([record])

        if self._data.empty:
            self._data = new_row
        else:
            self._data = pd.concat(
                [self._data, new_row],
                ignore_index=True
            )

        self.save_data()
        return new_row.iloc[0]

    def read(self):
        #Return the current dataset
        return self._data.copy()

    def update(self, record_id, updates):
#        Update a record using its record_id.
        index = self.validate_id(record_id)

        if not isinstance(updates, dict):
            raise TypeError("Updates must be provided as a dictionary.")

        if not updates:
            raise ValueError("No values were provided for update.")

        for column, value in updates.items():
            if column == "record_id":
                raise ValueError("record_id cannot be changed.")

            if column not in self._data.columns:
                raise ValueError(f"Unknown column: {column}")

            self._data.at[index, column] = value

        self.save_data()
        return self._data.loc[index].copy()

    def delete(self, record_id):

#        Delete a record using its record_id.

        index = self.validate_id(record_id)

        deleted_record = self._data.loc[index].copy()
        self._data = self._data.drop(index).reset_index(drop=True)

        self.save_data()
        return deleted_record

    def validate_id(self, record_id):
#        Validate and locate a record by record_id.
        if "record_id" not in self._data.columns:
            raise ValueError("CSV must contain a 'record_id' column.")

        matches = self._data[
            self._data["record_id"] == record_id
        ].index

        if len(matches) == 0:
            raise ValueError(
                f"No record found with record_id: {record_id}"
            )

        return matches[0]

    def _validate_columns(self, data):
#       Check whether all required columns exist.
        if not self.required_columns:
            return

        missing_columns = [
            column
            for column in self.required_columns
            if column not in data.columns
        ]

        if missing_columns:
            raise ValueError(
                "CSV is missing required columns: "
                + ", ".join(missing_columns)
            )

    def _validate_record_id(self, record):
#       Check that record_id exists and is not duplicated.
        if "record_id" not in record:
            raise ValueError("record_id is required.")

        if "record_id" in self._data.columns:
            if record["record_id"] in self._data["record_id"].values:
                raise ValueError(
                    f"Duplicate record_id: {record['record_id']}"
                )
