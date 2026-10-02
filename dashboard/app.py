import streamlit as st
import pandas as pd
import json
import sys
from pathlib import Path

# Add parent directory to system path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import get_all_scholarships, get_scholarship_history, init_db
from app.config import DB_PATH
from run import run_pipeline

st.set_page_config(
    page_title="Scholarship Intelligence Dashboard",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for modern design aesthetics
st.markdown("""
<style>
    .main-header {
        font-size: 2.2rem;
        font-weight: 700;
        color: #1E293B;
        margin-bottom: 0.2rem;
    }
    .sub-header {
        font-size: 1.05rem;
        color: #64748B;
        margin-bottom: 1.5rem;
    }
    .metric-card {
        background: #F8FAFC;
        border: 1px solid #E2E8F0;
        border-radius: 10px;
        padding: 1.2rem;
        text-align: center;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }
    .metric-value {
        font-size: 1.8rem;
        font-weight: 700;
        color: #0F172A;
    }
    .metric-label {
        font-size: 0.85rem;
        color: #64748B;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    .status-badge-verified {
        background-color: #DCFCE7;
        color: #15803D;
        padding: 4px 10px;
        border-radius: 20px;
        font-weight: 600;
        font-size: 0.8rem;
    }
    .status-badge-review {
        background-color: #FEF3C7;
        color: #B45309;
        padding: 4px 10px;
        border-radius: 20px;
        font-weight: 600;
        font-size: 0.8rem;
    }
    .status-badge-expired {
        background-color: #FEE2E2;
        color: #B91C1C;
        padding: 4px 10px;
        border-radius: 20px;
        font-weight: 600;
        font-size: 0.8rem;
    }
    .status-badge-stale {
        background-color: #F1F5F9;
        color: #475569;
        padding: 4px 10px;
        border-radius: 20px;
        font-weight: 600;
        font-size: 0.8rem;
    }
</style>
""", unsafe_allow_html=True)

# Ensure DB is initialized
init_db()

# Load data
records = get_all_scholarships()

st.markdown('<div class="main-header">🎓 EDXSO Scholarship Intelligence System</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Authentic Scholarship Opportunities for Indian Students — Automated Crawler, Verification Audit & Change Detection</div>', unsafe_allow_html=True)

# Sidebar
st.sidebar.image("https://img.icons8.com/isometric/100/graduation-cap.png", width=70)
st.sidebar.title("Controls & Filters")

if st.sidebar.button("⚡ Run Live Crawler Pipeline", use_container_width=True):
    with st.spinner("Executing Crawler & Verification Pipeline..."):
        run_pipeline()
        st.sidebar.success("Crawl pipeline finished successfully!")
        st.rerun()

st.sidebar.divider()

# Search and Filters
search_query = st.sidebar.text_input("🔍 Search Scholarship / Provider", "")

source_types = ["All"] + sorted(list(set(r["source_type"] for r in records))) if records else ["All"]
selected_source = st.sidebar.selectbox("Category / Source Type", source_types)

statuses = ["All", "VERIFIED", "REVIEW_REQUIRED", "EXPIRED", "STALE"]
selected_status = st.sidebar.selectbox("Verification Status", statuses)

min_confidence = st.sidebar.slider("Minimum Confidence Score (%)", 0.0, 100.0, 0.0, 5.0)

# Filter Data
filtered = records.copy()

if search_query:
    q = search_query.lower()
    filtered = [r for r in filtered if q in r["title"].lower() or q in r["provider"].lower()]

if selected_source != "All":
    filtered = [r for r in filtered if r["source_type"] == selected_source]

if selected_status != "All":
    filtered = [r for r in filtered if r["status"] == selected_status]

filtered = [r for r in filtered if r["confidence_score"] >= min_confidence]

# Top KPI Summary Cards
col1, col2, col3, col4, col5 = st.columns(5)

total_records = len(records)
verified_count = sum(1 for r in records if r["status"] == "VERIFIED")
review_count = sum(1 for r in records if r["status"] == "REVIEW_REQUIRED")
expired_stale_count = sum(1 for r in records if r["status"] in ["EXPIRED", "STALE"])
govt_count = sum(1 for r in records if r["source_type"] == "Government")

with col1:
    st.markdown(f'<div class="metric-card"><div class="metric-value">{total_records}</div><div class="metric-label">Total Tracked</div></div>', unsafe_allow_html=True)
with col2:
    st.markdown(f'<div class="metric-card"><div class="metric-value" style="color:#15803D;">{verified_count}</div><div class="metric-label">Verified (≥95%)</div></div>', unsafe_allow_html=True)
with col3:
    st.markdown(f'<div class="metric-card"><div class="metric-value" style="color:#B45309;">{review_count}</div><div class="metric-label">Review Req.</div></div>', unsafe_allow_html=True)
with col4:
    st.markdown(f'<div class="metric-card"><div class="metric-value" style="color:#B91C1C;">{expired_stale_count}</div><div class="metric-label">Expired / Stale</div></div>', unsafe_allow_html=True)
with col5:
    st.markdown(f'<div class="metric-card"><div class="metric-value" style="color:#1E40AF;">{govt_count}</div><div class="metric-label">Govt Schemes</div></div>', unsafe_allow_html=True)

st.write("")
st.subheader(f"Scholarship Opportunities ({len(filtered)} items shown)")

if not filtered:
    st.info("No scholarships match the selected filter criteria.")
else:
    # Prepare Display Table
    table_data = []
    for r in filtered:
        status_html = f"**{r['status']}**"
        table_data.append({
            "ID": r["id"],
            "Scholarship Title": r["title"],
            "Provider": r["provider"],
            "Category": r["source_type"],
            "Confidence": f"{r['confidence_score']}%",
            "Status": r["status"],
            "Deadline": r["deadline"],
            "Official URL": r["official_source_url"]
        })
    
    df = pd.DataFrame(table_data)
    
    st.dataframe(
        df,
        column_config={
            "Official URL": st.column_config.LinkColumn("Official URL"),
            "Confidence": st.column_config.ProgressColumn("Confidence Score", format="%s", min_value=0, max_value=100)
        },
        use_container_width=True,
        hide_index=True
    )

st.divider()

# Detailed Inspection & Audit Trail
st.subheader("🔍 Deep Inspection & Verification Audit Trail")

if filtered:
    selected_title = st.selectbox(
        "Select a scholarship to inspect evidence, verification details, and version history:",
        [r["title"] for r in filtered]
    )
    
    selected_record = next(r for r in filtered if r["title"] == selected_title)
    
    col_a, col_b = st.columns([2, 1])
    
    with col_a:
        st.markdown(f"### {selected_record['title']}")
        st.write(f"**Provider:** {selected_record['provider']}")
        st.write(f"**Category:** {selected_record['source_type']}")
        st.write(f"**Education Level:** {selected_record['education_level']}")
        st.write(f"**Financial Benefit / Amount:** {selected_record['amount']}")
        st.write(f"**Eligibility Criteria:** {selected_record['eligibility']}")
        st.write(f"**Application Deadline:** {selected_record['deadline']}")
        st.write(f"**Official Source URL:** [{selected_record['official_source_url']}]({selected_record['official_source_url']})")
        st.write(f"**Application URL:** [{selected_record['application_url']}]({selected_record['application_url']})")

    with col_b:
        st.markdown("### Confidence & Status")
        st.metric(label="Calculated Confidence Score", value=f"{selected_record['confidence_score']}%")
        st.progress(selected_record['confidence_score'] / 100.0)
        
        status_val = selected_record['status']
        if status_val == "VERIFIED":
            st.success("✅ VERIFIED (Confidence >= 95%)")
        elif status_val == "REVIEW_REQUIRED":
            st.warning("⚠️ REVIEW REQUIRED (Confidence < 95%)")
        elif status_val == "EXPIRED":
            st.error("🚫 EXPIRED / CLOSED")
        else:
            st.info("ℹ️ STALE / UNREACHABLE")

        st.caption(f"Last Verified: {selected_record['last_verified_at']}")

    # Tabs for Audit Details
    tab1, tab2 = st.tabs(["📋 Verification Audit Evidence JSON", "📜 Change History Timeline"])
    
    with tab1:
        st.json(selected_record["verification_evidence"])
        
    with tab2:
        history = get_scholarship_history(selected_record["id"])
        if not history:
            st.info("No field updates recorded yet.")
        else:
            h_df = pd.DataFrame(history)
            st.dataframe(h_df[["changed_at", "change_type", "field_name", "old_value", "new_value"]], use_container_width=True)
