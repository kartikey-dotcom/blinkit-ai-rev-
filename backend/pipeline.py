from typing import List, Tuple
from backend.config import TARGET_CORPUS_COUNT
from backend.models import RawReviewEntry, SanitizedReviewEntry, TextChunkEntry, IngestionSummary
from backend.pii_normalizer import PIINormalizer
from backend.ingestion_connector import MultiChannelIngestionConnector
from backend.text_chunker import TextChunker
from backend.database import DatabaseManager
from backend.export_manager import ExportManager


class Phase1Pipeline:
    """Orchestrator for Phase 1 Ingestion, Zero-Trust PII Masking, Chunking & Data Persistence."""

    def __init__(self, db_manager: DatabaseManager = None):
        self.db_manager = db_manager or DatabaseManager()

    def run_pipeline(self, target_count: int = TARGET_CORPUS_COUNT) -> Tuple[IngestionSummary, List[SanitizedReviewEntry], List[TextChunkEntry]]:
        """Executes the complete Phase 1 data pipeline."""
        print(f"[*] Starting Phase 1 Ingestion for Blinkit (com.grofers.inkart) - Target: {target_count} entries...")

        # 1. Fetch raw multi-channel feedback entries
        raw_entries: List[RawReviewEntry] = MultiChannelIngestionConnector.generate_corpus(target_count)

        sanitized_entries: List[SanitizedReviewEntry] = []
        all_chunks: List[TextChunkEntry] = []

        total_pii_count = 0
        total_rejected_count = 0
        channel_breakdown = {}

        # 2. Process & Sanitize raw entries
        for raw in raw_entries:
            channel_name = raw.source_channel
            channel_breakdown[channel_name] = channel_breakdown.get(channel_name, 0) + 1

            sanitized_entry, status = PIINormalizer.sanitize(raw)
            if sanitized_entry is None:
                total_rejected_count += 1
                continue

            if sanitized_entry.has_pii_redacted:
                total_pii_count += 1

            sanitized_entries.append(sanitized_entry)

            # 3. Chunk text into 500-token chunks with 50-token overlap
            chunks = TextChunker.chunk_review(sanitized_entry)
            all_chunks.extend(chunks)

        # 4. Save to Database & JSON Cache
        self.db_manager.save_raw_reviews(raw_entries)
        self.db_manager.save_sanitized_reviews(sanitized_entries)
        self.db_manager.save_text_chunks(all_chunks)
        self.db_manager.save_cache_json(sanitized_entries, all_chunks)

        # 5. Export text files
        ExportManager.export_actual_reviews(raw_entries)
        ExportManager.export_finalized_reviews(sanitized_entries)

        summary = IngestionSummary(
            total_raw_ingested=len(raw_entries),
            total_sanitized_valid=len(sanitized_entries),
            total_rejected_short_or_emoji=total_rejected_count,
            total_pii_redacted=total_pii_count,
            total_chunks_created=len(all_chunks),
            channel_breakdown=channel_breakdown,
        )

        print(f"[+] Phase 1 Pipeline Completed Successfully!")
        print(f"   - Raw Ingested: {summary.total_raw_ingested}")
        print(f"   - Valid Sanitized: {summary.total_sanitized_valid}")
        print(f"   - PII Redacted Entries: {summary.total_pii_redacted}")
        print(f"   - 500-Token Chunks Created: {summary.total_chunks_created}")

        return summary, sanitized_entries, all_chunks


if __name__ == "__main__":
    pipeline = Phase1Pipeline()
    pipeline.run_pipeline()
