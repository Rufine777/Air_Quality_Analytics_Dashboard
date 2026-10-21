import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import streamlit as st

st.set_page_config(page_title="Pollution Sources", layout="wide")

try:
    from manager.page3_manager import PollutionSourceManager, SECTORS, TYPES, YEARS
    from ui import apply_theme
except ModuleNotFoundError as e:
    st.error(f"Missing dependency: {e}. Run `pip install -r requirements.txt`.")
    st.stop()

apply_theme()


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
        BG = "#111827"
        FG = "#e5e7eb"
        GRID = "#1f2937"
        ACCENT = "#38bdf8"

        def style_ax(ax):
            ax.set_facecolor(BG)
            ax.figure.set_facecolor(BG)
            ax.tick_params(colors=FG)
            ax.xaxis.label.set_color(FG)
            ax.yaxis.label.set_color(FG)
            ax.title.set_color(FG)
            for spine in ax.spines.values():
                spine.set_color(GRID)
            ax.grid(True, color=GRID, alpha=0.5)

        a, b = st.columns(2)

        # 1. Emission share by sector (pie)
        fig, ax = plt.subplots(figsize=(5, 4))
        sec = m.by_sector(f)
        ax.pie(sec["emission_level"], labels=sec["sector"], autopct="%1.1f%%",
               colors=["#38bdf8", "#a78bfa", "#34d399", "#fbbf24", "#f87171", "#60a5fa"],
               textprops={"color": FG, "fontsize": 9})
        ax.set_title("Emission share by sector", color=FG)
        fig.set_facecolor(BG)
        a.pyplot(fig, use_container_width=True)
        plt.close(fig)

        # 2. Top 10 locations by average emission (horizontal bar)
        fig, ax = plt.subplots(figsize=(5, 4))
        top = m.top_locations(f, 10).sort_values("emission_level")
        ax.barh(top["location"], top["emission_level"], color=ACCENT)
        ax.set_title("Top 10 locations by average emission", color=FG)
        ax.set_xlabel("Average emission", color=FG)
        style_ax(ax)
        a2_col = b
        b.pyplot(fig, use_container_width=True)
        plt.close(fig)

        a2, b2 = st.columns(2)

        # 3. Total emission per year (line per sector)
        fig, ax = plt.subplots(figsize=(5, 4))
        by = m.by_year(f)
        for sector, g in by.groupby("sector"):
            g = g.sort_values("year")
            ax.plot(g["year"], g["emission_level"], marker="o", label=sector)
        ax.set_title("Total emission per year", color=FG)
        ax.set_xlabel("Year", color=FG)
        ax.set_ylabel("Emission", color=FG)
        ax.set_xticks(sorted(by["year"].unique()))
        style_ax(ax)
        ax.legend(fontsize=8, facecolor=BG, edgecolor=GRID, labelcolor=FG)
        a2.pyplot(fig, use_container_width=True)
        plt.close(fig)

        # 4. Distribution of emission levels (histogram, log scale)
        fig, ax = plt.subplots(figsize=(5, 4))
        ax.hist(f["emission_level"], bins=30, color=ACCENT, log=True)
        ax.set_title("Distribution of emission levels (log scale)", color=FG)
        ax.set_xlabel("Emission level", color=FG)
        ax.set_ylabel("Count (log)", color=FG)
        style_ax(ax)
        b2.pyplot(fig, use_container_width=True)
        plt.close(fig)

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
