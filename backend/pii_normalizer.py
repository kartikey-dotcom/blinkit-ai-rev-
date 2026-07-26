import re
import unicodedata
from typing import Tuple, Optional
from backend.config import MIN_WORD_COUNT
from backend.models import RawReviewEntry, SanitizedReviewEntry


class PIINormalizer:
    """Zero-Trust PII Masking Gateway & Data Normalizer Engine."""

    # Regex patterns for PII redaction
    PHONE_REGEX = re.compile(
        r'(?:\+?91[\-\s]?)?(?:[6-9]\d{9}|[6-9]\d{4}[\-\s]\d{5}|0\d{10})\b'
    )
    EMAIL_REGEX = re.compile(
        r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}\b'
    )
    ORDER_ID_REGEX = re.compile(
        r'\b(?:ORD|BLINK|ORDER|ID|TXN|GROF)[-_\s#]*[A-Z0-9]{5,12}\b',
        re.IGNORECASE
    )
    ADDRESS_REGEX = re.compile(
        r'\b(?:flat|house|apt|apartment|sector|phase|block|pocket|tower|street|road|nagar|colony|pincode|pin\s*code)[\s\w,.\-]*\b\d{6}\b|\b\d{6}\b',
        re.IGNORECASE
    )

    @classmethod
    def has_emojis(cls, text: str) -> bool:
        """Detect if text contains any emoji characters."""
        for char in text:
            category = unicodedata.category(char)
            cp = ord(char)
            if category == "So" or (
                0x1F600 <= cp <= 0x1F64F or  # Emoticons
                0x1F300 <= cp <= 0x1F5FF or  # Misc Symbols & Pictographs
                0x1F680 <= cp <= 0x1F6FF or  # Transport & Map
                0x2600  <= cp <= 0x26FF  or  # Misc Symbols
                0x2700  <= cp <= 0x27BF  or  # Dingbats
                0x1F900 <= cp <= 0x1F9FF or  # Supplemental Symbols
                0x1FA70 <= cp <= 0x1FAFF     # Symbols & Pictographs Extended
            ):
                return True
        return False

    @classmethod
    def is_latin_script(cls, text: str) -> bool:
        """Check if text contains only valid Latin script characters (English/Hinglish in Latin alphabet)."""
        for char in text:
            if char.isalpha():
                name = unicodedata.name(char, "")
                if "LATIN" not in name:
                    return False
        return True

    @classmethod
    def redact_pii(cls, text: str) -> Tuple[str, bool]:
        """Redact sensitive customer PII and return (scrubbed_text, pii_found)."""
        pii_found = False
        scrubbed = text

        if cls.EMAIL_REGEX.search(scrubbed):
            scrubbed = cls.EMAIL_REGEX.sub("[EMAIL_REDACTED]", scrubbed)
            pii_found = True

        if cls.PHONE_REGEX.search(scrubbed):
            scrubbed = cls.PHONE_REGEX.sub("[PHONE_REDACTED]", scrubbed)
            pii_found = True

        if cls.ORDER_ID_REGEX.search(scrubbed):
            scrubbed = cls.ORDER_ID_REGEX.sub("[ORDER_ID_REDACTED]", scrubbed)
            pii_found = True

        if cls.ADDRESS_REGEX.search(scrubbed):
            scrubbed = cls.ADDRESS_REGEX.sub("[ADDRESS_REDACTED]", scrubbed)
            pii_found = True

        return scrubbed, pii_found

    @classmethod
    def sanitize(cls, raw_entry: RawReviewEntry) -> Tuple[Optional[SanitizedReviewEntry], str]:
        """
        Sanitize and normalize a raw review entry according to Phase 1 Normalization Rules:
        1. Remove reviews with less than 8 words.
        2. Remove reviews containing emojis or written in non-Latin/other languages.
        """
        text_content = raw_entry.raw_text
        if raw_entry.title:
            text_content = f"{raw_entry.title}. {text_content}"

        # Rule 2a: Reject reviews with emojis
        if cls.has_emojis(text_content):
            return None, "REJECTED_CONTAINS_EMOJIS"

        # Rule 2b: Reject reviews in non-Latin/other languages
        if not cls.is_latin_script(text_content):
            return None, "REJECTED_NON_LATIN_LANGUAGE"

        # Redact PII
        scrubbed_text, pii_redacted = cls.redact_pii(text_content)
        cleaned_text = re.sub(r'\s+', ' ', scrubbed_text).strip()

        # Rule 1: Reject reviews with less than 8 words
        words = cleaned_text.split()
        word_count = len(words)

        if word_count < MIN_WORD_COUNT:
            return None, f"REJECTED_LESS_THAN_8_WORDS ({word_count} < {MIN_WORD_COUNT})"

        sanitized_entry = SanitizedReviewEntry(
            review_id=raw_entry.review_id,
            app_package=raw_entry.app_package,
            rating=raw_entry.rating,
            sanitized_text=cleaned_text,
            word_count=word_count,
            has_pii_redacted=pii_redacted,
            timestamp=raw_entry.timestamp,
            source_channel=raw_entry.source_channel,
            community_tag=raw_entry.community_tag,
            thumbs_up_count=raw_entry.thumbs_up_count,
            product_category=raw_entry.product_category or "General",
            is_valid_latin=True,
        )

        return sanitized_entry, "SUCCESS"
