from datetime import datetime

import pandas as pd
import plotly.express as px
import streamlit as st

from manager.page1_manager import AQI_CATEGORIES, PollutantRecordManager

st.set_page_config(page_title="Pollutant Readings", layout="wide")

UNKNOWN_SENTINEL = "(Unknown)"


def safe(action, *args):
    """
    Safely executes an action, catching known exceptions and returning (ok, result).
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


# Fresh load of pollutant dataset at page start
m = PollutantRecordManager("data/page1.csv")
ok, all_df = safe(m.load_data)
if not ok:
    st.stop()

st.title("Pollutant Readings")
st.write(
    "Explore global AQI, CO, Ozone, NO2, and PM2.5 pollutant readings across countries and cities."
)

if "msg" in st.session_state:
    st.success(st.session_state.pop("msg"))

# --- Sidebar Filters ---
st.sidebar.header("Filters")

country_options = sorted(all_df["Country"].dropna().unique().tolist())
selected_countries = st.sidebar.multiselect(
    "Country",
    options=country_options + [UNKNOWN_SENTINEL],
    default=country_options + [UNKNOWN_SENTINEL],
)

selected_categories = st.sidebar.multiselect(
    "AQI Category",
    options=AQI_CATEGORIES,
    default=AQI_CATEGORIES,
)

min_aqi_val = int(all_df["AQI Value"].min())
max_aqi_val = int(all_df["AQI Value"].max())
aqi_range = st.sidebar.slider(
    "AQI Value Range",
    min_value=min_aqi_val,
    max_value=max_aqi_val,
    value=(min_aqi_val, max_aqi_val),
)

search_query = st.sidebar.text_input("Search (Country or City)", key="pollutant_search")

include_unknown = UNKNOWN_SENTINEL in selected_countries
known_selected = [c for c in selected_countries if c != UNKNOWN_SENTINEL]

# Apply category/AQI-range/search filters without touching Country, then select the
# Country subset manually so the "(Unknown)" sentinel can include null-Country rows.
no_country_filtered = m.filter_data(
    countries=None,
    categories=selected_categories if selected_categories else None,
    aqi_range=aqi_range,
    search_text=search_query,
)

country_mask = pd.Series(False, index=no_country_filtered.index)
if known_selected:
    country_mask |= no_country_filtered["Country"].isin(known_selected)
if include_unknown:
    country_mask |= no_country_filtered["Country"].isna()

filtered_df = no_country_filtered[country_mask].reset_index(drop=True)

stats = m.summary_stats(filtered_df)

filter_desc = (
    f"Countries: {', '.join(selected_countries) if selected_countries else 'None'}; "
    f"Categories: {', '.join(selected_categories) if selected_categories else 'None'}; "
    f"AQI Value: {aqi_range[0]} - {aqi_range[1]}; "
    f"Search: '{search_query}'"
)

st.write(f"Showing **{len(filtered_df)}** of **{len(all_df)}** records based on active filters.")

# --- Navigation Tabs ---
tab_view, tab_charts, tab_add, tab_edit, tab_delete, tab_report = st.tabs(
    ["View", "Charts", "Add", "Edit", "Delete", "Report"]
)

# ----------------- TAB 1: VIEW -----------------
with tab_view:
    st.subheader("Key Pollutant Metrics")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Records", stats["count"])
    c2.metric("Mean AQI Value", stats["mean_aqi"] if stats["mean_aqi"] is not None else "—")
    c3.metric("Mean PM2.5 AQI Value", stats["mean_pm25"] if stats["mean_pm25"] is not None else "—")
    c4.metric("Top Country (Mean AQI)", stats["top_country"])

    st.caption(
        "ℹ️ **Missing Values Handling**: Rows with a missing Country are labeled "
        f"'{UNKNOWN_SENTINEL}' in the table and excluded only from the country-average "
        "bar chart and the top-country stat; they are still counted in all other totals "
        "and in the category chart."
    )

    if filtered_df.empty:
        st.info("No records match the active filters.")
    else:
        st.divider()
        st.write("**Pollutant Records Table**")
        sort_col1, sort_col2 = st.columns([3, 1])
        with sort_col1:
            sort_by = st.selectbox("Sort table by column", list(filtered_df.columns), index=0)
        with sort_col2:
            sort_direction = st.radio("Order", ["Ascending", "Descending"], horizontal=True)

        sorted_df = m.sort_data(filtered_df, sort_by, ascending=(sort_direction == "Ascending"))
        display_df = sorted_df.copy()
        display_df["Country"] = display_df["Country"].fillna(UNKNOWN_SENTINEL)
        st.dataframe(display_df, hide_index=True)

# ----------------- TAB 2: CHARTS -----------------
with tab_charts:
    if filtered_df.empty:
        st.info("No records match the active filters.")
    else:
        st.subheader("Pollutant Visualizations")

        chart_col1, chart_col2 = st.columns(2)
        with chart_col1:
            metric = st.selectbox("Metric for Country Averages", ["AQI Value", "PM2.5 AQI Value"])
        with chart_col2:
            top_n = st.number_input("Top N Countries", min_value=1, max_value=50, value=10, step=1)

        row1_left, row1_right = st.columns(2)
        with row1_left:
            country_avgs = m.country_averages(filtered_df, metric, int(top_n))
            fig_bar = px.bar(
                country_avgs,
                x="Country",
                y=metric,
                color=metric,
                color_continuous_scale="Viridis",
                title=f"Average {metric} by Top {int(top_n)} Countries",
            )
            st.plotly_chart(fig_bar, use_container_width=True)

        with row1_right:
            category_dist = m.category_distribution(filtered_df)
            fig_pie = px.pie(
                category_dist,
                names="category",
                values="count",
                title="AQI Category Distribution",
            )
            st.plotly_chart(fig_pie, use_container_width=True)

# ----------------- TAB 3: ADD (CREATE) -----------------
with tab_add:
    st.subheader("Add New Pollutant Reading")
    st.write("Enter the pollutant parameters below. All entries are validated before saving.")

    with st.form("add_pollutant_form"):
        fc1, fc2 = st.columns(2)
        with fc1:
            city_in = st.text_input("City")
            country_in = st.text_input("Country (optional)")
            aqi_in = st.number_input("AQI Value", min_value=0, value=0, step=1)
            aqi_cat_in = st.selectbox("AQI Category", AQI_CATEGORIES)
            co_in = st.number_input("CO AQI Value", min_value=0, value=0, step=1)
            co_cat_in = st.selectbox("CO AQI Category", AQI_CATEGORIES)

        with fc2:
            ozone_in = st.number_input("Ozone AQI Value", min_value=0, value=0, step=1)
            ozone_cat_in = st.selectbox("Ozone AQI Category", AQI_CATEGORIES)
            no2_in = st.number_input("NO2 AQI Value", min_value=0, value=0, step=1)
            no2_cat_in = st.selectbox("NO2 AQI Category", AQI_CATEGORIES)
            pm25_in = st.number_input("PM2.5 AQI Value", min_value=0, value=0, step=1)
            pm25_cat_in = st.selectbox("PM2.5 AQI Category", AQI_CATEGORIES)

        submit_add = st.form_submit_button("Add Record")

    if submit_add:
        new_record = {
            "City": city_in,
            "Country": country_in,
            "AQI Value": aqi_in,
            "AQI Category": aqi_cat_in,
            "CO AQI Value": co_in,
            "CO AQI Category": co_cat_in,
            "Ozone AQI Value": ozone_in,
            "Ozone AQI Category": ozone_cat_in,
            "NO2 AQI Value": no2_in,
            "NO2 AQI Category": no2_cat_in,
            "PM2.5 AQI Value": pm25_in,
            "PM2.5 AQI Category": pm25_cat_in,
        }
        ok, created = safe(m.create, new_record)
        if ok:
            st.session_state["msg"] = f"Successfully added record ID #{created['record_id']} for {city_in}!"
            st.rerun()

# ----------------- TAB 4: EDIT (UPDATE) -----------------
with tab_edit:
    st.subheader("Edit Existing Pollutant Reading")
    edit_id = st.number_input("Enter Record ID to Edit", min_value=1, step=1, key="edit_record_id")

    match_rows = all_df[all_df["record_id"] == edit_id]
    if match_rows.empty:
        st.warning(f"No pollutant record found with ID #{edit_id}.")
    else:
        rec = match_rows.iloc[0]
        k = str(edit_id)
        rec_country = "" if pd.isna(rec["Country"]) else str(rec["Country"])

        with st.form("edit_pollutant_form"):
            ec1, ec2 = st.columns(2)
            with ec1:
                e_city = st.text_input("City", value=str(rec["City"]), key="ecity_" + k)
                e_country = st.text_input("Country (optional)", value=rec_country, key="ecountry_" + k)
                e_aqi = st.number_input("AQI Value", min_value=0, value=int(rec["AQI Value"]), step=1, key="eaqi_" + k)
                e_aqi_cat = st.selectbox(
                    "AQI Category", AQI_CATEGORIES,
                    index=AQI_CATEGORIES.index(rec["AQI Category"]) if rec["AQI Category"] in AQI_CATEGORIES else 0,
                    key="eaqicat_" + k,
                )
                e_co = st.number_input("CO AQI Value", min_value=0, value=int(rec["CO AQI Value"]), step=1, key="eco_" + k)
                e_co_cat = st.selectbox(
                    "CO AQI Category", AQI_CATEGORIES,
                    index=AQI_CATEGORIES.index(rec["CO AQI Category"]) if rec["CO AQI Category"] in AQI_CATEGORIES else 0,
                    key="ecocat_" + k,
                )

            with ec2:
                e_ozone = st.number_input("Ozone AQI Value", min_value=0, value=int(rec["Ozone AQI Value"]), step=1, key="eozone_" + k)
                e_ozone_cat = st.selectbox(
                    "Ozone AQI Category", AQI_CATEGORIES,
                    index=AQI_CATEGORIES.index(rec["Ozone AQI Category"]) if rec["Ozone AQI Category"] in AQI_CATEGORIES else 0,
                    key="eozonecat_" + k,
                )
                e_no2 = st.number_input("NO2 AQI Value", min_value=0, value=int(rec["NO2 AQI Value"]), step=1, key="eno2_" + k)
                e_no2_cat = st.selectbox(
                    "NO2 AQI Category", AQI_CATEGORIES,
                    index=AQI_CATEGORIES.index(rec["NO2 AQI Category"]) if rec["NO2 AQI Category"] in AQI_CATEGORIES else 0,
                    key="eno2cat_" + k,
                )
                e_pm25 = st.number_input("PM2.5 AQI Value", min_value=0, value=int(rec["PM2.5 AQI Value"]), step=1, key="epm25_" + k)
                e_pm25_cat = st.selectbox(
                    "PM2.5 AQI Category", AQI_CATEGORIES,
                    index=AQI_CATEGORIES.index(rec["PM2.5 AQI Category"]) if rec["PM2.5 AQI Category"] in AQI_CATEGORIES else 0,
                    key="epm25cat_" + k,
                )

            submit_edit = st.form_submit_button("Save Changes")

        if submit_edit:
            updates = {
                "City": e_city,
                "Country": e_country,
                "AQI Value": e_aqi,
                "AQI Category": e_aqi_cat,
                "CO AQI Value": e_co,
                "CO AQI Category": e_co_cat,
                "Ozone AQI Value": e_ozone,
                "Ozone AQI Category": e_ozone_cat,
                "NO2 AQI Value": e_no2,
                "NO2 AQI Category": e_no2_cat,
                "PM2.5 AQI Value": e_pm25,
                "PM2.5 AQI Category": e_pm25_cat,
            }
            ok, updated_row = safe(m.update, int(edit_id), updates)
            if ok:
                st.session_state["msg"] = f"Successfully updated record ID #{edit_id}."
                st.rerun()

# ----------------- TAB 5: DELETE -----------------
with tab_delete:
    st.subheader("Delete Pollutant Reading")
    del_id = st.number_input("Enter Record ID to Delete", min_value=1, step=1, key="delete_record_id")

    match_del = all_df[all_df["record_id"] == del_id]
    if match_del.empty:
        st.warning(f"No pollutant record found with ID #{del_id}.")
    else:
        st.write("Record selected for deletion:")
        display_del = match_del.copy()
        display_del["Country"] = display_del["Country"].fillna(UNKNOWN_SENTINEL)
        st.dataframe(display_del, hide_index=True)

        confirm_del = st.checkbox("Yes, permanently delete this record", key="confirm_delete_box")
        del_button = st.button("Delete Record", type="primary", disabled=not confirm_del)

        if del_button:
            ok, removed = safe(m.delete, int(del_id))
            if ok:
                st.session_state["msg"] = f"Record ID #{del_id} successfully deleted."
                st.rerun()

# ----------------- TAB 6: REPORT -----------------
with tab_report:
    st.subheader("Export Pollutant Analytics Report")
    st.write("Generate and download a comprehensive text summary of the filtered pollutant data.")

    report_text = m.export_report(filtered_df, filter_desc)
    st.text_area("Report Preview", report_text, height=350)

    st.download_button(
        label="Download Pollutant Report (.txt)",
        data=report_text,
        file_name=f"pollutant_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
        mime="text/plain",
    )
