from datetime import date, datetime
import plotly.express as px
import streamlit as st

from manager.page2_manager import (
    INDIAN_CITIES,
    WEATHER_FIELDS,
    WMO_CODE_MAP,
    WeatherManager,
)
from ui import apply_theme, chart_layout

st.set_page_config(page_title="Weather Conditions", layout="wide")

apply_theme()


def safe(action, *args):
    """
    Safely executes an action, catching known exceptions and returning (ok, result).
    Implements try/except/else/finally to prevent raw tracebacks.
    """
    res = None
    ok = False
    try:
        res = action(*args)
    except (FileNotFoundError, ValueError, TypeError, OSError) as err:
        st.error(f"Error: {err}")
        ok = False
    except Exception as err:
        st.error(f"An unexpected error occurred: {err}")
        ok = False
    else:
        ok = True
    finally:
        pass
    return ok, res


# Fresh load of weather dataset at page start
m = WeatherManager("data/page2.csv")
ok, all_df = safe(m.load_data)
if not ok:
    st.stop()

st.title("Weather Conditions & Environmental Analytics")
st.write(
    "Explore historical weather patterns, temperature dynamics, rainfall and wind conditions across major Indian cities."
)

if "msg" in st.session_state:
    st.success(st.session_state.pop("msg"))

# --- Sidebar Filters ---
st.sidebar.header("Filters")

# City selection
selected_cities = st.sidebar.multiselect(
    "Select Cities",
    options=INDIAN_CITIES,
    default=INDIAN_CITIES,
)

# Date range selection
min_date_val = datetime.strptime(str(all_df["date"].min()), "%Y-%m-%d").date()
max_date_val = datetime.strptime(str(all_df["date"].max()), "%Y-%m-%d").date()

date_range = st.sidebar.date_input(
    "Date Range",
    value=(min_date_val, max_date_val),
    min_value=min_date_val,
    max_value=max_date_val,
)

start_date = date_range[0] if isinstance(date_range, (list, tuple)) and len(date_range) > 0 else min_date_val
end_date = (
    date_range[1]
    if isinstance(date_range, (list, tuple)) and len(date_range) > 1
    else (date_range[0] if isinstance(date_range, (list, tuple)) and len(date_range) > 0 else max_date_val)
)

# Temperature range filter
min_temp_val = float(all_df["temp_max"].min())
max_temp_val = float(all_df["temp_max"].max())
temp_range = st.sidebar.slider(
    "Max Temperature Range (°C)",
    min_value=min_temp_val,
    max_value=max_temp_val,
    value=(min_temp_val, max_temp_val),
    step=0.5,
)

# Text search
search_query = st.sidebar.text_input("Search (City or Date YYYY-MM-DD)", key="weather_search")

# Apply filters
filtered_df = m.filter_data(
    cities=selected_cities,
    start_date=start_date,
    end_date=end_date,
    temp_range=temp_range,
    search_text=search_query,
)

stats = m.summary_stats(filtered_df)

filter_desc = (
    f"Cities: {', '.join(selected_cities) if selected_cities else 'None'}; "
    f"Dates: {start_date} to {end_date}; "
    f"Temp Max: {temp_range[0]}°C - {temp_range[1]}°C; "
    f"Search: '{search_query}'"
)

st.write(f"Showing **{len(filtered_df)}** of **{len(all_df)}** records based on active filters.")

# --- Navigation Tabs ---
tab_view, tab_charts, tab_add, tab_edit, tab_delete, tab_report = st.tabs(
    ["View", "Charts", "Add", "Edit", "Delete", "Report"]
)

# ----------------- TAB 1: VIEW -----------------
with tab_view:
    st.subheader("Key Weather Metrics")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Records", stats["count"])
    c2.metric(
        "Mean Max Temp",
        f"{stats['mean_temp_max']} °C" if stats["mean_temp_max"] is not None else "—",
    )
    c3.metric(
        "Mean Min Temp",
        f"{stats['mean_temp_min']} °C" if stats["mean_temp_min"] is not None else "—",
    )
    c4.metric(
        "Mean Feels Like",
        f"{stats['mean_feels_like']} °C" if stats["mean_feels_like"] is not None else "—",
    )

    c5, c6, c7, c8 = st.columns(4)
    c5.metric("Total Rainfall", f"{stats['total_rainfall']} mm")
    c6.metric("Total Precipitation", f"{stats['total_precipitation']} mm")
    c7.metric(
        "Max Wind Speed",
        f"{stats['max_wind_speed']} km/h" if stats["max_wind_speed"] is not None else "—",
    )
    c8.metric("Hottest City (Avg)", stats["top_temp_city"])

    st.caption(
        "ℹ️ **Missing Values Handling**: Rows with missing numerical weather values are excluded from summary statistics and charts."
    )

    if filtered_df.empty:
        st.info("No records match the active filters.")
    else:
        st.divider()
        col_left, col_right = st.columns(2)
        with col_left:
            st.write("**City Temperature Averages (°C)**")
            st.dataframe(m.city_temperature_averages(filtered_df), hide_index=True)
        with col_right:
            st.write("**City Wind Speed Averages (km/h)**")
            st.dataframe(m.city_wind_averages(filtered_df), hide_index=True)

        st.divider()
        st.write("**Weather Records Table**")
        sort_col1, sort_col2 = st.columns([3, 1])
        with sort_col1:
            sort_by = st.selectbox("Sort table by column", list(filtered_df.columns), index=2)
        with sort_col2:
            sort_direction = st.radio("Order", ["Ascending", "Descending"], horizontal=True)

        sorted_df = m.sort_data(filtered_df, sort_by, ascending=(sort_direction == "Ascending"))
        st.dataframe(sorted_df, hide_index=True)

# ----------------- TAB 2: CHARTS -----------------
with tab_charts:
    if filtered_df.empty:
        st.info("No records match the active filters.")
    else:
        st.subheader("Dynamic Meteorological Visualizations")

        # Row 1: Temperature Over Time & Average Temperature by City
        row1_left, row1_right = st.columns(2)
        with row1_left:
            fig_temp_line = px.line(
                filtered_df,
                x="date",
                y="temp_max",
                color="city",
                title="1. Maximum Temperature Over Time (°C)",
                labels={"temp_max": "Max Temp (°C)", "date": "Date"},
            )
            fig_temp_line.update_layout(hovermode="x unified")
            st.plotly_chart(chart_layout(fig_temp_line), use_container_width=True)

        with row1_right:
            city_temps = m.city_temperature_averages(filtered_df)
            fig_temp_bar = px.bar(
                city_temps,
                x="city",
                y="avg_max_temp",
                color="avg_max_temp",
                color_continuous_scale="Viridis",
                title="2. Average Maximum Temperature by City (°C)",
                labels={"avg_max_temp": "Avg Max Temp (°C)", "city": "City"},
            )
            st.plotly_chart(chart_layout(fig_temp_bar), use_container_width=True)

        # Row 2: Rainfall Over Time & Average Wind Speed by City
        row2_left, row2_right = st.columns(2)
        with row2_left:
            fig_rain_line = px.line(
                filtered_df,
                x="date",
                y="rainfall",
                color="city",
                title="3. Daily Rainfall Over Time (mm)",
                labels={"rainfall": "Rainfall (mm)", "date": "Date"},
            )
            st.plotly_chart(chart_layout(fig_rain_line), use_container_width=True)

        with row2_right:
            city_winds = m.city_wind_averages(filtered_df)
            fig_wind_bar = px.bar(
                city_winds,
                x="city",
                y="avg_wind_speed",
                color="avg_wind_speed",
                color_continuous_scale="Blues",
                title="4. Average Wind Speed by City (km/h)",
                labels={"avg_wind_speed": "Avg Wind Speed (km/h)", "city": "City"},
            )
            st.plotly_chart(chart_layout(fig_wind_bar), use_container_width=True)

        # Row 3: Histogram of Max Temperature & Temperature vs Wind Speed Scatter
        row3_left, row3_right = st.columns(2)
        with row3_left:
            fig_hist = px.histogram(
                filtered_df,
                x="temp_max",
                nbins=30,
                color="city",
                title="5. Distribution of Maximum Temperature (°C)",
                labels={"temp_max": "Max Temp (°C)"},
            )
            st.plotly_chart(chart_layout(fig_hist), use_container_width=True)

        with row3_right:
            fig_scatter = px.scatter(
                filtered_df,
                x="temp_max",
                y="wind_speed",
                color="city",
                title="6. Maximum Temperature vs Wind Speed (km/h)",
                labels={"temp_max": "Max Temp (°C)", "wind_speed": "Wind Speed (km/h)"},
                hover_data=["date", "weather_code"],
            )
            st.plotly_chart(chart_layout(fig_scatter), use_container_width=True)

# ----------------- TAB 3: ADD (CREATE) -----------------
with tab_add:
    st.subheader("Add New Weather Observation")
    st.write("Enter the weather parameters below. All entries are validated before saving.")

    with st.form("add_weather_form"):
        fc1, fc2 = st.columns(2)
        with fc1:
            city_in = st.selectbox("City", INDIAN_CITIES)
            date_in = st.date_input("Observation Date", value=date.today())
            temp_max_in = st.number_input("Maximum Temperature (°C)", value=30.0, step=0.1)
            temp_min_in = st.number_input("Minimum Temperature (°C)", value=20.0, step=0.1)
            feels_like_in = st.number_input("Apparent Temperature / Feels Like (°C)", value=32.0, step=0.1)
            rainfall_in = st.number_input("Rainfall (mm)", min_value=0.0, value=0.0, step=0.1)

        with fc2:
            precip_in = st.number_input("Precipitation (mm)", min_value=0.0, value=0.0, step=0.1)
            wmo_options = list(WMO_CODE_MAP.keys())
            wmo_code_in = st.selectbox(
                "Weather Code (WMO)",
                options=wmo_options,
                format_func=lambda c: f"{c}: {WMO_CODE_MAP.get(c, 'Unknown')}",
            )
            wind_speed_in = st.number_input("Wind Speed (km/h)", min_value=0.0, value=12.0, step=0.1)
            wind_gusts_in = st.number_input("Wind Gusts (km/h)", min_value=0.0, value=20.0, step=0.1)
            wind_dir_in = st.number_input("Wind Direction (0° - 360°)", min_value=0, max_value=360, value=180, step=1)

        submit_add = st.form_submit_button("Add Weather Record")

    if submit_add:
        new_record = {
            "record_id": m.next_id(),
            "city": city_in,
            "date": date_in.strftime("%Y-%m-%d"),
            "temp_max": temp_max_in,
            "temp_min": temp_min_in,
            "feels_like": feels_like_in,
            "rainfall": rainfall_in,
            "precipitation": precip_in,
            "weather_code": int(wmo_code_in),
            "wind_speed": wind_speed_in,
            "wind_gusts": wind_gusts_in,
            "wind_direction": int(wind_dir_in),
        }
        ok, created = safe(m.create, new_record)
        if ok:
            st.session_state["msg"] = (
                f"Successfully added record ID #{created['record_id']} for {city_in} on {date_in}!"
            )
            st.rerun()

# ----------------- TAB 4: EDIT (UPDATE) -----------------
with tab_edit:
    st.subheader("Edit Existing Weather Observation")
    edit_id = st.number_input("Enter Record ID to Edit", min_value=1, step=1, key="edit_record_id")

    match_rows = all_df[all_df["record_id"] == edit_id]
    if match_rows.empty:
        st.warning(f"No weather record found with ID #{edit_id}.")
    else:
        rec = match_rows.iloc[0]
        k = str(edit_id)

        try:
            curr_date = datetime.strptime(str(rec["date"]).strip(), "%Y-%m-%d").date()
        except ValueError:
            curr_date = date.today()

        with st.form("edit_weather_form"):
            ec1, ec2 = st.columns(2)
            with ec1:
                e_city = st.selectbox(
                    "City",
                    INDIAN_CITIES,
                    index=INDIAN_CITIES.index(rec["city"]) if rec["city"] in INDIAN_CITIES else 0,
                    key="ec_" + k,
                )
                e_date = st.date_input("Date", value=curr_date, key="ed_" + k)
                e_tmax = st.number_input("Max Temp (°C)", value=float(rec["temp_max"]), step=0.1, key="etmax_" + k)
                e_tmin = st.number_input("Min Temp (°C)", value=float(rec["temp_min"]), step=0.1, key="etmin_" + k)
                e_feels = st.number_input("Feels Like (°C)", value=float(rec["feels_like"]), step=0.1, key="efl_" + k)
                e_rain = st.number_input("Rainfall (mm)", min_value=0.0, value=float(rec["rainfall"]), step=0.1, key="er_" + k)

            with ec2:
                e_precip = st.number_input("Precipitation (mm)", min_value=0.0, value=float(rec["precipitation"]), step=0.1, key="ep_" + k)
                curr_wmo = int(rec["weather_code"]) if int(rec["weather_code"]) in WMO_CODE_MAP else 0
                wmo_keys = list(WMO_CODE_MAP.keys())
                e_wmo = st.selectbox(
                    "Weather Code (WMO)",
                    options=wmo_keys,
                    index=wmo_keys.index(curr_wmo) if curr_wmo in wmo_keys else 0,
                    format_func=lambda c: f"{c}: {WMO_CODE_MAP.get(c, 'Unknown')}",
                    key="ewmo_" + k,
                )
                e_ws = st.number_input("Wind Speed (km/h)", min_value=0.0, value=float(rec["wind_speed"]), step=0.1, key="ews_" + k)
                e_wg = st.number_input("Wind Gusts (km/h)", min_value=0.0, value=float(rec["wind_gusts"]), step=0.1, key="ewg_" + k)
                e_wd = st.number_input("Wind Direction (0° - 360°)", min_value=0, max_value=360, value=int(rec["wind_direction"]), step=1, key="ewd_" + k)

            submit_edit = st.form_submit_button("Save Changes")

        if submit_edit:
            updates = {
                "city": e_city,
                "date": e_date.strftime("%Y-%m-%d"),
                "temp_max": e_tmax,
                "temp_min": e_tmin,
                "feels_like": e_feels,
                "rainfall": e_rain,
                "precipitation": e_precip,
                "weather_code": int(e_wmo),
                "wind_speed": e_ws,
                "wind_gusts": e_wg,
                "wind_direction": int(e_wd),
            }
            ok, updated_row = safe(m.update, int(edit_id), updates)
            if ok:
                st.session_state["msg"] = f"Successfully updated record ID #{edit_id}."
                st.rerun()

# ----------------- TAB 5: DELETE -----------------
with tab_delete:
    st.subheader("Delete Weather Observation")
    del_id = st.number_input("Enter Record ID to Delete", min_value=1, step=1, key="delete_record_id")

    match_del = all_df[all_df["record_id"] == del_id]
    if match_del.empty:
        st.warning(f"No weather record found with ID #{del_id}.")
    else:
        st.write("Record selected for deletion:")
        st.dataframe(match_del, hide_index=True)

        confirm_del = st.checkbox("Yes, permanently delete this record", key="confirm_delete_box")
        del_button = st.button("Delete Record", type="primary", disabled=not confirm_del)

        if del_button:
            ok, removed = safe(m.delete, int(del_id))
            if ok:
                st.session_state["msg"] = f"Record ID #{del_id} successfully deleted."
                st.rerun()

# ----------------- TAB 6: REPORT -----------------
with tab_report:
    st.subheader("Export Weather Analytics Report")
    st.write("Generate and download a comprehensive text summary of the filtered weather data.")

    report_text = m.export_report(filtered_df, filter_desc)
    st.text_area("Report Preview", report_text, height=350)

    st.download_button(
        label="Download Weather Report (.txt)",
        data=report_text,
        file_name=f"weather_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
        mime="text/plain",
    )
