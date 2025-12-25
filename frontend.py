import streamlit as st
import pandas as pd
import numpy as np

# backend helpers (READ ONLY)
from app import snake_case, detect_type

# ---------------- PAGE CONFIG ----------------
st.set_page_config(
    page_title="CLEANIFI – Stepwise Cleaning",
    page_icon="🧹",
    layout="wide"
)

# ---------------- CSS ----------------
st.markdown("""
<style>
.glass {
    background: rgba(255,255,255,0.08);
    backdrop-filter: blur(18px);
    border-radius: 18px;
    padding: 20px;
    border: 1px solid rgba(255,255,255,0.15);
    margin-bottom: 20px;
}
.stButton>button {
    border-radius: 12px;
    font-weight: 600;
}
</style>
""", unsafe_allow_html=True)

# ---------------- HEADER ----------------
st.markdown("<div class='glass'><h1>CLEANIFI</h1><p>Step-by-step Data Cleaning Preview</p></div>", unsafe_allow_html=True)

# ---------------- SESSION STATE INIT ----------------
if "step" not in st.session_state:
    st.session_state.step = 0
if "work_df" not in st.session_state:
    st.session_state.work_df = None
if "raw_df" not in st.session_state:
    st.session_state.raw_df = None

# ---------------- UPLOAD ----------------
file = st.file_uploader("📤 Upload CSV or Excel", type=["csv", "xlsx"])

if file and st.session_state.raw_df is None:
    if file.name.endswith(".csv"):
        st.session_state.raw_df = pd.read_csv(file)
    else:
        st.session_state.raw_df = pd.read_excel(file)

    st.session_state.work_df = st.session_state.raw_df.copy()
    st.session_state.step = 1

# ---------------- STEP 1 ----------------
if st.session_state.step == 1:
    st.markdown("<div class='glass'><h3>Step 1: Column Name Standardization</h3></div>", unsafe_allow_html=True)

    preview_df = st.session_state.work_df.copy()
    preview_df.columns = [snake_case(c) for c in preview_df.columns]

    st.subheader("🔍 Preview")
    st.dataframe(preview_df.head(50), use_container_width=True)

    c1, c2 = st.columns(2)
    with c1:
        if st.button("✅ Apply"):
            st.session_state.work_df = preview_df
            st.session_state.step = 2
    with c2:
        if st.button("❌ No Need"):
            st.session_state.step = 2

# ---------------- STEP 2 ----------------
if st.session_state.step == 2:
    st.markdown("<div class='glass'><h3>Step 2: Remove Duplicate Rows</h3></div>", unsafe_allow_html=True)

    preview_df = st.session_state.work_df.drop_duplicates()

    st.subheader("🔍 Preview")
    st.dataframe(preview_df.head(50), use_container_width=True)

    c1, c2 = st.columns(2)
    with c1:
        if st.button("✅ Apply"):
            st.session_state.work_df = preview_df
            st.session_state.step = 3
    with c2:
        if st.button("❌ No Need"):
            st.session_state.step = 3

# ---------------- STEP 3 ----------------
if st.session_state.step == 3:
    st.markdown("<div class='glass'><h3>Step 3: Handle Missing Values</h3></div>", unsafe_allow_html=True)

    preview_df = st.session_state.work_df.copy()

    for col in preview_df.columns:
        if preview_df[col].isnull().sum() > 0:
            if detect_type(preview_df[col]) == "numeric":
                preview_df[col] = preview_df[col].fillna(preview_df[col].mean())
            else:
                preview_df[col] = preview_df[col].fillna("Unknown")

    st.subheader("🔍 Preview")
    st.dataframe(preview_df.head(50), use_container_width=True)

    c1, c2 = st.columns(2)
    with c1:
        if st.button("✅ Apply"):
            st.session_state.work_df = preview_df
            st.session_state.step = 4
    with c2:
        if st.button("❌ No Need"):
            st.session_state.step = 4

# ---------------- FINAL ----------------
if st.session_state.step == 4:
    st.markdown("<div class='glass'><h3>✅ Final Cleaned Dataset</h3></div>", unsafe_allow_html=True)

    st.dataframe(st.session_state.work_df, use_container_width=True)

    st.download_button(
        "⬇ Download Cleaned Data",
        st.session_state.work_df.to_csv(index=False),
        file_name="cleaned_data.csv",
        mime="text/csv"
    )
