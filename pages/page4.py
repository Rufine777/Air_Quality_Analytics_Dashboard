from datetime import date

import pandas as pd
import plotly.express as px
import streamlit as st

from manager.page4_manager import AQI_CATEGORIES, FIELDS, HealthImpactManager
from ui import apply_theme, chart_layout

st.set_page_config(page_title="Health Impact", layout="wide")

apply_theme()


def safe(action, *args):
    try:
        return True, action(*args)
    except (FileNotFoundError, ValueError, TypeError, OSError) as e:
        st.error(str(e))
        return False, None


def show(value, digits=2):
    if value is None:
        return "N/A"
    if isinstance(value, str):
        return value
    if isinstance(value, int):
        return f"{value:,}"
    return f"{value:,.{digits}f}"


m = HealthImpactManager()
ok, all_df = safe(m.load_data)
if not ok:
    st.info("Fix or restore data/health_impact.csv (scripts/prepare_health_data.py can rebuild it), then reload.")
    st.stop()

st.title("Health Impact Dashboard")
st.caption("How are air quality conditions and respiratory health related across areas and over time?")

if "msg" in st.session_state:
    st.success(st.session_state.pop("msg"))

st.sidebar.header("Filters")
all_areas = sorted(all_df["area"].unique())
areas = st.sidebar.multiselect("Area", all_areas, default=all_areas)
cats = st.sidebar.multiselect("AQI category", AQI_CATEGORIES, default=AQI_CATEGORIES)

if all_df.empty:
    first_day = last_day = date.today()
else:
    first_day, last_day = date.fromisoformat(all_df["date"].min()), date.fromisoformat(all_df["date"].max())
picked = st.sidebar.date_input("Date range", value=(first_day, last_day), min_value=first_day, max_value=last_day)
if isinstance(picked, (tuple, list)) and len(picked) == 2:
    start, end = picked
else:
    start, end = first_day, last_day
    st.sidebar.info("Pick an end date to apply the date filter.")

search = st.sidebar.text_input("Search", placeholder="area, date, category, ID...")
sort_col = st.sidebar.selectbox("Sort by", FIELDS, index=FIELDS.index("date"))
order = st.sidebar.radio("Order", ["Ascending", "Descending"], horizontal=True)

ok, f = safe(m.read, areas, cats, start, end, search, sort_col, order == "Ascending")
if not ok:
    st.stop()
stats = m.summary_stats(f)

filters = {
    "Areas": "all" if len(areas) == len(all_areas) else (", ".join(areas) or "none selected"),
    "AQI categories": "all" if len(cats) == len(AQI_CATEGORIES) else (", ".join(cats) or "none selected"),
    "Date range": f"{start.isoformat()} to {end.isoformat()}",
    "Search": search.strip() or "(none)",
}

st.write(f"**Showing {len(f):,} of {len(all_df):,} records**")

r1 = st.columns(5)
r1[0].metric("Records", show(stats["records"]))
r1[1].metric("Total respiratory cases", show(stats["total_respiratory"]))
r1[2].metric("Total hospital visits", show(stats["total_hospital"]))
r1[3].metric("Avg respiratory cases", show(stats["avg_respiratory"]))
r1[4].metric("Avg hospital visits", show(stats["avg_hospital"]))
r2 = st.columns(4)
r2[0].metric("Min respiratory cases", show(stats["min_respiratory"]))
r2[1].metric("Max respiratory cases", show(stats["max_respiratory"]))
r2[2].metric("Area with most respiratory cases", show(stats["top_area"]))
r2[3].metric("Most common AQI category", show(stats["common_category"]))

if stats["missing_respiratory"] or stats["missing_hospital"]:
    st.warning(
        f"Some health values are missing in the selected rows (respiratory cases: {stats['missing_respiratory']}, "
        f"hospital visits: {stats['missing_hospital']}). They are not treated as 0; those rows are left out of "
        "the related statistics and charts."
    )

t_data, t_charts, t_add, t_edit, t_del, t_report = st.tabs(["Data", "Charts", "Add", "Edit", "Delete", "Report"])

with t_data:
    if f.empty:
        st.info("No records match the current filters.")
    else:
        st.dataframe(f, hide_index=True)

with t_charts:
    if f.empty:
        st.info("No records match the current filters, so there is nothing to chart.")
    else:
        left, right = st.columns(2)

        d = m.average_by_area(f, "respiratory_cases")
        if d.empty:
            left.info("No respiratory case values available for the area chart.")
        else:
            fig = px.bar(d, x="area", y="respiratory_cases", title="Average respiratory cases per area",
                         labels={"area": "Area", "respiratory_cases": "Average respiratory cases"})
            left.plotly_chart(chart_layout(fig), use_container_width=True)

        d = m.total_cases_by_date(f)
        if d.empty:
            right.info("No respiratory case values available for the time chart.")
        else:
            fig = px.line(d, x="date", y="respiratory_cases", title="Total respiratory cases over time",
                          labels={"date": "Date", "respiratory_cases": "Total respiratory cases"})
            right.plotly_chart(chart_layout(fig), use_container_width=True)

        left2, right2 = st.columns(2)

        d = m.average_by_area(f, "hospital_visits")
        if d.empty:
            left2.info("No hospital visit values available for this chart.")
        else:
            fig = px.bar(d, x="area", y="hospital_visits", title="Average hospital visits per area",
                         labels={"area": "Area", "hospital_visits": "Average hospital visits"})
            left2.plotly_chart(chart_layout(fig), use_container_width=True)

        d = m.average_cases_by_category(f)
        if d.empty:
            right2.info("No respiratory case values available for the AQI category chart.")
        else:
            fig = px.bar(d, x="aqi_category", y="respiratory_cases", title="Average respiratory cases by AQI category",
                         labels={"aqi_category": "AQI category", "respiratory_cases": "Average respiratory cases"})
            right2.plotly_chart(chart_layout(fig), use_container_width=True)

        st.caption("Bar charts use averages so areas and categories with different numbers of rows compare fairly; "
                   "the line chart adds up all cases on each date.")

with t_add:
    with st.form("add_form"):
        new_date = st.date_input("Date", value=last_day, key="add_date")
        area_pick = st.selectbox("Area", all_areas, key="add_area") if all_areas else None
        area_new = st.text_input("Or type a new area (leave blank to use the one selected above)", key="add_area_new")
        new_resp = st.number_input("Respiratory cases", min_value=0, step=1, value=0, key="add_resp")
        new_hosp = st.number_input("Hospital visits", min_value=0, step=1, value=0, key="add_hosp")
        new_cat = st.selectbox("AQI category", AQI_CATEGORIES, key="add_cat")
        submitted = st.form_submit_button("Add record")
    if submitted:
        rec = {
            "date": new_date,
            "area": area_new if area_new.strip() else area_pick,
            "respiratory_cases": new_resp,
            "hospital_visits": new_hosp,
            "aqi_category": new_cat,
        }
        ok, row = safe(m.create, rec)
        if ok:
            st.session_state["msg"] = f"Record {int(row['record_id'])} added."
            st.rerun()

with t_edit:
    if all_df.empty:
        st.info("There are no records to edit.")
    else:
        rid = st.number_input("Record ID to edit", min_value=1, step=1, value=int(all_df["record_id"].min()), key="edit_id")
        rows = all_df[all_df["record_id"] == rid]
        if rows.empty:
            st.warning("No record with that ID.")
        else:
            r = rows.iloc[0]
            k = str(int(rid))
            with st.form("edit_form"):
                st.text_input("Record ID (cannot be changed)", value=k, disabled=True, key="eid" + k)
                e_date = st.date_input("Date", value=date.fromisoformat(r["date"]), key="ed" + k)
                e_area = st.text_input("Area", value=str(r["area"]), key="ea" + k)
                e_resp = st.number_input("Respiratory cases", min_value=0, step=1, key="er" + k,
                                         value=None if pd.isna(r["respiratory_cases"]) else int(r["respiratory_cases"]))
                e_hosp = st.number_input("Hospital visits", min_value=0, step=1, key="eh" + k,
                                         value=None if pd.isna(r["hospital_visits"]) else int(r["hospital_visits"]))
                e_cat = st.selectbox("AQI category", AQI_CATEGORIES, index=AQI_CATEGORIES.index(r["aqi_category"]), key="ec" + k)
                saved = st.form_submit_button("Save changes")
            if saved:
                changes = {}
                if e_date.isoformat() != r["date"]:
                    changes["date"] = e_date
                if e_area != r["area"]:
                    changes["area"] = e_area
                for col, new in (("respiratory_cases", e_resp), ("hospital_visits", e_hosp)):
                    if pd.isna(r[col]) and new is None:
                        continue
                    if pd.isna(r[col]) or new is None or int(new) != int(r[col]):
                        changes[col] = new
                if e_cat != r["aqi_category"]:
                    changes["aqi_category"] = e_cat
                if not changes:
                    st.info("No changes to save.")
                else:
                    ok, out = safe(m.update, int(rid), changes)
                    if ok:
                        st.session_state["msg"] = f"Record {int(rid)} updated."
                        st.rerun()

with t_del:
    if all_df.empty:
        st.info("There are no records to delete.")
    else:
        did = st.number_input("Record ID to delete", min_value=1, step=1, value=int(all_df["record_id"].min()), key="del_id")
        rows = all_df[all_df["record_id"] == did]
        if rows.empty:
            st.warning("No record with that ID.")
        else:
            st.dataframe(rows, hide_index=True)
            sure = st.checkbox("Yes, delete this record", key="del_ok" + str(int(did)))
            if st.button("Delete record", disabled=not sure):
                ok, out = safe(m.delete, int(did))
                if ok:
                    st.session_state["msg"] = f"Record {int(did)} deleted."
                    st.rerun()

with t_report:
    report = m.export_report(f, filters)
    st.text(report)
    st.download_button("Download report", report, file_name="health_impact_report.txt", mime="text/plain")
