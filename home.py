import streamlit as st

st.set_page_config(
    page_title="Air Quality Analytics Dashboard",
    page_icon="🌍",
    layout="wide",
)

st.title("🌍 Air Quality Analytics Dashboard")
st.subheader("Course: 22AIE205 – Introduction to Python (Semester 3)")
st.caption("Term Project: Data Analytics Web Application Development")

st.markdown(
    """
    Welcome to the **Air Quality Analytics Dashboard**, an integrated multi-page Python web application built using **Streamlit**, **Pandas**, **NumPy**, and **Plotly**. 

    This platform analyzes environmental data across multiple angles to understand air quality dynamics, atmospheric influences, emission sources, and human health outcomes.
    """
)

st.divider()

st.header("📑 Modules & Dashboards")

col1, col2 = st.columns(2)

with col1:
    with st.container(border=True):
        st.subheader("🌤️ Page 2: Weather Conditions")
        st.markdown(
            """
            * **Owner:** Ajul T M
            * **Dataset:** Daily weather records for 10 major Indian cities (2022–2024).
            * **Focus:** Historical temperatures, precipitation, rainfall, wind speeds, wind gusts, and dominant wind directions.
            * **Features:** Full CRUD operations, 6 dynamic Plotly visualizations, summary statistics, and exportable reports.
            """
        )
        st.page_link("pages/page2.py", label="Open Weather Conditions Dashboard", icon="🌤️")

with col2:
    with st.container(border=True):
        st.subheader("🏭 Page 3: Pollution Sources")
        st.markdown(
            """
            * **Owner:** Krishna
            * **Dataset:** Climate TRACE PM2.5 emissions by source and sector in India (2024–2026).
            * **Focus:** Sectoral emissions (buildings, power, manufacturing, transport, mineral-extraction) and facility-level tracking.
            * **Features:** Full CRUD operations, interactive charts, and downloadable reports.
            """
        )
        st.page_link("pages/page3.py", label="Open Pollution Sources Dashboard", icon="🏭")

col3, col4 = st.columns(2)

with col3:
    with st.container(border=True):
        st.subheader("📊 Page 1: Pollutant Readings")
        st.markdown(
            """
            * **Owner:** Aadith Anil *(In Progress)*
            * **Dataset:** Global Air Pollution dataset measuring AQI, CO, Ozone, NO2, and PM2.5.
            * **Focus:** City-level pollutant concentration tracking and AQI classifications.
            """
        )

with col4:
    with st.container(border=True):
        st.subheader("🏥 Page 4: Health Impact")
        st.markdown(
            """
            * **Owner:** Mokshith
            * **Dataset:** Air quality, weather, and respiratory health hospital visit data (2020–2021).
            * **Focus:** Evaluating correlations between AQI exposure and respiratory admissions.
            * **Features:** Full CRUD operations, interactive charts, and downloadable reports.
            """
        )
        st.page_link("pages/page4.py", label="Open Health Impact Dashboard", icon="🏥")

st.divider()

st.header("⚙️ Architectural Highlights")
st.markdown(
    """
    - **Shared OOP Base Class (`CSVManager`):** Centralizes all CSV reads, writes, schema checks, and atomic file replacements.
    - **Domain Managers:** `WeatherManager`, `PollutionSourceManager`, etc. inherit from `CSVManager` to encapsulate domain-specific business validation and statistics.
    - **Crash-Resistant Design:** Every CSV interaction is wrapped in structured `try / except / else / finally` blocks with user-friendly error banners.
    - **Dynamic Visualizations:** All charts and KPIs update in real-time based on active sidebar filters and database modifications.
    """
)
