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

col3, col1 = st.columns(2)
col2, col4 = st.columns(2)

with col3:
    with st.container(border=True):
        st.subheader("📊 Page 1: Pollutant Readings")
        st.markdown(
            """
            * **Owner:** Aadith Anil
            * **Dataset:** ~2,000-row stratified sample of the Global Air Pollution dataset measuring AQI, CO, Ozone, NO2, and PM2.5.
            * **Focus:** Country/city-level pollutant concentration tracking and AQI classifications.
            * **Features:** Full CRUD operations, 2 Plotly visualizations, summary statistics, and exportable reports.
            """
        )
        st.page_link("pages/page1.py", label="Open Pollutant Readings Dashboard", icon="📊")

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