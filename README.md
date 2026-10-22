# Air Quality Analytics Dashboard

**Course:** 22AIE205 – Introduction to Python (Semester 3)  
**Project:** Term Project, Data Analytics Web Application Development  

---

## 👥 Team Members & Dataset Ownership

| Page | Dataset Topic | Owner | CSV File | Page File | Status |
| :---: | :--- | :--- | :--- | :--- | :---: |
| **1** | Pollutant Readings | Aadith Anil | `data/page1.csv` | `pages/page1.py` | **Complete** |
| **2** | Weather Conditions | Ajul T M | `data/page2.csv` | `pages/page2.py` | **Complete** |
| **3** | Pollution Sources | Krishna | `data/page3.csv` | `pages/page3.py` | **Complete** |
| **4** | Health Impact | Mokshith | `data/page4.csv` | `pages/page4.py` | **Complete** |

---

## 🚀 Setup & Execution Instructions

### 1. Prerequisites
- Python 3.10+ (tested on Python 3.12)
- Virtual environment tool (e.g. `venv`, `uv`, or `conda`)

### 2. Environment Setup
Create and activate a virtual environment:
```bash
python3 -m venv .venv
source .venv/bin/activate
```

Install all dependencies strictly from `requirements.txt`:
```bash
pip install -r requirements.txt
```

### 3. Run the Dashboard
Launch the multi-page Streamlit application:
```bash
streamlit run home.py
```
Open your web browser at `http://localhost:8501`.

---

## 📂 Project Structure

```text
Air_Quality_Dashboard/
├── home.py                        # Landing page linking to all modules
├── requirements.txt               # Dependencies (Streamlit, Pandas, NumPy, Plotly)
├── README.md                      # Documentation & team ownership
├── data/
│   ├── page1.csv                  # Member 1 (Aadith) pollutant readings dataset
│   ├── page2.csv                  # Member 2 (Ajul) weather dataset
│   ├── page3.csv                  # Member 3 (Krishna) pollution sources dataset
│   └── page4.csv                  # Member 4 (Mokshith) health impact dataset
├── manager/
│   ├── __init__.py
│   ├── csv_manager.py             # Shared base class for CSV CRUD & atomic writes
│   ├── page1_manager.py           # Member 1: PollutantRecordManager
│   ├── page2_manager.py           # Member 2: WeatherManager (CRUD, stats, validation)
│   ├── page3_manager.py           # Member 3: PollutionSourceManager
│   └── page4_manager.py           # Member 4: HealthImpactManager
├── pages/
│   ├── page1.py                   # Member 1 (Aadith) pollutant readings dashboard
│   ├── page2.py                   # Member 2 (Ajul) weather conditions dashboard
│   ├── page3.py                   # Member 3 (Krishna) pollution sources dashboard
│   └── page4.py                   # Member 4 (Mokshith) health impact dashboard
└── scripts/
    ├── page1.py                   # Member 1 dataset preprocessing script
    ├── page2.py                   # Member 2 dataset preprocessing script
    ├── page3.py                   # Member 3 dataset preprocessing script
    └── page4.py                   # Member 4 dataset preprocessing script
```

---

## 🏗️ Architecture & OOP Design

### What is CSVManager?
`CSVManager` is the **shared base class** for all four dataset managers.
All datasets are distinct, but share common CSV management needs:
* Load CSV data with schema checking
* Protected data attribute (`_data`) exposed via `@property`
* Safe atomic writes using temporary files (`tempfile`) and `os.replace`
* Base CRUD operations: `create`, `read`, `update`, `delete`
* Validation of `record_id` and required column integrity
* Error handling wrapped in `try / except / else / finally`

```text
CSVManager (Base Class)
├── PollutantRecordManager (Page 1)
├── WeatherManager         (Page 2 - Member 2)
├── PollutionSourceManager (Page 3 - Member 3)
└── HealthImpactManager    (Page 4)
```

Each child manager encapsulates its dataset-specific rules, such as:
* Numerical validation (e.g., temperature range, non-negative rainfall & wind speeds)
* Specialized multi-criteria filtering and sorting
* Domain statistics calculation (mean temperatures, cumulative precipitation, extreme winds)
* Domain-specific summary report export
