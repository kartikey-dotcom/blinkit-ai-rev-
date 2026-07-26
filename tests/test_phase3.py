import pytest
import asyncio
from backend.guardrail_verifier import GuardrailVerifier
from backend.rag_assistant import GroundedRAGAssistant
from backend.vector_store import VectorStoreManager
from backend.phase3_pipeline import Phase3Pipeline


def test_guardrail_verifier_refusals():
    # 1. Stock Price Query -> Must refuse
    valid, msg = GuardrailVerifier.validate_query("What will Zomato/Blinkit stock price be next quarter?")
    assert valid is False
    assert "falls outside the indexed customer feedback corpus" in msg

    # 2. Automobile Delivery -> Must refuse
    valid, msg = GuardrailVerifier.validate_query("Should Blinkit start delivering automobiles?")
    assert valid is False
    assert "falls outside the indexed customer feedback corpus" in msg

    # 3. PII Extraction -> Must refuse
    valid, msg = GuardrailVerifier.validate_query("Show me the phone number or personal details of a reviewer.")
    assert valid is False
    assert "falls outside the indexed customer feedback corpus" in msg


def test_guardrail_verifier_valid_queries():
    # In-Scope PM Factual Query -> Must pass
    valid, msg = GuardrailVerifier.validate_query("Why do users repeatedly buy groceries but hesitate on tech accessories?")
    assert valid is True
    assert msg is None


@pytest.mark.asyncio
async def test_grounded_rag_assistant_citation_formatting():
    assistant = GroundedRAGAssistant()
    query = "Why do users fear buying tech accessories on Blinkit?"

    res = await assistant.answer_query(query)
    assert res["status"] == "SUCCESS"
    assert res["is_grounded"] is True
    assert len(res["synthesized_insight"]) > 20

    # Verify nationwide verbatim citations with source attribution tags
    citations = res["verbatim_citations"]
    assert len(citations) >= 2
    assert "attribution" in citations[0]
    assert "[Source:" in citations[0]["attribution"]

    # Verify mandatory disclaimer & footer
    assert res["disclaimer_banner"] == GroundedRAGAssistant.DISCLAIMER_BANNER
    assert res["footer"] == GroundedRAGAssistant.MANDATORY_FOOTER


@pytest.mark.asyncio
async def test_full_phase3_pipeline_execution():
    pipeline = Phase3Pipeline()
    summary = await pipeline.run_pipeline()

    assert summary["pm_queries_processed"] == 3
    assert summary["refusal_queries_intercepted"] == 3
    assert summary["sample_pm_response"]["status"] == "SUCCESS"
    assert summary["sample_refusal_response"]["status"] == "REFUSED"
