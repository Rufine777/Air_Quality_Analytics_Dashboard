import streamlit as st

st.set_page_config(page_title="University Pollution Project", layout="wide")

st.title("University Pollution Project")
st.write("Open the dashboard to explore the latest pollution-source data.")
st.page_link("pages/page3.py", label="Open Pollution Sources Dashboard")
