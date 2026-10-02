import numpy as np
import pandas as pd

raw = pd.read_csv("data/page3.csv")
print("Rows in raw file:", len(raw))

cols = ["name", "sector", "subsector", "sourceType", "gas", "emissionsQuantity", "assetType", "year"]
df = raw[cols].copy()
print("Missing values in the columns we use:")
print(df.isna().sum())

df = df.rename(columns={
    "name": "location",
    "sourceType": "source_type",
    "gas": "pollutant",
    "emissionsQuantity": "emission_level",
    "assetType": "asset_type",
})

n = len(df)
df = df.dropna(subset=["location", "sector", "source_type", "year", "emission_level"])
print("Rows dropped because a key value was missing:", n - len(df))

df["asset_type"] = df["asset_type"].replace("", np.nan)
df["asset_type"] = df["asset_type"].fillna("Unknown")

b = df[(df["sector"] == "buildings") & (df["source_type"] == "gadm-aggregation")]
o = df[(df["sector"] != "buildings") & (df["source_type"] == "point-source")]
df = pd.concat([b, o])
print("Rows kept after removing double counted rows:", len(df))

df["year"] = df["year"].astype(int)
df["emission_level"] = df["emission_level"].round(2)
df = df.reset_index(drop=True)
df.insert(0, "record_id", range(1, len(df) + 1))
df = df[["record_id", "year", "location", "sector", "subsector", "source_type", "pollutant", "emission_level", "asset_type"]]

print("Missing values left:", int(df.isna().sum().sum()))
df.to_csv("data/page3.csv", index=False)
print("Saved data/page3.csv with", len(df), "rows and", len(df.columns), "columns")