import asyncio
from typing import List, Dict, Any, Tuple
from backend.config import COSINE_SIMILARITY_THRESHOLD
from backend.models import SanitizedReviewEntry, TextChunkEntry
from backend.database import DatabaseManager
from backend.gemini_absa_engine import GeminiABSAEngine
from backend.embedding_service import VectorEmbeddingService
from backend.vector_store import VectorStoreManager, VectorSearchResult


class Phase2Pipeline:
    """Orchestrator for Phase 2 Vector Embedding Indexing, ABSA & Vector Store Setup."""

    def __init__(self, db_manager: DatabaseManager = None, vector_store: VectorStoreManager = None):
        self.db_manager = db_manager or DatabaseManager()
        self.vector_store = vector_store or VectorStoreManager()
        self.absa_engine = GeminiABSAEngine()
        self.embedding_service = VectorEmbeddingService()

    async def run_pipeline(self) -> Dict[str, Any]:
        """Executes Phase 2 Vector Embedding & ABSA Indexing Pipeline."""
        print("[*] Starting Phase 2 Vector Embedding & ABSA Pipeline...")

        # 1. Fetch normalized reviews and text chunks from SQLite
        sanitized_entries = self.db_manager.get_all_sanitized_reviews()
        chunks = self.db_manager.get_all_chunks()

        if not sanitized_entries or not chunks:
            print("[!] Warning: No sanitized reviews or chunks found. Please run Phase 1 pipeline first.")
            return {}

        print(f"   - Loaded {len(sanitized_entries)} sanitized reviews and {len(chunks)} text chunks.")

        # 2. Run ABSA & Friction analysis in batches of 10
        absa_results = []
        batch_size = 10
        for i in range(0, len(sanitized_entries), batch_size):
            batch = sanitized_entries[i:i + batch_size]
            res = await self.absa_engine.analyze_batch(batch)
            absa_results.extend(res)

        # 3. Generate Vector Embeddings (1536-dim) in batches
        vector_tuples: List[Tuple[TextChunkEntry, List[float]]] = []
        for i in range(0, len(chunks), batch_size):
            chunk_batch = chunks[i:i + batch_size]
            embedded_pairs = await self.embedding_service.embed_batch(chunk_batch)
            vector_tuples.extend(embedded_pairs)

        # 4. Save vectors to Vector Store Database & load in-memory cache
        self.vector_store.save_vectors(vector_tuples)
        chunks_dict = {c.chunk_id: c for c in chunks}
        self.vector_store.load_index_into_memory(chunks_dict)

        # 5. Run Verification Sample Vector Queries (Cosine Score >= 0.75)
        test_queries = [
            "Why do users fear buying tech accessories on Blinkit?",
            "What are top complaints about skincare products?",
            "What drives daily grocery reorders?",
        ]

        verification_results = {}
        for q in test_queries:
            q_vec = self.embedding_service.embed_text_query(q)
            matches = self.vector_store.search_similar(q_vec, top_k=2, threshold=0.75)
            verification_results[q] = [m.to_dict() for m in matches]

        summary = {
            "total_reviews_analyzed": len(absa_results),
            "total_chunks_embedded": len(vector_tuples),
            "embedding_model": "text-embedding-3-small",
            "embedding_dimensions": 1536,
            "cosine_threshold": COSINE_SIMILARITY_THRESHOLD,
            "verification_sample_matches": verification_results,
        }

        print("[+] Phase 2 Pipeline Completed Successfully!")
        print(f"   - ABSA Reviews Analyzed: {summary['total_reviews_analyzed']}")
        print(f"   - Vector Chunks Embedded: {summary['total_chunks_embedded']}")
        print(f"   - Embedding Model: {summary['embedding_model']} ({summary['embedding_dimensions']} dims)")
        print(f"   - Cosine Similarity Threshold: {summary['cosine_threshold']}")

        return summary


if __name__ == "__main__":
    pipeline = Phase2Pipeline()
    asyncio.run(pipeline.run_pipeline())
