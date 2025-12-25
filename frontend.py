import streamlit as st
import pandas as pd

# BACKEND IMPORT (UNCHANGED)
from app import snake_case, detect_type

st.set_page_config(page_title="CLEANIFI", page_icon="🧹", layout="wide")

# ---------------- UI STYLE ----------------
st.markdown("""
<style>
.glass {
    background: rgba(255,255,255,0.1);
    backdrop-filter: blur(15px);
    border-radius: 16px;
    padding: 20px;
    margin-bottom: 20px;
}
</style>
""", unsafe_allow_html=True)

st.markdown("<div class='glass'><h1>CLEANIFI</h1><p>Step-by-Step Data Cleaning</p></div>", unsafe_allow_html=True)

# ---------------- SESSION STATE ----------------
if "step" not in st.session_state:
    st.session_state.step = 0
if "raw_df" not in st.session_state:
    st.session_state.raw_df = None
if "work_df" not in st.session_state:
    st.session_state.work_df = None

# ---------------- FILE UPLOAD ----------------
file = st.file_uploader("Upload Dataset", type=["csv", "xlsx"])

if file and st.session_state.raw_df is None:
    if file.name.endswith(".csv"):
        df = pd.read_csv(file)
    else:
        df = pd.read_excel(file)

    st.session_state.raw_df = df
    st.session_state.work_df = df.copy()
    st.session_state.step = 1

# ---------------- STEP 1 ----------------
if st.session_state.step == 1:
    st.subheader("Step 1: Standardize Column Names")

    preview = st.session_state.work_df.copy()
    preview.columns = [snake_case(c) for c in preview.columns]

    st.dataframe(preview.head(50), use_container_width=True)

    c1, c2 = st.columns(2)
    if c1.button("Apply", key="step1_apply"):
        st.session_state.work_df = preview
        st.session_state.step = 2
    if c2.button("No Need", key="step1_skip"):
        st.session_state.step = 2

# ---------------- STEP 2 ----------------
if st.session_state.step == 2:
    st.subheader("Step 2: Remove Duplicates")

    preview = st.session_state.work_df.drop_duplicates()
    st.dataframe(preview.head(50), use_container_width=True)

    c1, c2 = st.columns(2)
    if c1.button("Apply", key="step2_apply"):
        st.session_state.work_df = preview
        st.session_state.step = 3
    if c2.button("No Need", key="step2_skip"):
        st.session_state.step = 3

# ---------------- STEP 3 ----------------
if st.session_state.step == 3:
    st.subheader("Step 3: Handle Missing Values")

    preview = st.session_state.work_df.copy()
    for col in preview.columns:
        if preview[col].isnull().sum() > 0:
            if detect_type(preview[col]) == "numeric":
                preview[col] = preview[col].fillna(preview[col].mean())
            else:
                preview[col] = preview[col].fillna("Unknown")

    st.dataframe(preview.head(50), use_container_width=True)

    c1, c2 = st.columns(2)
    if c1.button("Apply", key="step3_apply"):
        st.session_state.work_df = preview
        st.session_state.step = 4
    if c2.button("No Need", key="step3_skip"):
        st.session_state.step = 4

# ---------------- FINAL ----------------
if st.session_state.step == 4:
    st.subheader("Final Cleaned Dataset")
    st.dataframe(st.session_state.work_df, use_container_width=True)

    st.download_button(
        "Download CSV",
        st.session_state.work_df.to_csv(index=False),
        "cleaned_data.csv",
        key="download_final"
    )
