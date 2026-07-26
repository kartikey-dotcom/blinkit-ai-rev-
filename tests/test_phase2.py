import pytest
import asyncio
import math
from datetime import datetime
from backend.models import SanitizedReviewEntry, TextChunkEntry
from backend.gemini_absa_engine import GeminiABSAEngine
from backend.embedding_service import VectorEmbeddingService
from backend.vector_store import VectorStoreManager, VectorSearchResult
from backend.phase2_pipeline import Phase2Pipeline


def test_gemini_absa_classification():
    # 1. Tech Accessories Friction
    tech_text = "Received a Type-C fast charger box with zero brand seal, stopped working after 2 hours. No return option."
    res_tech = GeminiABSAEngine.classify_review(tech_text, rating=1, product_category="Tech Accessories")
    assert res_tech["friction_category"] == "Quality & Spoilage Anxiety" or "Return" in res_tech["friction_category"]
    assert res_tech["is_critical"] is True
    assert res_tech["sentiment_score"] < 0

    # 2. Core Grocery Reorder Loyalty
    grocery_text = "Fresh Amul milk, brown bread, and onions delivered in under 10 minutes every single morning."
    res_grocery = GeminiABSAEngine.classify_review(grocery_text, rating=5, product_category="Core Grocery")
    assert res_grocery["friction_category"] == "Habitual Emergency Reorder Mental Model"
    assert res_grocery["sentiment_score"] > 0.5


@pytest.mark.asyncio
async def test_vector_embedding_service():
    service = VectorEmbeddingService()
    text = "Blinkit fast delivery for daily groceries and tech accessories."
    vector = service._generate_deterministic_vector(text)

    # 1. Verify 1536 dimensions
    assert len(vector) == 1536

    # 2. Verify L2 normalization (magnitude = 1.0)
    magnitude = math.sqrt(sum(v * v for v in vector))
    assert abs(magnitude - 1.0) < 1e-5


def test_vector_store_cosine_similarity(tmp_path):
    test_db = tmp_path / "vector_test.db"
    store = VectorStoreManager(db_path=test_db, min_similarity_threshold=0.75)

    service = VectorEmbeddingService()
    chunk1 = TextChunkEntry(
        chunk_id="C1",
        review_id="R1",
        chunk_index=0,
        total_chunks=1,
        chunk_text="Why do people buy electronics on Blinkit? Type-C fast charger stopped working after 2 hours.",
        token_count=100,
        source_channel="Reddit r/IndiaTech",
        star_rating=1,
        attribution_tag="[Source: r/IndiaTech]",
        product_category="Tech Accessories"
    )

    vector1 = service._generate_deterministic_vector(chunk1.chunk_text)
    store.save_vectors([(chunk1, vector1)])

    # Search with identical query -> Cosine score = 1.0 >= 0.75
    query_vec = service.embed_text_query("Why do people buy electronics on Blinkit Type-C fast charger?")
    matches = store.search_similar(query_vec, top_k=1, threshold=0.75)

    assert len(matches) == 1
    assert matches[0].cosine_similarity >= 0.75
    assert matches[0].chunk.chunk_id == "C1"


@pytest.mark.asyncio
async def test_full_phase2_pipeline_execution():
    pipeline = Phase2Pipeline()
    summary = await pipeline.run_pipeline()

    assert summary["total_reviews_analyzed"] > 0
    assert summary["total_chunks_embedded"] > 0
    assert summary["embedding_dimensions"] == 1536
    assert summary["cosine_threshold"] == 0.75
