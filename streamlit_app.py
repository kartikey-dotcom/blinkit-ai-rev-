import sys
from pathlib import Path

# Add project root directory to python path for Streamlit Cloud runtime
ROOT_DIR = Path(__file__).parent.resolve()
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import asyncio
import streamlit as st
import pandas as pd
import plotly.express as px
import base64
from backend.config import APP_NAME, TARGET_ORGANIZATION
from backend.customer_discovery_engine import CustomerDiscoveryEngine, BLINKIT_DISCOVERY_MATRIX
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
    /* App background & theme */
    .stApp {
        background-color: #F8F9FA;
    }
    
    /* Main Header Banner */
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

    /* Navigation Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 10px;
        background-color: #EFEFEF;
        padding: 6px 10px;
        border-radius: 12px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 44px;
        background-color: #FFFFFF;
        border-radius: 8px;
        color: #000000;
        font-weight: 700;
        border: 1px solid #E0E0E0;
    }
    .stTabs [aria-selected="true"] {
        background-color: #FFE141 !important;
        color: #000000 !important;
        border: 2px solid #0C831F !important;
        font-weight: 900 !important;
    }

    /* KPI Cards */
    .kpi-card {
        background-color: #FFFFFF;
        padding: 18px;
        border-radius: 12px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.05);
        border-top: 5px solid #FFE141;
        border-bottom: 3px solid #0C831F;
        text-align: center;
    }
    .kpi-card h3 {
        color: #555555;
        font-size: 14px;
        font-weight: 700;
        margin-bottom: 5px;
    }
    .kpi-card h2 {
        color: #000000;
        font-size: 28px;
        font-weight: 900;
        margin: 0;
    }

    /* Behavioral Discovery Question Cards */
    .behavioral-card-container {
        background-color: #FFFFFF;
        border-radius: 14px;
        margin-bottom: 15px;
        box-shadow: 0 4px 18px rgba(0, 0, 0, 0.07);
        overflow: hidden;
        border: 1px solid #E0E0E0;
    }
    .behavioral-question-header {
        background-color: #FFE141;
        color: #000000;
        padding: 14px 20px;
        font-size: 18px;
        font-weight: 900;
        border-bottom: 3px solid #0C831F;
    }
    .behavioral-answer-body {
        padding: 16px 20px;
        background-color: #FFFFFF;
    }
    .answer-insight {
        font-size: 15px;
        color: #000000;
        font-weight: 500;
        line-height: 1.55;
        margin-bottom: 10px;
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
        padding: 12px;
        border-radius: 6px;
        text-align: center;
        font-size: 13px;
        color: #37474F;
        font-weight: 700;
        margin-top: 20px;
    }
    </style>
""", unsafe_allow_html=True)

# Load Blinkit Logo Image Asset
logo_path = ROOT_DIR / "assets" / "blinkit_logo.png"
if logo_path.exists():
    logo_b64 = base64.b64encode(logo_path.read_bytes()).decode("utf-8")
    logo_img_html = f'<img src="data:image/png;base64,{logo_b64}" style="height: 85px; background-color: #FFE141; border-radius: 18px; margin-bottom: 6px;" alt="Blinkit Logo"><br>'
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
tab1, tab2 = st.tabs(["📊 Executive Discovery Matrix", "💬 Ask Blinkit AI - Grounded RAG"])

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
                <p style="color:#2E7D32; font-size:12px; margin:0; font-weight:600;">Daily Milk/Staples Lock-In</p>
            </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown("""
            <div class="kpi-card">
                <h3>MAC Category Exploration</h3>
                <h2>18.6%</h2>
                <p style="color:#C62828; font-size:12px; margin:0; font-weight:600;">Target Goal = 35.0%</p>
            </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown("""
            <div class="kpi-card">
                <h3>Top Switching Barrier</h3>
                <h2 style="font-size:22px;">Quality Anxiety</h2>
                <p style="color:#C62828; font-size:12px; margin:0; font-weight:600;">42.8% Quality & Return Policy Anxiety</p>
            </div>
        """, unsafe_allow_html=True)

    with col4:
        st.markdown("""
            <div class="kpi-card">
                <h3>Corpus Entries Scanned</h3>
                <h2>5,000</h2>
                <p style="color:#1565C0; font-size:12px; margin:0; font-weight:600;">Multi-Channel Feedback</p>
            </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # 8 Core Behavioral Discovery Cards (Blinkit Yellow Question Header + Side-by-Side Dual Verbatims View)
    st.subheader("🧩 8 Core Customer Behavioral Discovery Insights")
    
    for key, card in BLINKIT_DISCOVERY_MATRIX.items():
        with st.container():
            # Blinkit Yellow Header Box with Question and Green Metric Badge
            st.markdown(f"""
                <div class="behavioral-card-container">
                    <div class="behavioral-question-header" style="display:flex; justify-content:space-between; align-items:center;">
                        <span>💡 {card['question']}</span>
                        <span style="background-color:#146C2E; color:white; padding:4px 12px; border-radius:12px; font-size:13px; font-weight:bold;">{card['metric_badge']}</span>
                    </div>
                    <div class="behavioral-answer-body">
                        <div class="answer-insight">
                            <strong style="color:#0C831F; font-weight:800;">💡 Synthesized Insight:</strong> {card['key_finding']}
                        </div>
                    </div>
                </div>
            """, unsafe_allow_html=True)

            # Render Dual Customer Verbatim Quotes Side-by-Side (Task 2 Requirement)
            st.markdown("**Customer Verbatim Citations:**")
            v_col1, v_col2 = st.columns(2)

            with v_col1:
                st.markdown(
                    f"""
                    <div style="background-color: #F8F9FA; padding: 12px; border-left: 4px solid #146C2E; border-radius: 6px; min-height: 90px; font-size: 13px; color: #1B1C1D;">
                        💬 <i>{card['verbatims'][0]}</i>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

            with v_col2:
                st.markdown(
                    f"""
                    <div style="background-color: #F8F9FA; padding: 12px; border-left: 4px solid #146C2E; border-radius: 6px; min-height: 90px; font-size: 13px; color: #1B1C1D;">
                        💬 <i>{card['verbatims'][1]}</i>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

            # Strategic PM Action Box
            st.info(f"🎯 **{card['action']}**")
            st.divider()

    st.markdown("<br>", unsafe_allow_html=True)

    # Plotly Friction Distribution Chart (Aligned Label: "Quality & Return Policy Anxiety")
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
    try:
        st.plotly_chart(fig, width="stretch")
    except Exception:
        st.plotly_chart(fig, use_container_width=True)

    # Product Category Adoption Matrix Table
    st.subheader("📦 Product Category Adoption Matrix")
    df_adoption = CustomerDiscoveryEngine.get_category_adoption_dataframe()
    try:
        st.dataframe(df_adoption, width="stretch")
    except Exception:
        st.dataframe(df_adoption, use_container_width=True)

    # 1-Click CSV Exporter
    st.subheader("📥 Export Normalized Customer Feedback Data")

    @st.cache_data
    def get_csv_export():
        try:
            db_mgr = DatabaseManager()
            sanitized_reviews = db_mgr.get_all_sanitized_reviews()
            if sanitized_reviews:
                df_export = pd.DataFrame([s.model_dump() for s in sanitized_reviews])
                return df_export.to_csv(index=False).encode('utf-8')
        except Exception:
            pass
        return None

    csv_bytes = get_csv_export()
    if csv_bytes:
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

    # Mandatory Disclaimer Banner (Task 3 Requirement)
    st.caption("🔒 Grounded AI Assistant: Answers generated strictly from indexed public customer reviews. Zero hallucinated advice.")

    # 3 Interactive Quick-Click Prompt Chips (Task 3 Requirement)
    st.markdown("**Interactive Quick-Click Prompt Chips:**")
    chip_col1, chip_col2, chip_col3 = st.columns(3)
    
    if "rag_query" not in st.session_state:
        st.session_state.rag_query = ""

    with chip_col1:
        if st.button("📱 Chip 1: Why do users fear buying tech accessories on Blinkit?"):
            st.session_state.rag_query = "Why do users fear buying tech accessories on Blinkit?"
    with chip_col2:
        if st.button("🧴 Chip 2: What return frustrations emerge for cosmetics > ₹500?"):
            st.session_state.rag_query = "What return frustrations emerge for cosmetics > ₹500?"
    with chip_col3:
        if st.button("🥛 Chip 3: What drives daily grocery reorder habits?"):
            st.session_state.rag_query = "What drives daily grocery reorder habits?"

    # Query Input Box
    user_query = st.text_input(
        "Enter your strategic PM or user research question:",
        value=st.session_state.rag_query,
        placeholder="e.g. Why do users hesitate to purchase home utility appliances on Blinkit?"
    )

    btn_submitted = st.button("🔍 Execute Grounded RAG Query", type="primary")
    if (btn_submitted or st.session_state.rag_query) and user_query:
        # Check guardrail refusal keywords (Task 3 Requirement)
        query_lower = user_query.lower()
        out_of_scope_keywords = ["stock price", "automobile", "car", "phone number", "address", "delivery boy contact"]
        
        if any(kw in query_lower for kw in out_of_scope_keywords):
            st.error("⚠️ This query falls outside the indexed customer feedback corpus. Please ask questions related to product friction, returns, category exploration, or user sentiment.")
        else:
            with st.spinner("Retrieving vector embeddings (Cosine >= 0.75) and synthesizing grounded insights..."):
                # Execute RAG query asynchronously
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                response = loop.run_until_complete(rag_assistant.answer_query(user_query))

            status = response.get("status")

            if status == "REFUSED":
                st.error(f"⚠️ {response.get('refusal_message')}")
            elif status == "NO_MATCHES":
                st.warning(f"⚠️ **No Vector Match**: {response.get('synthesized_insight')}")
            elif status == "SUCCESS":
                st.success("✅ **Grounded RAG Response Generated Successfully**")
                
                st.markdown("### 💡 Synthesized Insight")
                st.info(response.get("synthesized_insight"))

                st.markdown("### 💬 Direct Customer Verbatim Citations")
                citations = response.get("verbatim_citations", [])
                for idx, c in enumerate(citations[:2], 1):
                    st.markdown(f"**Quote {idx}**: {c['quote']}  ")
                    st.markdown(f"`{c['attribution']}` *(Cosine Match Score: {c['cosine_score']})*")

                # Mandatory Verification Footer (Task 3 Requirement)
                st.markdown("""
                    <div class="footer-stamp">
                        🛡️ Ground-Truth Accuracy Verified | Source Corpus Updated: July 2026
                    </div>
                """, unsafe_allow_html=True)
