import math
import sqlite3
import json
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
from backend.config import DB_PATH, COSINE_SIMILARITY_THRESHOLD, EMBEDDING_DIM
from backend.models import TextChunkEntry


class VectorSearchResult:
    """Represents a vector similarity search result with Cosine match score and metadata tags."""

    def __init__(self, chunk: TextChunkEntry, cosine_similarity: float, vector: List[float] = None):
        self.chunk = chunk
        self.cosine_similarity = cosine_similarity
        self.vector = vector

    def to_dict(self) -> Dict[str, Any]:
        return {
            "chunk_id": self.chunk.chunk_id,
            "review_id": self.chunk.review_id,
            "chunk_text": self.chunk.chunk_text,
            "cosine_similarity": round(self.cosine_similarity, 4),
            "attribution_tag": self.chunk.attribution_tag,
            "source_channel": self.chunk.source_channel,
            "star_rating": self.chunk.star_rating,
            "community_tag": self.chunk.community_tag,
            "product_category": self.chunk.product_category,
        }


class VectorStoreManager:
    """
    Vector Store Database & Search Engine supporting 1536-dim vector indexing 
    and Cosine Similarity Vector Retrieval (threshold >= 0.75).
    """

    def __init__(self, db_path: Path = DB_PATH, min_similarity_threshold: float = COSINE_SIMILARITY_THRESHOLD):
        self.db_path = db_path
        self.min_similarity_threshold = min_similarity_threshold
        self._vector_cache: List[Tuple[TextChunkEntry, List[float]]] = []
        self._init_vector_table()
        if self.db_path.exists():
            self.load_index_into_memory()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_vector_table(self):
        """Initializes the vector embeddings storage table in SQLite."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS vector_embeddings (
                    chunk_id TEXT PRIMARY KEY,
                    review_id TEXT,
                    embedding_json TEXT,
                    attribution_tag TEXT,
                    source_channel TEXT,
                    star_rating INTEGER,
                    product_category TEXT,
                    FOREIGN KEY (chunk_id) REFERENCES text_chunks (chunk_id)
                )
            """)
            conn.commit()

    @classmethod
    def cosine_similarity(cls, vec_a: List[float], vec_b: List[float]) -> float:
        """Computes Cosine Similarity dot product between two normalized 1536-dim vectors."""
        if len(vec_a) != len(vec_b):
            return 0.0
        return sum(a * b for a, b in zip(vec_a, vec_b))

    def save_vectors(self, embeddings_list: List[Tuple[TextChunkEntry, List[float]]]):
        """Persists vector embeddings to SQLite database and in-memory search cache."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            for chunk, vector in embeddings_list:
                vector_json = json.dumps(vector)
                cursor.execute("""
                    INSERT OR REPLACE INTO vector_embeddings
                    (chunk_id, review_id, embedding_json, attribution_tag, source_channel, star_rating, product_category)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    chunk.chunk_id, chunk.review_id, vector_json,
                    chunk.attribution_tag, chunk.source_channel,
                    chunk.star_rating, chunk.product_category
                ))

                # Update in-memory cache
                self._vector_cache.append((chunk, vector))

            conn.commit()

    def load_index_into_memory(self, chunks_dict: Optional[Dict[str, TextChunkEntry]] = None):
        """Loads all vector embeddings from SQLite into in-memory search cache for fast retrieval."""
        self._vector_cache.clear()
        
        # If chunks_dict is not passed, load from database text_chunks table directly
        if chunks_dict is None:
            from backend.database import DatabaseManager
            db_mgr = DatabaseManager(db_path=self.db_path)
            chunks = db_mgr.get_all_chunks()
            chunks_dict = {c.chunk_id: c for c in chunks}

        if not chunks_dict:
            return

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT chunk_id, embedding_json FROM vector_embeddings")
            rows = cursor.fetchall()
            for r in rows:
                chunk_id = r["chunk_id"]
                if chunk_id in chunks_dict:
                    chunk = chunks_dict[chunk_id]
                    vector = json.loads(r["embedding_json"])
                    self._vector_cache.append((chunk, vector))

    def search_similar(
        self,
        query_vector: List[float],
        top_k: int = 5,
        threshold: Optional[float] = None,
        filter_category: Optional[str] = None,
        filter_rating: Optional[int] = None,
    ) -> List[VectorSearchResult]:
        """
        Executes Cosine Similarity search over indexed vector chunks.
        Enforces min similarity threshold (default Cosine Score >= 0.75).
        """
        if not self._vector_cache and self.db_path.exists():
            self.load_index_into_memory()

        min_score = threshold if threshold is not None else self.min_similarity_threshold
        matched_results: List[VectorSearchResult] = []

        for chunk, vector in self._vector_cache:
            # Apply metadata filters if specified
            if filter_category and chunk.product_category != filter_category:
                continue
            if filter_rating and chunk.star_rating != filter_rating:
                continue

            score = self.cosine_similarity(query_vector, vector)

            if score >= min_score:
                matched_results.append(VectorSearchResult(chunk=chunk, cosine_similarity=score, vector=vector))

        # Sort by Cosine similarity descending
        matched_results.sort(key=lambda r: r.cosine_similarity, reverse=True)

        return matched_results[:top_k]
