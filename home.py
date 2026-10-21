import streamlit as st

from ui import apply_theme

st.set_page_config(
    page_title="Air Quality Analytics Dashboard",
    page_icon="A",
    layout="wide",
)

apply_theme()

st.title("Air Quality Analytics Dashboard")
st.caption("Course 22AIE205 - Introduction to Python (Semester 3)  |  Term Project")

st.markdown(
    "A multi-page analytics application exploring air quality, weather, emission "
    "sources, and respiratory health outcomes across Indian datasets."
)

st.divider()

st.header("Modules")

col1, col2 = st.columns(2)

with col1:
    with st.container(border=True):
        st.subheader("Weather Conditions")
        st.markdown(
            "**Owner:** Ajul T M  \n"
            "**Dataset:** Daily weather records for 10 major Indian cities (2022-2024).  \n"
            "**Focus:** Temperature, precipitation, wind speed and direction.  \n"
            "**Features:** CRUD operations, 6 Plotly visualisations, summary statistics, exportable reports."
        )
        st.page_link("pages/page2.py", label="Open dashboard")

with col2:
    with st.container(border=True):
        st.subheader("Pollution Sources")
        st.markdown(
            "**Owner:** Krishna  \n"
            "**Dataset:** Climate TRACE PM2.5 emissions by source and sector in India (2024-2026).  \n"
            "**Focus:** Sectoral emissions and facility-level tracking.  \n"
            "**Features:** CRUD operations, interactive charts, downloadable reports."
        )
        st.page_link("pages/page3.py", label="Open dashboard")

col3, col4 = st.columns(2)

with col3:
    with st.container(border=True):
        st.subheader("Pollutant Readings")
        st.markdown(
            "**Owner:** Aadith Anil  \n"
            "**Status:** In progress  \n"
            "**Dataset:** Global Air Pollution dataset (AQI, CO, Ozone, NO2, PM2.5).  \n"
            "**Focus:** City-level pollutant concentration tracking and AQI classification."
        )

with col4:
    with st.container(border=True):
        st.subheader("Health Impact")
        st.markdown(
            "**Owner:** Mokshith  \n"
            "**Dataset:** Air quality, weather and respiratory health hospital visits (2020-2021).  \n"
            "**Focus:** Correlations between AQI exposure and respiratory admissions.  \n"
            "**Features:** CRUD operations, interactive charts, downloadable reports."
        )
        st.page_link("pages/page4.py", label="Open dashboard")

st.divider()

st.header("Architecture")
st.markdown(
    "- **Shared base class (`CSVManager`):** centralises CSV reads, writes, schema checks and atomic file replacement.  \n"
    "- **Domain managers:** `WeatherManager`, `PollutionSourceManager`, `HealthImpactManager` inherit from `CSVManager`.  \n"
    "- **Crash-resistant design:** CSV interactions wrapped in `try / except / else / finally` with friendly error banners.  \n"
    "- **Reactive visualisations:** charts and KPIs update from active sidebar filters and data edits."
)