import sqlite3
import json
from typing import List, Dict, Any, Optional
from pathlib import Path
from backend.config import DB_PATH, CACHE_PATH
from backend.models import RawReviewEntry, SanitizedReviewEntry, TextChunkEntry


class DatabaseManager:
    """SQLite Database Manager & Cache Storage Engine for Blinkit AI Reviews."""

    def __init__(self, db_path: Path = DB_PATH, cache_path: Path = CACHE_PATH):
        self.db_path = db_path
        self.cache_path = cache_path
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        try:
            conn = sqlite3.connect(self.db_path, timeout=30.0, check_same_thread=False)
            conn.row_factory = sqlite3.Row
            return conn
        except (sqlite3.DatabaseError, sqlite3.OperationalError):
            if self.db_path.exists():
                try:
                    self.db_path.unlink()
                except Exception:
                    pass
            conn = sqlite3.connect(self.db_path, timeout=30.0, check_same_thread=False)
            conn.row_factory = sqlite3.Row
            return conn

    def _init_db(self):
        """Creates SQLite tables if they do not exist."""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()

                # Raw Reviews Table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS raw_reviews (
                        review_id TEXT PRIMARY KEY,
                        app_package TEXT,
                        author_name TEXT,
                        rating INTEGER,
                        title TEXT,
                        raw_text TEXT,
                        timestamp TEXT,
                        source_channel TEXT,
                        community_tag TEXT,
                        thumbs_up_count INTEGER,
                        product_category TEXT
                    )
                """)

                # Sanitized Reviews Table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS sanitized_reviews (
                        review_id TEXT PRIMARY KEY,
                        app_package TEXT,
                        rating INTEGER,
                        sanitized_text TEXT,
                        word_count INTEGER,
                        has_pii_redacted BOOLEAN,
                        timestamp TEXT,
                        source_channel TEXT,
                        community_tag TEXT,
                        thumbs_up_count INTEGER,
                        product_category TEXT
                    )
                """)

                # Text Chunks Table (500 tokens / 50 overlap)
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS text_chunks (
                        chunk_id TEXT PRIMARY KEY,
                        review_id TEXT,
                        chunk_index INTEGER,
                        total_chunks INTEGER,
                        chunk_text TEXT,
                        token_count INTEGER,
                        source_channel TEXT,
                        star_rating INTEGER,
                        community_tag TEXT,
                        attribution_tag TEXT,
                        product_category TEXT,
                        FOREIGN KEY (review_id) REFERENCES sanitized_reviews (review_id)
                    )
                """)
                conn.commit()
        except sqlite3.Error:
            pass

    def save_raw_reviews(self, raw_entries: List[RawReviewEntry]):
        """Persists raw reviews to SQLite."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            for r in raw_entries:
                cursor.execute("""
                    INSERT OR REPLACE INTO raw_reviews 
                    (review_id, app_package, author_name, rating, title, raw_text, timestamp, source_channel, community_tag, thumbs_up_count, product_category)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    r.review_id, r.app_package, r.author_name, r.rating, r.title,
                    r.raw_text, r.timestamp.isoformat(), r.source_channel,
                    r.community_tag, r.thumbs_up_count, r.product_category
                ))
            conn.commit()

    def save_sanitized_reviews(self, sanitized_entries: List[SanitizedReviewEntry]):
        """Persists normalized sanitized reviews to SQLite."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            for s in sanitized_entries:
                cursor.execute("""
                    INSERT OR REPLACE INTO sanitized_reviews
                    (review_id, app_package, rating, sanitized_text, word_count, has_pii_redacted, timestamp, source_channel, community_tag, thumbs_up_count, product_category)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    s.review_id, s.app_package, s.rating, s.sanitized_text,
                    s.word_count, s.has_pii_redacted, s.timestamp.isoformat(),
                    s.source_channel, s.community_tag, s.thumbs_up_count, s.product_category
                ))
            conn.commit()

    def save_text_chunks(self, chunks: List[TextChunkEntry]):
        """Persists text chunks to SQLite."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            for c in chunks:
                cursor.execute("""
                    INSERT OR REPLACE INTO text_chunks
                    (chunk_id, review_id, chunk_index, total_chunks, chunk_text, token_count, source_channel, star_rating, community_tag, attribution_tag, product_category)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    c.chunk_id, c.review_id, c.chunk_index, c.total_chunks,
                    c.chunk_text, c.token_count, c.source_channel, c.star_rating,
                    c.community_tag, c.attribution_tag, c.product_category
                ))
            conn.commit()

    def get_all_sanitized_reviews(self) -> List[SanitizedReviewEntry]:
        """Retrieves all sanitized reviews from SQLite."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM sanitized_reviews")
            rows = cursor.fetchall()
            entries = []
            for r in rows:
                entries.append(
                    SanitizedReviewEntry(
                        review_id=r["review_id"],
                        app_package=r["app_package"],
                        rating=r["rating"],
                        sanitized_text=r["sanitized_text"],
                        word_count=r["word_count"],
                        has_pii_redacted=bool(r["has_pii_redacted"]),
                        timestamp=r["timestamp"],
                        source_channel=r["source_channel"],
                        community_tag=r["community_tag"],
                        thumbs_up_count=r["thumbs_up_count"],
                        product_category=r["product_category"] or "General",
                    )
                )
            return entries

    def get_all_chunks(self) -> List[TextChunkEntry]:
        """Retrieves all text chunks from SQLite."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM text_chunks")
            rows = cursor.fetchall()
            chunks = []
            for r in rows:
                chunks.append(
                    TextChunkEntry(
                        chunk_id=r["chunk_id"],
                        review_id=r["review_id"],
                        chunk_index=r["chunk_index"],
                        total_chunks=r["total_chunks"],
                        chunk_text=r["chunk_text"],
                        token_count=r["token_count"],
                        source_channel=r["source_channel"],
                        star_rating=r["star_rating"],
                        community_tag=r["community_tag"],
                        attribution_tag=r["attribution_tag"],
                        product_category=r["product_category"] or "General",
                    )
                )
            return chunks

    def save_cache_json(self, sanitized_entries: List[SanitizedReviewEntry], chunks: List[TextChunkEntry]):
        """Saves reviews and chunks to JSON cache file (`reviews_cache.json`)."""
        cache_data = {
            "metadata": {
                "app_package": "com.grofers.inkart",
                "app_name": "Blinkit",
                "total_reviews": len(sanitized_entries),
                "total_chunks": len(chunks),
            },
            "reviews": [s.model_dump(mode="json") for s in sanitized_entries],
            "chunks": [c.model_dump(mode="json") for c in chunks],
        }
        with open(self.cache_path, "w", encoding="utf-8") as f:
            json.dump(cache_data, f, indent=2, default=str)
