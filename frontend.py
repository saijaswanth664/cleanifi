import streamlit as st
import pandas as pd
from io import BytesIO
import time

# 🔗 IMPORT BACKEND (NO LOGIC CHANGED)
from app import snake_case, detect_type, quality_score

# ---------------- PAGE CONFIG ----------------
st.set_page_config(
    page_title="CLEANIFI",
    page_icon="🧹",
    layout="wide"
)

# ---------------- CSS ----------------
st.markdown("""
<style>
html, body {
    background: radial-gradient(circle at top, #1e293b, #020617);
    color: #e5e7eb;
    font-family: 'Inter', sans-serif;
}

.glass {
    background: rgba(255,255,255,0.08);
    backdrop-filter: blur(18px);
    border-radius: 20px;
    padding: 24px;
    border: 1px solid rgba(255,255,255,0.15);
    box-shadow: 0 10px 30px rgba(0,0,0,0.4);
    margin-bottom: 22px;
}

.title {
    font-size: 42px;
    font-weight: 800;
    background: linear-gradient(90deg,#38bdf8,#a855f7);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}

.subtitle {
    opacity: 0.7;
    font-size: 15px;
}

.progress-step {
    display: flex;
    gap: 10px;
    margin-top: 12px;
}

.step {
    flex: 1;
    height: 6px;
    border-radius: 10px;
    background: rgba(255,255,255,0.15);
}

.step.active {
    background: linear-gradient(90deg,#38bdf8,#a855f7);
}

.stButton>button {
    border-radius: 14px;
    font-weight: 600;
    padding: 0.6rem 1.6rem;
    transition: all 0.2s ease;
}

.stButton>button:hover {
    transform: scale(1.05);
    box-shadow: 0 6px 20px rgba(0,0,0,0.4);
}
</style>
""", unsafe_allow_html=True)

# ---------------- HEADER ----------------
st.markdown("""
<div class="glass">
    <div style="display:flex;align-items:center;gap:18px">
        <img src="assets/cleanifi_logo.png" width="80">
        <div>
            <div class="title">CLEANIFI</div>
            <div class="subtitle">Premium Intelligent Data Cleaning Platform</div>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# ---------------- UPLOAD ----------------
st.markdown("<div class='glass'>", unsafe_allow_html=True)
uploaded = st.file_uploader("📤 Upload CSV or Excel File", type=["csv","xlsx"])
st.markdown("</div>", unsafe_allow_html=True)

if uploaded:
    # ---------------- STEP 1 ----------------
    st.markdown("<div class='glass'>", unsafe_allow_html=True)
    st.subheader("Step 1 · Data Preview")

    if uploaded.name.endswith(".csv"):
        df = pd.read_csv(uploaded)
    else:
        df = pd.read_excel(uploaded)

    st.dataframe(df, use_container_width=True)

    st.markdown("""
    <div class="progress-step">
        <div class="step active"></div>
        <div class="step"></div>
        <div class="step"></div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)

    # ---------------- OPTIONS ----------------
    st.markdown("<div class='glass'>", unsafe_allow_html=True)
    st.subheader("Step 2 · Cleaning Configuration")

    c1, c2, c3 = st.columns(3)
    with c1:
        rename_cols = st.checkbox("Snake Case Columns", True)
    with c2:
        drop_dupes = st.checkbox("Remove Duplicates", True)
    with c3:
        fill_missing = st.checkbox("Fill Missing Values", True)

    st.markdown("""
    <div class="progress-step">
        <div class="step active"></div>
        <div class="step active"></div>
        <div class="step"></div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)

    # ---------------- CLEAN ----------------
    if st.button("🚀 Run Cleaning Pipeline"):
        with st.spinner("Applying intelligent cleaning..."):
            time.sleep(1.2)

        clean_df = df.copy()

        if rename_cols:
            clean_df.columns = [snake_case(c) for c in clean_df.columns]

        if drop_dupes:
            clean_df = clean_df.drop_duplicates()

        if fill_missing:
            for col in clean_df.columns:
                dtype = detect_type(clean_df[col])
                if dtype == "numeric":
                    clean_df[col] = clean_df[col].fillna(clean_df[col].mean())
                else:
                    clean_df[col] = clean_df[col].fillna("Unknown")

        score = quality_score(df, clean_df)

        # ---------------- RESULT ----------------
        st.markdown("<div class='glass'>", unsafe_allow_html=True)
        st.subheader("Step 3 · Cleaned Output")

        st.dataframe(clean_df, use_container_width=True)

        st.markdown("### 📊 Data Quality Score")
        st.progress(score / 100)
        st.markdown(f"**{score}% Quality Improvement Achieved**")

        buffer = BytesIO()
        clean_df.to_csv(buffer, index=False)
        buffer.seek(0)

        st.download_button(
            "⬇ Download Cleaned Data",
            buffer,
            file_name="cleaned_data.csv",
            mime="text/csv"
        )

        st.markdown("""
        <div class="progress-step">
            <div class="step active"></div>
            <div class="step active"></div>
            <div class="step active"></div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("</div>", unsafe_allow_html=True)
