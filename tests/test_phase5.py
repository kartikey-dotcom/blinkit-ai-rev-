import pytest
import asyncio
from backend.audit_alignment import AuditAlignmentEvaluator
from backend.rag_performance import RAGPerformanceProfiler
from backend.phase5_pipeline import Phase5Pipeline


def test_audit_alignment_evaluation():
    metrics = AuditAlignmentEvaluator.evaluate_audit_alignment()
    assert metrics["total_benchmark_samples"] == 10
    assert metrics["classification_accuracy_pct"] >= 90.0
    assert metrics["is_target_met"] is True


@pytest.mark.asyncio
async def test_rag_performance_profiler():
    profiler = RAGPerformanceProfiler()
    res = await profiler.profile_rag_query("Why do users fear buying tech accessories on Blinkit?")

    assert res["status"] == "SUCCESS"
    assert res["latency_seconds"] < 2.5
    assert res["latency_sla_met"] is True
    assert res["has_two_citations"] is True
    assert res["has_source_tags"] is True
    assert res["has_valid_footer"] is True
    assert res["has_valid_banner"] is True
    assert res["hallucination_rate_pct"] == 0.0


@pytest.mark.asyncio
async def test_full_phase5_pipeline_execution():
    pipeline = Phase5Pipeline()
    summary = await pipeline.run_pipeline()

    assert summary["is_phase5_passed"] is True
    assert summary["audit_alignment_metrics"]["classification_accuracy_pct"] >= 90.0
    assert summary["rag_performance_metrics"]["zero_hallucinations_verified"] is True
