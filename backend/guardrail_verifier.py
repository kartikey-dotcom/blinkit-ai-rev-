import re
from typing import Tuple, Optional


class GuardrailVerifier:
    """
    Refusal & Guardrail Verifier for Blinkit RAG Discovery Engine.
    Intercepts non-factual, speculative, stock/financial, trivia, general knowledge, 
    or personal PII queries prior to vector retrieval and provides polite navigational guidance.
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
    GENERAL_KNOWLEDGE_PATTERNS = re.compile(
        r'\b(?:president|prime minister|governor|capital|who is|who was|who won|world cup|olympics|movie|actor|actress|politics|election|narendra modi|droupadi murmu|bjp|congress|recipe|cook|math|joke|riddle|song|lyrics|weather|temperature|history|geography|science|planet|sun|moon|star)\b',
        re.IGNORECASE
    )
    DOMAIN_KEYWORDS_PATTERN = re.compile(
        r'\b(?:blinkit|grofers|zomato|grocery|groceries|order|orders|delivery|deliver|return|returns|refund|exchange|item|items|product|products|category|categories|tech|charger|earbud|cosmetic|skincare|app|support|chat|surge|price|fee|checkout|cart|store|dark store|review|reviews|customer|customers|user|users|feedback|quality|delay|speed|habit|buy|purchase|explore|resistance|friction)\b',
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

        # 4. Check General Knowledge / Trivia / Politics / Irrelevant Queries
        if cls.GENERAL_KNOWLEDGE_PATTERNS.search(text):
            if not cls.DOMAIN_KEYWORDS_PATTERN.search(text):
                return False, cls.STANDARD_REFUSAL_MESSAGE

        # 5. Domain Relevance Safety Net: If query has >= 3 words and zero domain keywords
        words = text.split()
        if len(words) >= 3 and not cls.DOMAIN_KEYWORDS_PATTERN.search(text):
            return False, cls.STANDARD_REFUSAL_MESSAGE

        return True, None
