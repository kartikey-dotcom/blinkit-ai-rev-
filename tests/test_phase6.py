import pytest
import asyncio
from pathlib import Path
from backend.scheduler import ContinuousPipelineScheduler


def test_docker_files_existence():
    root_dir = Path(__file__).parent.parent

    dockerfile = root_dir / "Dockerfile"
    docker_compose = root_dir / "docker-compose.yml"
    docker_ignore = root_dir / ".dockerignore"

    assert dockerfile.exists()
    assert docker_compose.exists()
    assert docker_ignore.exists()

    content_df = dockerfile.read_text(encoding="utf-8")
    assert "FROM python:3.11-slim" in content_df
    assert "EXPOSE 8501" in content_df

    content_dc = docker_compose.read_text(encoding="utf-8")
    assert "blinkit-rag-app" in content_dc
    assert "8501:8501" in content_dc


@pytest.mark.asyncio
async def test_continuous_scheduler_cycle():
    scheduler = ContinuousPipelineScheduler(interval_hours=24.0)
    summary = await scheduler.execute_full_pipeline_cycle()

    assert summary["status"] == "SUCCESS"
    assert "timestamp" in summary
    assert summary["phase1_summary"].get("valid_sanitized", summary["phase1_summary"].get("valid_reviews", 0)) > 0
    assert summary["phase2_summary"]["total_chunks_embedded"] > 0
