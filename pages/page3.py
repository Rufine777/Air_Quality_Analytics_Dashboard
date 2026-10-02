import plotly.express as px
import streamlit as st

from manager.page3_manager import PollutionSourceManager, SECTORS, TYPES, YEARS

st.set_page_config(page_title="Pollution Sources", layout="wide")


def safe(action, *args):
    try:
        return True, action(*args)
    except (FileNotFoundError, ValueError, TypeError, OSError) as e:
        st.error(str(e))
        return False, None


m = PollutionSourceManager()
ok, all_df = safe(m.load_data)
if not ok:
    st.stop()

st.title("Pollution Sources Dashboard")

if "msg" in st.session_state:
    st.success(st.session_state.pop("msg"))

st.sidebar.header("Filters")
sec = st.sidebar.multiselect("Sector", SECTORS, default=SECTORS)
typ = st.sidebar.multiselect("Source type", TYPES, default=TYPES)
yr = st.sidebar.slider("Year range", 2024, 2026, (2024, 2026))
txt = st.sidebar.text_input("Search location", key="location_search")

f = m.filter_data(sec, typ, yr[0], yr[1], txt)
s = m.stats(f)
ftxt = "sectors=" + ", ".join(sec) + "; types=" + ", ".join(typ) + "; years=" + str(yr[0]) + "-" + str(yr[1]) + "; search=" + txt
st.write("Showing " + str(len(f)) + " of " + str(len(all_df)) + " records after the source overlap rule")

t1, t2, t3, t4, t5, t6 = st.tabs(["View", "Charts", "Add", "Edit", "Delete", "Report"])

with t1:
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Records", s["count"])
    if s["mean"] is None:
        c2.metric("Mean emission", "—")
        c3.metric("Highest emission", "—")
    else:
        c2.metric("Mean emission", round(s["mean"], 2))
        c3.metric("Highest emission", round(s["max"], 2))
    c4.metric("Top location", s["top"])
    if len(f) == 0:
        st.info("No records match these filters.")
    else:
        a, b = st.columns(2)
        a.write("Total emission by sector")
        a.dataframe(m.by_sector(f), hide_index=True)
        b.write("Records by source type")
        b.dataframe(m.by_type(f), hide_index=True)
        col = st.selectbox("Sort by", list(f.columns))
        order = st.radio("Order", ["Ascending", "Descending"], horizontal=True)
        st.dataframe(m.sort_data(f, col, order == "Ascending"), hide_index=True)

with t2:
    if len(f) == 0:
        st.info("No records match these filters.")
    else:
        a, b = st.columns(2)
        a.plotly_chart(px.pie(m.by_sector(f), names="sector", values="emission_level", title="Emission share by sector"))
        b.plotly_chart(px.bar(m.top_locations(f, 10), x="emission_level", y="location", orientation="h", title="Top 10 locations by average emission"))
        a2, b2 = st.columns(2)
        fig = px.line(m.by_year(f), x="year", y="emission_level", color="sector", markers=True, title="Total emission per year")
        fig.update_xaxes(dtick=1)
        a2.plotly_chart(fig)
        b2.plotly_chart(px.histogram(f, x="emission_level", nbins=30, log_y=True, title="Distribution of emission levels (log scale)"))
        st.caption("Buildings use district totals and other sectors use point sources. Overlapping rows are excluded from analysis but remain unchanged in the CSV.")

with t3:
    with st.form("add_form"):
        year = st.selectbox("Year", YEARS)
        loc = st.text_input("Location")
        sector = st.selectbox("Sector", SECTORS)
        sub = st.text_input("Subsector")
        typ2 = st.selectbox("Source type", TYPES)
        em = st.number_input("Emission level", min_value=0.0, step=0.1)
        asset = st.text_input("Asset type (leave blank for Unknown)")
        go = st.form_submit_button("Add record")
    if go:
        rec = {"record_id": m.next_id(), "year": year, "location": loc, "sector": sector, "subsector": sub, "source_type": typ2, "pollutant": "pm2_5", "emission_level": em, "asset_type": asset}
        ok, out = safe(m.create, rec)
        if ok:
            st.session_state["msg"] = "Record added."
            st.rerun()

with t4:
    rid = st.number_input("Record ID to edit", min_value=1, step=1, key="edit_id")
    rows = all_df[all_df["record_id"] == rid]
    if len(rows) == 0:
        st.warning("No record with that ID.")
    else:
        r = rows.iloc[0]
        k = str(rid)
        with st.form("edit_form"):
            year = st.selectbox("Year", YEARS, index=YEARS.index(int(r["year"])), key="ey" + k)
            loc = st.text_input("Location", value=str(r["location"]), key="el" + k)
            sector = st.selectbox("Sector", SECTORS, index=SECTORS.index(r["sector"]), key="es" + k)
            sub = st.text_input("Subsector", value=str(r["subsector"]), key="eu" + k)
            typ2 = st.selectbox("Source type", TYPES, index=TYPES.index(r["source_type"]), key="et" + k)
            em = st.number_input("Emission level", min_value=0.0, value=float(r["emission_level"]), step=0.1, key="ee" + k)
            asset = st.text_input("Asset type", value=str(r["asset_type"]), key="ea" + k)
            go = st.form_submit_button("Save changes")
        if go:
            upd = {"year": year, "location": loc, "sector": sector, "subsector": sub, "source_type": typ2, "emission_level": em, "asset_type": asset}
            ok, out = safe(m.update, int(rid), upd)
            if ok:
                st.session_state["msg"] = "Record updated."
                st.rerun()

with t5:
    rid = st.number_input("Record ID to delete", min_value=1, step=1, key="del_id")
    rows = all_df[all_df["record_id"] == rid]
    if len(rows) == 0:
        st.warning("No record with that ID.")
    else:
        st.dataframe(rows, hide_index=True)
        sure = st.checkbox("Yes, delete this record")
        if st.button("Delete", disabled=not sure):
            ok, out = safe(m.delete, int(rid))
            if ok:
                st.session_state["msg"] = "Record deleted."
                st.rerun()

with t6:
    text = m.report(f, ftxt)
    st.text(text)
    st.download_button("Download report", text, file_name="pollution_report.txt")
