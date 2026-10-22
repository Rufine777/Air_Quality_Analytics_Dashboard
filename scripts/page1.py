from pathlib import Path

import pandas as pd

SOURCE_PATH = Path("data/page1.csv")
BACKUP_PATH = Path("data/page1_full_backup.csv")
TARGET_ROWS = 2000
RANDOM_STATE = 42

COLUMN_ORDER = [
    "record_id", "Country", "City", "AQI Value", "AQI Category",
    "CO AQI Value", "CO AQI Category", "Ozone AQI Value", "Ozone AQI Category",
    "NO2 AQI Value", "NO2 AQI Category", "PM2.5 AQI Value", "PM2.5 AQI Category",
]
AQI_VALUE_COLUMNS = [
    "AQI Value", "CO AQI Value", "Ozone AQI Value", "NO2 AQI Value", "PM2.5 AQI Value",
]


def stratified_category_counts(category_counts, target_total):
    raw = category_counts / category_counts.sum() * target_total
    counts = raw.astype(int)
    remainder = target_total - int(counts.sum())
    if remainder > 0:
        fracs = (raw - counts).sort_values(ascending=False)
        for cat in fracs.index[:remainder]:
            counts[cat] += 1
    return counts


def preprocess():
    df = pd.read_csv(SOURCE_PATH)
    print(f"Read {len(df)} rows from {SOURCE_PATH}.")

    if not BACKUP_PATH.exists():
        df.to_csv(BACKUP_PATH, index=False)
        print(f"Saved unmodified backup to {BACKUP_PATH}.")
    else:
        print(f"Backup already exists at {BACKUP_PATH}; leaving it untouched.")

    category_counts = df["AQI Category"].value_counts()
    target_counts = stratified_category_counts(category_counts, TARGET_ROWS)

    sampled_groups = []
    for category, n in target_counts.items():
        group = df[df["AQI Category"] == category]
        sampled_groups.append(group.sample(n=int(n), random_state=RANDOM_STATE))
    sample = pd.concat(sampled_groups).reset_index(drop=True)

    sample.insert(0, "record_id", range(1, len(sample) + 1))
    sample = sample[COLUMN_ORDER]

    for col in AQI_VALUE_COLUMNS:
        sample[col] = sample[col].astype(int)

    sample.to_csv(SOURCE_PATH, index=False)
    print(f"Saved {SOURCE_PATH} with {len(sample)} rows and {len(sample.columns)} columns.")
    print("Category breakdown:")
    print(sample["AQI Category"].value_counts())


if __name__ == "__main__":
    preprocess()
