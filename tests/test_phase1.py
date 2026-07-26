import os
import pytest
from pathlib import Path
from datetime import datetime
from backend.models import RawReviewEntry, SanitizedReviewEntry
from backend.pii_normalizer import PIINormalizer
from backend.text_chunker import TextChunker
from backend.database import DatabaseManager
from backend.export_manager import ExportManager
from backend.pipeline import Phase1Pipeline
from backend.config import ACTUAL_REVIEWS_TXT, FINALIZED_REVIEWS_TXT, DB_PATH, CACHE_PATH


def test_pii_redaction_phone_numbers():
    text = "Please call me at 9876543210 regarding my order or reach +91-9876543210."
    scrubbed, pii_found = PIINormalizer.redact_pii(text)
    assert pii_found is True
    assert "9876543210" not in scrubbed
    assert "[PHONE_REDACTED]" in scrubbed


def test_pii_redaction_email_addresses():
    text = "Contact support at rahul.tech@gmail.com for refund issues."
    scrubbed, pii_found = PIINormalizer.redact_pii(text)
    assert pii_found is True
    assert "rahul.tech@gmail.com" not in scrubbed
    assert "[EMAIL_REDACTED]" in scrubbed


def test_pii_redaction_order_ids():
    text = "Order BLINK-889104 was missing milk and bread items."
    scrubbed, pii_found = PIINormalizer.redact_pii(text)
    assert pii_found is True
    assert "BLINK-889104" not in scrubbed
    assert "[ORDER_ID_REDACTED]" in scrubbed


def test_pii_redaction_addresses():
    text = "Delivered to Sector 56 Gurgaon 122011 instead of my home."
    scrubbed, pii_found = PIINormalizer.redact_pii(text)
    assert pii_found is True
    assert "122011" not in scrubbed
    assert "[ADDRESS_REDACTED]" in scrubbed


def test_word_count_filtering_less_than_8_words():
    raw_short = RawReviewEntry(
        review_id="TEST-001",
        app_package="com.grofers.inkart",
        rating=1,
        raw_text="Bad app, hate it.",  # 4 words
        source_channel="Google Play Store"
    )
    sanitized, status = PIINormalizer.sanitize(raw_short)
    assert sanitized is None
    assert "REJECTED_LESS_THAN_8_WORDS" in status


def test_rejection_of_reviews_with_emojis():
    raw_emoji = RawReviewEntry(
        review_id="TEST-EMOJI",
        app_package="com.grofers.inkart",
        rating=5,
        raw_text="Loved the instant grocery delivery! Fast milk and bread topup 👍 super app! 😊",
        source_channel="Google Play Store"
    )
    sanitized, status = PIINormalizer.sanitize(raw_emoji)
    assert sanitized is None
    assert status == "REJECTED_CONTAINS_EMOJIS"


def test_rejection_of_non_latin_language_reviews():
    raw_hindi = RawReviewEntry(
        review_id="TEST-HINDI",
        app_package="com.grofers.inkart",
        rating=5,
        raw_text="ब्लिंकिट की 10 मिनट डिलीवरी बहुत ही शानदार और तेज है। दूध और सब्जियां हमेशा ताजा मिलती हैं।",
        source_channel="Google Play Store"
    )
    sanitized, status = PIINormalizer.sanitize(raw_hindi)
    assert sanitized is None
    assert status == "REJECTED_NON_LATIN_LANGUAGE"


def test_text_chunking_500_tokens_50_overlap():
    sanitized = SanitizedReviewEntry(
        review_id="CHUNK-TEST",
        app_package="com.grofers.inkart",
        rating=2,
        sanitized_text="Blinkit Type-C fast charger purchased in an emergency stopped working after 2 hours. " * 30,
        word_count=300,
        has_pii_redacted=False,
        timestamp=datetime.utcnow(),
        source_channel="Reddit r/IndiaTech",
        community_tag="r/IndiaTech"
    )
    chunks = TextChunker.chunk_review(sanitized)
    assert len(chunks) >= 1
    assert chunks[0].attribution_tag == "[Source: r/IndiaTech]"
    assert chunks[0].star_rating == 2


def test_database_persistence_and_exports(tmp_path):
    test_db = tmp_path / "test_blinkit.db"
    test_cache = tmp_path / "test_cache.json"
    test_actual = tmp_path / "actual.txt"
    test_finalized = tmp_path / "finalized.txt"

    db = DatabaseManager(db_path=test_db, cache_path=test_cache)

    raw_entry = RawReviewEntry(
        review_id="DB-001",
        app_package="com.grofers.inkart",
        rating=4,
        raw_text="Great instant delivery for groceries and daily essentials in under 10 minutes.",
        source_channel="Google Play Store"
    )
    sanitized_entry, _ = PIINormalizer.sanitize(raw_entry)
    chunks = TextChunker.chunk_review(sanitized_entry)

    db.save_raw_reviews([raw_entry])
    db.save_sanitized_reviews([sanitized_entry])
    db.save_text_chunks(chunks)
    db.save_cache_json([sanitized_entry], chunks)

    ExportManager.export_actual_reviews([raw_entry], test_actual)
    ExportManager.export_finalized_reviews([sanitized_entry], test_finalized)

    assert test_db.exists()
    assert test_cache.exists()
    assert test_actual.exists()
    assert test_finalized.exists()

    all_sanitized = db.get_all_sanitized_reviews()
    assert len(all_sanitized) == 1
    assert all_sanitized[0].review_id == "DB-001"


def test_full_phase1_pipeline_execution():
    pipeline = Phase1Pipeline()
    summary, sanitized_entries, chunks = pipeline.run_pipeline(target_count=50)

    assert summary.total_raw_ingested == 50
    assert summary.total_sanitized_valid > 0
    assert summary.total_rejected_short_or_emoji > 0
    assert DB_PATH.exists()
    assert CACHE_PATH.exists()
    assert ACTUAL_REVIEWS_TXT.exists()
    assert FINALIZED_REVIEWS_TXT.exists()
