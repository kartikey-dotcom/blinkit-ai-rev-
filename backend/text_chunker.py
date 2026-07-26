import math
from typing import List
from backend.config import CHUNK_SIZE_TOKENS, CHUNK_OVERLAP_TOKENS
from backend.models import SanitizedReviewEntry, TextChunkEntry


class TextChunker:
    """Pre-processor engine that splits text into 500-token chunks with 50-token sliding window overlap."""

    # Approximate 1 token = ~0.75 words, or ~1.33 tokens per word
    WORDS_PER_TOKEN = 0.75

    @classmethod
    def estimate_token_count(cls, text: str) -> int:
        """Estimate token count for text using standard word/character heuristics."""
        words = text.split()
        return max(1, int(len(words) / cls.WORDS_PER_TOKEN))

    @classmethod
    def generate_attribution_tag(cls, source_channel: str, rating: int, community_tag: str = None) -> str:
        """Generate structured metadata attribution tag for citation matching."""
        if "Reddit" in source_channel or community_tag:
            tag = community_tag or source_channel
            return f"[Source: {tag}]"
        else:
            channel_name = "Play Store" if "Play" in source_channel else "App Store"
            return f"[Source: {channel_name} | {rating}-Star Review]"

    @classmethod
    def chunk_review(cls, entry: SanitizedReviewEntry) -> List[TextChunkEntry]:
        """
        Splits a sanitized review entry into 500-token chunks with 50-token overlap.
        For reviews under 500 tokens, creates a single chunk.
        """
        words = entry.sanitized_text.split()
        total_tokens = cls.estimate_token_count(entry.sanitized_text)

        target_words_per_chunk = int(CHUNK_SIZE_TOKENS * cls.WORDS_PER_TOKEN) # ~375 words
        overlap_words = int(CHUNK_OVERLAP_TOKENS * cls.WORDS_PER_TOKEN) # ~37 words

        attribution_tag = cls.generate_attribution_tag(
            entry.source_channel, entry.rating, entry.community_tag
        )

        if len(words) <= target_words_per_chunk:
            # Single chunk case
            chunk_entry = TextChunkEntry(
                chunk_id=f"{entry.review_id}_chunk_0",
                review_id=entry.review_id,
                chunk_index=0,
                total_chunks=1,
                chunk_text=entry.sanitized_text,
                token_count=total_tokens,
                source_channel=entry.source_channel,
                star_rating=entry.rating,
                community_tag=entry.community_tag,
                attribution_tag=attribution_tag,
                product_category=entry.product_category,
            )
            return [chunk_entry]

        # Multi-chunk sliding window
        chunks: List[TextChunkEntry] = []
        step = target_words_per_chunk - overlap_words
        start = 0
        chunk_idx = 0

        while start < len(words):
            end = min(start + target_words_per_chunk, len(words))
            chunk_words = words[start:end]
            chunk_text = " ".join(chunk_words)

            chunks.append(
                TextChunkEntry(
                    chunk_id=f"{entry.review_id}_chunk_{chunk_idx}",
                    review_id=entry.review_id,
                    chunk_index=chunk_idx,
                    total_chunks=0,  # Updated below
                    chunk_text=chunk_text,
                    token_count=cls.estimate_token_count(chunk_text),
                    source_channel=entry.source_channel,
                    star_rating=entry.rating,
                    community_tag=entry.community_tag,
                    attribution_tag=attribution_tag,
                    product_category=entry.product_category,
                )
            )

            chunk_idx += 1
            start += step

        # Update total_chunks count for all generated chunks
        total_generated = len(chunks)
        for c in chunks:
            c.total_chunks = total_generated

        return chunks
