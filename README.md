# The folder Structure is planned as follows:

```
Air_Quality_Dashboard/
├── Home.py
├── csv_manager.py
├── requirements.txt
├── README.md
│
├── data/
│   ├── pollutant_readings.csv
│   ├── weather_conditions.csv
│   ├── pollution_sources.csv
│   └── health_impact.csv
│
└── pages/
    ├── 1_Pollutant_Readings.py
    ├── 2_Weather_Conditions.py
    ├── 3_Pollution_Sources.py
    └── 4_Health_Impact.py

```

### What is CSVManager?

`CSVManager` is the **shared base class** for all four of our dataset managers.

All our datasets are different, but they need the same basic CSV operations:

* Load CSV data
* Read records
* Create records
* Update records
* Delete records
* Validate `record_id`
* Save changes safely to the CSV
* Check that required columns exist

Instead of writing these common operations separately in all four managers, we write them **once in `CSVManager`** and inherit them in:

```text
CSVManager
├── PollutantRecordManager
├── WeatherManager
├── PollutionSourceManager
└── HealthImpactManager
```

Each child manager then focuses only on its **dataset-specific logic**.

For example, `WeatherManager` handles things like:

* Validating rainfall and temperature
* Weather-specific filtering
* Weather statistics
* Weather report generation

So the basic idea is:

**CSVManager = How to manage a CSV**

**Child Manager = How to manage that particular type of data**

This avoids duplicate code, keeps the project consistent, and makes the code easier to maintain.
