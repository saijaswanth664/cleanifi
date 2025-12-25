import streamlit as st
import pandas as pd
import numpy as np
import re
from io import BytesIO

# ---------------- PAGE CONFIG ----------------
st.set_page_config(page_title="CLEANIFI", page_icon="🧹", layout="wide")

# ---------------- THEME ----------------
dark = st.toggle("🌗 Light / Dark Mode", value=True)

bg = "#0f172a" if dark else "#f8fafc"
card = "rgba(255,255,255,0.08)" if dark else "rgba(0,0,0,0.05)"
text = "#ffffff" if dark else "#0f172a"

# ---------------- CSS ----------------
st.markdown(f"""
<style>
body {{ background-color: {bg}; color: {text}; }}
.card {{
    background: {card};
    backdrop-filter: blur(12px);
    padding: 20px;
    border-radius: 18px;
    margin-bottom: 15px;
}}
h1 {{
    background: linear-gradient(90deg, #38bdf8, #a855f7);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}}
</style>
""", unsafe_allow_html=True)

# ---------------- HEADER ----------------
st.image("cleanify_logo.png", width=80)
st.markdown("<h1>CLEANIFI</h1>", unsafe_allow_html=True)
st.caption("AI-Assisted • Human-in-the-Loop Data Cleaning")

# ---------------- HELPERS ----------------
def snake_case(col):
    return re.sub(r'[^a-z0-9_]', '', col.lower().replace(" ", "_"))

def detect_type(series):
    if pd.api.types.is_datetime64_any_dtype(series):
        return "datetime"
    if pd.api.types.is_numeric_dtype(series):
        return "numeric"
    return "text"

def quality_score(df):
    return int((1 - df.isnull().sum().sum() / df.size) * 100)

# ---------------- FILE UPLOAD ----------------
file = st.file_uploader("📤 Upload Excel File", type=["xlsx"])

if file:
    df_original = pd.read_excel(file)
    df = df_original.copy()

    # ---------- COLUMN NAME PREVIEW ----------
    old_cols = df.columns.tolist()
    new_cols = [snake_case(c) for c in old_cols]

    st.subheader("🔁 Column Name Standardization")
    mapping_df = pd.DataFrame({
        "Original Column": old_cols,
        "Snake_Case Column": new_cols
    })
    st.dataframe(mapping_df)

    df.columns = new_cols

    # ---------- RENAME COLUMNS ----------
    st.subheader("✏ Rename Columns (Optional)")
    rename_map = {}
    for c in df.columns:
        new_name = st.text_input(f"{c}", c)
        if new_name != c:
            rename_map[c] = snake_case(new_name)

    if rename_map:
        df.rename(columns=rename_map, inplace=True)

    # ---------- DELETE COLUMNS ----------
    st.subheader("🗑 Delete Columns")
    delete_cols = st.multiselect("Select columns to delete", df.columns)
    if delete_cols:
        df.drop(columns=delete_cols, inplace=True)

    # ---------- CLEANING OPTIONS ----------
    st.subheader("🧠 Missing Value Handling")
    rules = {}

    for col in df.columns:
        if df[col].isnull().sum() == 0:
            continue

        col_type = detect_type(df[col])

        with st.container():
            st.markdown(f"<div class='card'><b>{col}</b> ({col_type})", unsafe_allow_html=True)

            if col_type == "numeric":
                method = st.selectbox(
                    "Method",
                    ["Mean", "Median", "Mode", "Keep NaN", "Delete Rows"],
                    key=f"{col}_method"
                )
                dtype = st.selectbox(
                    "Output Type", ["Float", "Integer"], key=f"{col}_dtype"
                )
                decimals = st.slider("Decimals", 0, 6, 2, key=f"{col}_dec") if dtype == "Float" else None

            elif col_type == "text":
                method = st.selectbox(
                    "Method",
                    ["Mode", "Keep NaN", "Delete Rows"],
                    key=f"{col}_method"
                )
                dtype = None
                decimals = None

            else:  # datetime
                method = st.selectbox(
                    "Method",
                    ["Forward Fill", "Backward Fill", "Most Frequent", "Keep NaN", "Delete Rows"],
                    key=f"{col}_method"
                )
                dtype = None
                decimals = None

            rules[col] = (method, dtype, decimals)
            st.markdown("</div>", unsafe_allow_html=True)

    # ---------- APPLY CLEANING ----------
    if st.button("🚀 Apply Data Cleaning"):
        for col, (method, dtype, decimals) in rules.items():
            if method == "Keep NaN":
                continue

            if method == "Delete Rows":
                df.dropna(subset=[col], inplace=True)
                continue

            if method in ["Mean", "Median", "Mode"]:
                value = getattr(df[col], method.lower())()
                df[col].fillna(value, inplace=True)

            elif method == "Forward Fill":
                df[col].fillna(method="ffill", inplace=True)
            elif method == "Backward Fill":
                df[col].fillna(method="bfill", inplace=True)
            elif method == "Most Frequent":
                df[col].fillna(df[col].mode()[0], inplace=True)

            if dtype == "Integer":
                df[col] = pd.to_numeric(df[col], errors="coerce").round().astype("Int64")
            elif dtype == "Float":
                df[col] = df[col].round(decimals)

        st.success("✅ Data cleaned successfully")

    # ---------- REPORT ----------
    st.subheader("📊 Data Quality Report")

    r, c = df.shape
    missing = df.isnull().sum().sum()
    score = quality_score(df)

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Rows", r)
    col2.metric("Columns", c)
    col3.metric("Missing Cells", missing)
    col4.metric("Quality Score", f"{score}%")

    # ---------- PREVIEW ----------
    st.subheader("📄 Cleaned Dataset")
    st.dataframe(df)

    # ---------- DOWNLOAD ----------
    buffer = BytesIO()
    df.to_excel(buffer, index=False)
    st.download_button(
        "⬇ Download Cleaned Excel",
        buffer.getvalue(),
        "cleanifi_cleaned.xlsx"
    )
