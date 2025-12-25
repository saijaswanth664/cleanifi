import streamlit as st
import pandas as pd
import numpy as np

# 🔗 BACKEND HELPERS (READ ONLY)
from app import detect_type, quality_score, snake_case

# ---------------- PAGE CONFIG ----------------
st.set_page_config(
    page_title="CLEANIFI – AI Cleaning Advisor",
    page_icon="🧹",
    layout="wide"
)

# ---------------- CSS ----------------
st.markdown("""
<style>
html, body {
    background: radial-gradient(circle at top, #1e293b, #020617);
    color: #e5e7eb;
    font-family: Inter, sans-serif;
}

.glass {
    background: rgba(255,255,255,0.08);
    backdrop-filter: blur(18px);
    border-radius: 22px;
    padding: 24px;
    border: 1px solid rgba(255,255,255,0.15);
    box-shadow: 0 12px 35px rgba(0,0,0,0.45);
    margin-bottom: 24px;
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

.tag {
    padding: 6px 14px;
    border-radius: 999px;
    font-size: 12px;
    font-weight: 600;
}

.high {
    background: rgba(239,68,68,0.2);
    color: #fecaca;
}

.medium {
    background: rgba(245,158,11,0.2);
    color: #fde68a;
}

.low {
    background: rgba(34,197,94,0.2);
    color: #bbf7d0;
}
</style>
""", unsafe_allow_html=True)

# ---------------- HEADER ----------------
st.markdown("""
<div class="glass">
  <div style="display:flex;align-items:center;gap:18px">
    <img src="assets/cleanifi_logo.png" width="85">
    <div>
      <div class="title">CLEANIFI</div>
      <div class="subtitle">AI-Style Data Cleaning Recommendations</div>
    </div>
  </div>
</div>
""", unsafe_allow_html=True)

# ---------------- UPLOAD ----------------
st.markdown("<div class='glass'>", unsafe_allow_html=True)
file = st.file_uploader("📤 Upload CSV or Excel Dataset", type=["csv", "xlsx"])
st.markdown("</div>", unsafe_allow_html=True)

if file:
    # ---------------- LOAD DATA ----------------
    if file.name.endswith(".csv"):
        df = pd.read_csv(file)
    else:
        df = pd.read_excel(file)

    rows, cols = df.shape
    score = quality_score(df)

    # ---------------- EXEC SUMMARY ----------------
    st.markdown("<div class='glass'>", unsafe_allow_html=True)
    st.subheader("🧠 AI Quality Summary")

    if score >= 90:
        verdict = "🟢 Dataset quality is excellent. Minimal cleaning required."
    elif score >= 70:
        verdict = "🟡 Dataset quality is moderate. Cleaning recommended."
    else:
        verdict = "🔴 Dataset quality is poor. Significant cleaning required."

    st.markdown(f"""
    **Overall Quality Score:** {score}%  
    **AI Verdict:** {verdict}
    """)

    st.markdown("</div>", unsafe_allow_html=True)

    # ---------------- AI RECOMMENDATIONS ----------------
    st.markdown("<div class='glass'>", unsafe_allow_html=True)
    st.subheader("🤖 AI-Generated Cleaning Recommendations")

    for col in df.columns:
        col_data = df[col]
        col_type = detect_type(col_data)
        missing = col_data.isnull().sum()
        missing_pct = (missing / rows) * 100
        unique = col_data.nunique(dropna=True)

        recommendations = []

        # Missing values
        if missing_pct > 30:
            recommendations.append((
                "High",
                f"Column **{col}** has {round(missing_pct,2)}% missing values. Consider removal or advanced imputation."
            ))
        elif missing_pct > 5:
            recommendations.append((
                "Medium",
                f"Column **{col}** has moderate missing values. Imputation recommended."
            ))

        # Duplicates / low variance
        if unique <= 1:
            recommendations.append((
                "High",
                f"Column **{col}** has no variance and provides no analytical value."
            ))
        elif unique < rows * 0.05:
            recommendations.append((
                "Medium",
                f"Column **{col}** has low uniqueness. Review for redundancy."
            ))

        # Data type issues
        if col_type == "text" and col_data.str.len().mean() > 50:
            recommendations.append((
                "Low",
                f"Column **{col}** contains long text. NLP preprocessing may be needed."
            ))

        if recommendations:
            st.markdown(f"### 🔹 {col}")
            for level, text in recommendations:
                css = "high" if level == "High" else "medium" if level == "Medium" else "low"
                st.markdown(
                    f"<span class='tag {css}'>{level} Priority</span> &nbsp; {text}",
                    unsafe_allow_html=True
                )

    st.markdown("</div>", unsafe_allow_html=True)

    # ---------------- DISCLAIMER ----------------
    st.markdown("<div class='glass'>", unsafe_allow_html=True)
    st.caption("""
    ⚠️ These recommendations are AI-style, explainable suggestions generated from data patterns.
    No backend logic or automatic cleaning has been applied.
    """)
    st.markdown("</div>", unsafe_allow_html=True)
