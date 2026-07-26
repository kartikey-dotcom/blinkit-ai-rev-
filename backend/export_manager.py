from pathlib import Path
from typing import List
from backend.config import ACTUAL_REVIEWS_TXT, FINALIZED_REVIEWS_TXT
from backend.models import RawReviewEntry, SanitizedReviewEntry


class ExportManager:
    """Manages file exports for actual_reviews.txt and finalized_reviews.txt containing ONLY review text."""

    @classmethod
    def export_actual_reviews(cls, raw_entries: List[RawReviewEntry], file_path: Path = ACTUAL_REVIEWS_TXT):
        """Exports raw review text corpus (ONLY review text, 1 review per line, no review_id or userName)."""
        with open(file_path, "w", encoding="utf-8") as f:
            for entry in raw_entries:
                text_content = entry.raw_text
                if entry.title:
                    text_content = f"{entry.title}. {text_content}"
                clean_line = text_content.replace("\r", " ").replace("\n", " ").strip()
                if clean_line:
                    f.write(f"{clean_line}\n")

    @classmethod
    def export_finalized_reviews(cls, sanitized_entries: List[SanitizedReviewEntry], file_path: Path = FINALIZED_REVIEWS_TXT):
        """Exports finalized normalized review text corpus (ONLY review text, 1 review per line, no review_id or userName)."""
        with open(file_path, "w", encoding="utf-8") as f:
            for entry in sanitized_entries:
                clean_line = entry.sanitized_text.replace("\r", " ").replace("\n", " ").strip()
                if clean_line:
                    f.write(f"{clean_line}\n")
