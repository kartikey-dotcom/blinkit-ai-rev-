import os
from pathlib import Path

# Load environment variables from .env file if present
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Base workspace directory
BASE_DIR = Path(__file__).resolve().parent.parent

# API Key Configuration
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

# Application & Target Scope
APP_PACKAGE = os.getenv("TARGET_APP_PACKAGE", "com.grofers.inkart")
APP_NAME = "Blinkit"
TARGET_ORGANIZATION = "Blinkit Commerce Private Limited"

# Storage & Export Paths
DB_PATH = BASE_DIR / "blinkit_reviews.db"
CACHE_PATH = BASE_DIR / "reviews_cache.json"
ACTUAL_REVIEWS_TXT = BASE_DIR / "actual_reviews.txt"
FINALIZED_REVIEWS_TXT = BASE_DIR / "finalized_reviews.txt"

# Ingestion & Corpus Specifications
TARGET_CORPUS_COUNT = int(os.getenv("TARGET_CORPUS_INGESTION_COUNT", "5000"))
MIN_WORD_COUNT = int(os.getenv("MIN_WORD_COUNT", "8"))

# Chunking & Vector Store Parameters
CHUNK_SIZE_TOKENS = 500
CHUNK_OVERLAP_TOKENS = 50
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")
EMBEDDING_DIM = int(os.getenv("EMBEDDING_DIM", "1536"))
COSINE_SIMILARITY_THRESHOLD = float(os.getenv("COSINE_SIMILARITY_THRESHOLD", "0.75"))

# Google AI Studio (Gemini 1.5 Flash) Rate Limits & Batching Strategy
GEMINI_RPM_LIMIT = int(os.getenv("GOOGLE_AI_STUDIO_RPM_LIMIT", "60"))
GEMINI_TPM_LIMIT = int(os.getenv("GOOGLE_AI_STUDIO_TPM_LIMIT", "100000"))
GEMINI_BATCH_SIZE = 10             # Reviews per prompt batch (600 reviews/min throughput)
GEMINI_REQUEST_GAP_SECONDS = 1.0   # Asynchronous Leaky Bucket minimum gap

# Ingestion Multi-Channels
CHANNELS = {
    "PLAY_STORE": "Google Play Store",
    "APP_STORE": "iOS App Store",
    "REDDIT_INDIA_TECH": "Reddit r/IndiaTech",
    "REDDIT_DELHI": "Reddit r/delhi",
    "REDDIT_BANGALORE": "Reddit r/bangalore",
    "REDDIT_GURGAON": "Reddit r/gurgaon",
    "REDDIT_INDIA": "Reddit r/india",
    "PUBLIC_UNBOXING": "Public Unboxing & Commentary",
}
