from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class RawReviewEntry(BaseModel):
    """Raw scraped/ingested customer feedback entry before PII sanitization."""
    review_id: str
    app_package: str = "com.grofers.inkart"
    author_name: Optional[str] = None
    rating: int = Field(..., ge=1, le=5)
    title: Optional[str] = None
    raw_text: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    source_channel: str
    community_tag: Optional[str] = None
    thumbs_up_count: int = 0
    product_category: Optional[str] = "General"


class SanitizedReviewEntry(BaseModel):
    """Normalized, PII-scrubbed customer feedback entry ready for embedding & storage."""
    review_id: str
    app_package: str = "com.grofers.inkart"
    rating: int
    sanitized_text: str
    word_count: int
    has_pii_redacted: bool
    timestamp: datetime
    source_channel: str
    community_tag: Optional[str] = None
    thumbs_up_count: int = 0
    product_category: str = "General"
    is_valid_latin: bool = True


class TextChunkEntry(BaseModel):
    """500-token chunk with sliding window overlap and metadata attribution."""
    chunk_id: str
    review_id: str
    chunk_index: int
    total_chunks: int
    chunk_text: str
    token_count: int
    source_channel: str
    star_rating: int
    community_tag: Optional[str] = None
    attribution_tag: str
    product_category: str = "General"


class IngestionSummary(BaseModel):
    """Summary metrics for Phase 1 ingestion, sanitization, and chunking pipeline."""
    total_raw_ingested: int
    total_sanitized_valid: int
    total_rejected_short_or_emoji: int
    total_pii_redacted: int
    total_chunks_created: int
    channel_breakdown: Dict[str, int]
