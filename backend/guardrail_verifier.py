import re
from typing import Tuple, Optional


class GuardrailVerifier:
    """
    Refusal & Guardrail Verifier for Blinkit RAG Discovery Engine.
    Intercepts non-factual, speculative, stock/financial, or personal PII queries 
    prior to vector retrieval and provides polite navigational guidance.
    """

    # Keyword patterns for out-of-scope query detection
    STOCK_FINANCIAL_PATTERNS = re.compile(
        r'\b(?:stocks?|stock price|share price|zomato stock|blinkit stock|valuation|market cap|quarterly revenue|earnings|dividend|nifty|sensex)\b',
        re.IGNORECASE
    )
    OUT_OF_DOMAIN_PATTERNS = re.compile(
        r'\b(?:automobiles?|cars?|car delivery|deliver cars|buy house|real estate|flight tickets?|hotel bookings?|weather forecast|cricket score)\b',
        re.IGNORECASE
    )
    PII_EXTRACTION_PATTERNS = re.compile(
        r'\b(?:phone numbers?|email address(?:es)?|order ids?|home address(?:es)?|personal details|reviewer names?|user phone|contact info(?:rmation)?)\b',
        re.IGNORECASE
    )

    STANDARD_REFUSAL_MESSAGE = (
        "This query falls outside the indexed customer feedback corpus. "
        "Please ask questions related to product friction, returns, category exploration, or user sentiment on Blinkit."
    )

    @classmethod
    def validate_query(cls, query_text: str) -> Tuple[bool, Optional[str]]:
        """
        Validates if query falls strictly within the indexed customer feedback corpus.
        Returns (is_valid, refusal_message_or_none).
        """
        if not query_text or not query_text.strip():
            return False, "Query text cannot be empty. Please enter a valid product research question."

        text = query_text.strip()

        # 1. Check Stock / Financial Queries
        if cls.STOCK_FINANCIAL_PATTERNS.search(text):
            return False, cls.STANDARD_REFUSAL_MESSAGE

        # 2. Check Out-of-Domain Requests
        if cls.OUT_OF_DOMAIN_PATTERNS.search(text):
            return False, cls.STANDARD_REFUSAL_MESSAGE

        # 3. Check PII Extraction Requests
        if cls.PII_EXTRACTION_PATTERNS.search(text):
            return False, cls.STANDARD_REFUSAL_MESSAGE

        return True, None
