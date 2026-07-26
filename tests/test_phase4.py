import pytest
import pandas as pd
from backend.customer_discovery_engine import CustomerDiscoveryEngine
from backend.rag_assistant import GroundedRAGAssistant


def test_customer_discovery_engine_kpi_metrics():
    metrics = CustomerDiscoveryEngine.KPI_METRICS
    assert metrics["core_repetition_rate"] == "81.4%"
    assert metrics["non_core_adoption_rate"] == "18.6%"
    assert metrics["total_reviews_analyzed"] == 5000

    questions = CustomerDiscoveryEngine.BEHAVIORAL_QUESTIONS
    assert len(questions) == 8
    assert questions[0]["id"] == 1
    assert "reorder" in questions[0]["percentage_badge"].lower()


def test_category_adoption_dataframe():
    df = CustomerDiscoveryEngine.get_category_adoption_dataframe()
    assert isinstance(df, pd.DataFrame)
    assert len(df) == 6
    assert "Category" in df.columns
    assert "Review Count" in df.columns
    assert "Core Grocery & Dairy" in df["Category"].values


def test_rag_assistant_disclaimer_and_footer():
    assistant = GroundedRAGAssistant()
    assert "Grounded AI Assistant:" in assistant.DISCLAIMER_BANNER
    assert "Ground-Truth Accuracy Verified" in assistant.MANDATORY_FOOTER
