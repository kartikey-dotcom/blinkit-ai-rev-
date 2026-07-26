import asyncio
import streamlit as st
import pandas as pd
import plotly.express as px
from backend.config import APP_NAME, TARGET_ORGANIZATION
from backend.customer_discovery_engine import CustomerDiscoveryEngine
from backend.rag_assistant import GroundedRAGAssistant
from backend.database import DatabaseManager

# Page Configuration
st.set_page_config(
    page_title="Blinkit AI Reviews — Grounded RAG Discovery Engine",
    page_icon="🛒",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for Blinkit Brand Theme (#FFE141 & #0C831F)
st.markdown("""
    <style>
    .main-header {
        background-color: #FFE141;
        padding: 24px 30px;
        border-radius: 16px;
        color: #000000;
        text-align: center;
        margin-bottom: 25px;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
    }
    .main-header h1 {
        color: #000000;
        font-weight: 900;
        font-size: 32px;
        margin: 10px 0 6px 0;
        letter-spacing: -0.5px;
    }
    .main-header p {
        color: #121212;
        font-size: 15px;
        font-weight: 600;
        margin: 0;
    }
    .blink-green {
        color: #0C831F;
        font-weight: 900;
    }
    .blink-black {
        color: #000000;
        font-weight: 900;
    }
    .disclaimer-banner {
        background-color: #FFFDE7;
        border-left: 6px solid #0C831F;
        padding: 14px 18px;
        border-radius: 8px;
        color: #1B5E20;
        font-weight: 600;
        font-size: 14px;
        margin-bottom: 20px;
    }
    .footer-stamp {
        background-color: #ECEFF1;
        border-top: 2px solid #CFD8DC;
        padding: 10px;
        border-radius: 6px;
        text-align: center;
        font-size: 13px;
        color: #455A64;
        font-weight: 600;
        margin-top: 20px;
    }
    .kpi-card {
        background-color: #FFFFFF;
        padding: 18px;
        border-radius: 10px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.05);
        border-top: 4px solid #FFE141;
        text-align: center;
    }
    .kpi-card h3 {
        color: #666;
        font-size: 14px;
        margin-bottom: 5px;
    }
    .kpi-card h2 {
        color: #000000;
        font-size: 28px;
        font-weight: 700;
        margin: 0;
    }
    </style>
""", unsafe_allow_html=True)

import base64
from pathlib import Path

# Load Blinkit Logo Image Asset
logo_path = Path(__file__).parent / "assets" / "blinkit_logo.png"
if logo_path.exists():
    logo_b64 = base64.b64encode(logo_path.read_bytes()).decode("utf-8")
    logo_img_html = f'<img src="data:image/png;base64,{logo_b64}" style="height: 85px; margin-bottom: 6px;" alt="Blinkit Logo"><br>'
else:
    logo_img_html = ""

# Main Header Banner
st.markdown(f"""
    <div class="main-header">
        {logo_img_html}
        <h1><span class="blink-black">blink</span><span class="blink-green">it</span> <span style="color:#000000; font-weight:800;">AI Reviews — Grounded RAG Discovery Engine</span></h1>
        <p>Multi-Channel Customer Feedback Intelligence & Cross-Category Habit Analysis | {TARGET_ORGANIZATION}</p>
    </div>
""", unsafe_allow_html=True)

# Navigation Tabs
tab1, tab2 = st.tabs(["📊 Executive Discovery Matrix", "🔍 Ask Blinkit AI (Grounded RAG)"])

# Initialize RAG Assistant Engine
@st.cache_resource
def get_rag_assistant():
    return GroundedRAGAssistant()

rag_assistant = get_rag_assistant()

# ----------------------------------------------------
# TAB 1: EXECUTIVE DISCOVERY MATRIX
# ----------------------------------------------------
with tab1:
    st.subheader("💡 Executive Performance Overview")

    # 4 Executive KPI Containers
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown("""
            <div class="kpi-card">
                <h3>Core Grocery Repetition</h3>
                <h2>81.4%</h2>
                <p style="color:#2E7D32; font-size:12px; margin:0;">Daily Staples Habit Loop</p>
            </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown("""
            <div class="kpi-card">
                <h3>Non-Core Adoption</h3>
                <h2>18.6%</h2>
                <p style="color:#C62828; font-size:12px; margin:0;">Target Goal: > 30.0%</p>
            </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown("""
            <div class="kpi-card">
                <h3>Top Switching Barrier</h3>
                <h2 style="font-size:18px;">Quality Anxiety</h2>
                <p style="color:#C62828; font-size:12px; margin:0;">42.8% of Friction Reviews</p>
            </div>
        """, unsafe_allow_html=True)

    with col4:
        st.markdown("""
            <div class="kpi-card">
                <h3>Corpus Entries Analyzed</h3>
                <h2>5,000</h2>
                <p style="color:#1565C0; font-size:12px; margin:0;">Multi-Channel Feedback</p>
            </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # 8 Core Behavioral Discovery Accordions
    st.subheader("🧩 8 Core Customer Behavioral Discovery Questions")
    
    questions = CustomerDiscoveryEngine.BEHAVIORAL_QUESTIONS
    for q in questions:
        with st.expander(f"Question {q['id']}: {q['question']}"):
            st.markdown(f"**Insight Badge**: <span style='background-color:{q['badge_color']}; color:white; padding:4px 10px; border-radius:12px; font-size:13px;'>{q['percentage_badge']}</span>", unsafe_allow_html=True)
            st.markdown(f"**Synthesized Insight**: {q['insight']}")
            st.markdown(f"**Customer Verbatim Quote**: *{q['verbatim_quote']}* `{q['attribution']}`")
            st.markdown(f"**Recommended PM Action**: `{q['pm_action']}`")

    st.markdown("<br>", unsafe_allow_html=True)

    # Plotly Friction Distribution Chart
    st.subheader("📉 Category Switching Friction Distribution")
    friction_data = CustomerDiscoveryEngine.FRICTION_DISTRIBUTION
    df_friction = pd.DataFrame(friction_data)
    
    fig = px.bar(
        df_friction,
        x="share_pct",
        y="friction_category",
        orientation="h",
        text="share_pct",
        color="share_pct",
        color_continuous_scale="YlOrRd",
        labels={"share_pct": "Share of Reviews (%)", "friction_category": "Friction Category"},
        title="Customer Category Switching Barriers (%)"
    )
    fig.update_traces(texttemplate='%{text:.1f}%', textposition='outside')
    fig.update_layout(height=350, margin=dict(l=0, r=40, t=40, b=0))
    st.plotly_chart(fig, use_container_width=True)

    # Product Category Adoption Matrix Table
    st.subheader("📦 Product Category Adoption Matrix")
    df_adoption = CustomerDiscoveryEngine.get_category_adoption_dataframe()
    st.dataframe(df_adoption, use_container_width=True)

    # 1-Click CSV Exporter
    st.subheader("📥 Export Normalized Customer Feedback Data")
    db_mgr = DatabaseManager()
    sanitized_reviews = db_mgr.get_all_sanitized_reviews()
    if sanitized_reviews:
        df_export = pd.DataFrame([s.model_dump() for s in sanitized_reviews])
        csv_bytes = df_export.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="⬇️ Download blinkit_playstore_reviews.csv",
            data=csv_bytes,
            file_name="blinkit_playstore_reviews.csv",
            mime="text/csv"
        )

# ----------------------------------------------------
# TAB 2: INTERACTIVE ASK BLINKIT AI (GROUNDED RAG)
# ----------------------------------------------------
with tab2:
    st.subheader("🤖 Ask Blinkit AI — Grounded RAG Assistant")

    # Mandatory Disclaimer Banner
    st.markdown(f"""
        <div class="disclaimer-banner">
            ⚠️ <strong>{rag_assistant.DISCLAIMER_BANNER}</strong>
        </div>
    """, unsafe_allow_html=True)

    # Example Prompt Chips
    st.markdown("**Example Prompt Chips (Click to Query):**")
    chip_col1, chip_col2, chip_col3 = st.columns(3)
    
    selected_query = ""
    with chip_col1:
        if st.button("📱 Why do users fear buying tech on Blinkit?"):
            selected_query = "Why do users fear buying tech accessories on Blinkit?"
    with chip_col2:
        if st.button("🧴 What are top complaints about skincare products?"):
            selected_query = "What are top complaints about skincare products on Blinkit?"
    with chip_col3:
        if st.button("🥛 What drives daily grocery reorders?"):
            selected_query = "What drives daily grocery reorders in under 10 minutes?"

    # Query Input Box
    user_query = st.text_input(
        "Enter your strategic PM or user research question:",
        value=selected_query,
        placeholder="e.g. Why do users hesitate to purchase home utility appliances on Blinkit?"
    )

    if st.button("🔍 Execute Grounded RAG Query", type="primary") and user_query:
        with st.spinner("Retrieving vector embeddings (Cosine >= 0.75) and synthesizing grounded insights..."):
            # Execute RAG query asynchronously
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            response = loop.run_until_complete(rag_assistant.answer_query(user_query))

        # Render Response Container
        status = response.get("status")

        if status == "REFUSED":
            st.error(f"⛔ **Query Refused**: {response.get('refusal_message')}")
        elif status == "NO_MATCHES":
            st.warning(f"⚠️ **No Vector Match**: {response.get('synthesized_insight')}")
        elif status == "SUCCESS":
            st.success("✅ **Grounded RAG Response Generated Successfully**")
            
            st.markdown("### 💡 Synthesized Insight (Max 2-3 Sentences)")
            st.info(response.get("synthesized_insight"))

            st.markdown("### 💬 Direct Customer Verbatim Citations (Exactly 2 Quotes)")
            citations = response.get("verbatim_citations", [])
            for idx, c in enumerate(citations, 1):
                st.markdown(f"**Quote {idx}**: {c['quote']}  ")
                st.markdown(f"`{c['attribution']}` *(Cosine Match Score: {c['cosine_score']})*")

            # Mandatory Verification Footer
            st.markdown(f"""
                <div class="footer-stamp">
                    🛡️ {response.get('footer')}
                </div>
            """, unsafe_allow_html=True)
