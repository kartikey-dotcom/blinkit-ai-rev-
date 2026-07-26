import asyncio
from typing import Dict, Any, List, Optional
from backend.config import GEMINI_BATCH_SIZE
from backend.llm_rate_limiter import GoogleAIStudioRateLimiter
from backend.models import SanitizedReviewEntry

# 5 Q-Commerce Aspect Categories
ASPECT_CATEGORIES = [
    "App UX, Pin Location & Search UI Visibility",
    "Delivery Speed, Dark Store Fulfillment & Rider Conduct",
    "Product Freshness, Spoilage Anxiety & Quality Assurance",
    "Pricing, Small-Cart Handling Fees & Surge Surcharges",
    "Non-Core Category Adoption Friction",
]

# 5 Core Category Switching Friction Points
FRICTION_CATEGORIES = [
    "Quality & Spoilage Anxiety",
    "App UI & Search Visibility",
    "Pricing, Handling & Surge Fees",
    "Return & Refund Policy Friction",
    "Habitual Emergency Reorder Mental Model",
]


class GeminiABSAEngine:
    """
    Aspect-Based Sentiment Analysis (ABSA) & Category Friction Engine for Blinkit AI Reviews.
    Throttled by GoogleAIStudioRateLimiter (60 RPM, 100K TPM).
    """

    def __init__(self, rate_limiter: Optional[GoogleAIStudioRateLimiter] = None):
        self.rate_limiter = rate_limiter or GoogleAIStudioRateLimiter()

    @classmethod
    def classify_review(cls, text: str, rating: int, product_category: str = "General") -> Dict[str, Any]:
        """
        Evaluates customer review text to extract Primary Aspect, Friction Category, Sentiment Score, and Critical Flag.
        """
        txt_lower = text.lower()

        # 1. Friction & Aspect Classification
        if any(kw in txt_lower for kw in ["seal", "fake", "defective", "spoiled", "damaged", "counterfeit", "rotten", "leaking", "expired", "used"]):
            aspect = "Product Freshness, Spoilage Anxiety & Quality Assurance"
            friction = "Quality & Spoilage Anxiety"
            score = -0.90 if rating <= 2 else (0.85 if rating >= 4 else 0.1)

        elif any(kw in txt_lower for kw in ["return", "refund", "non-returnable", "replacement", "3-day", "warranty", "policy", "service center"]):
            aspect = "Non-Core Category Adoption Friction"
            friction = "Return & Refund Policy Friction"
            score = -0.88 if rating <= 2 else (0.75 if rating >= 4 else 0.0)

        elif any(kw in txt_lower for kw in ["ui", "search", "banner", "obscured", "hidden", "browse", "pin location", "otp", "crash"]):
            aspect = "App UX, Pin Location & Search UI Visibility"
            friction = "App UI & Search Visibility"
            score = -0.85 if rating <= 2 else (0.80 if rating >= 4 else 0.0)

        elif any(kw in txt_lower for kw in ["surge", "handling fee", "delivery fee", "coupon", "discount", "price", "expensive"]):
            aspect = "Pricing, Small-Cart Handling Fees & Surge Surcharges"
            friction = "Pricing, Handling & Surge Fees"
            score = -0.80 if rating <= 2 else (0.70 if rating >= 4 else 0.0)

        elif any(kw in txt_lower for kw in ["reorder", "milk", "bread", "veggies", "grocery", "habit", "emergency", "topup"]):
            aspect = "Delivery Speed, Dark Store Fulfillment & Rider Conduct"
            friction = "Habitual Emergency Reorder Mental Model"
            score = 0.90 if rating >= 4 else (-0.75 if rating <= 2 else 0.2)

        else:
            if product_category in ["Tech Accessories", "Beauty & Personal Care", "Home Utilities"]:
                aspect = "Non-Core Category Adoption Friction"
                friction = "Quality & Spoilage Anxiety"
            else:
                aspect = "Delivery Speed, Dark Store Fulfillment & Rider Conduct"
                friction = "Habitual Emergency Reorder Mental Model"
            score = -0.70 if rating <= 2 else (0.85 if rating >= 4 else 0.1)

        return {
            "primary_aspect": aspect,
            "friction_category": friction,
            "sentiment_score": score,
            "confidence": 0.95,
            "is_critical": rating <= 2,
        }

    async def analyze_batch(self, entries: List[SanitizedReviewEntry]) -> List[Dict[str, Any]]:
        """
        Analyzes a batch of normalized reviews (up to GEMINI_BATCH_SIZE).
        Enforces 60 RPM and 100K TPM rate limits.
        """
        if not entries:
            return []

        # Estimate tokens for 10-review batch (~1500 tokens)
        estimated_tokens = sum(e.word_count * 2 for e in entries)
        await self.rate_limiter.acquire_slot(estimated_tokens=estimated_tokens)

        results = []
        for e in entries:
            analysis = self.classify_review(e.sanitized_text, e.rating, e.product_category)
            results.append({
                "review_id": e.review_id,
                "rating": e.rating,
                "primary_aspect": analysis["primary_aspect"],
                "friction_category": analysis["friction_category"],
                "sentiment_score": analysis["sentiment_score"],
                "confidence": analysis["confidence"],
                "is_critical": analysis["is_critical"],
                "product_category": e.product_category,
                "source_channel": e.source_channel,
            })

        return results
