import random
import uuid
from datetime import datetime, timedelta
from typing import List
from backend.config import APP_PACKAGE, TARGET_CORPUS_COUNT, CHANNELS
from backend.models import RawReviewEntry


class MultiChannelIngestionConnector:
    """Ingestion Engine fetching multi-channel public customer feedback entries for Blinkit."""

    TEMPLATES = [
        # --- Core Grocery Loyalty & Routine (4-5 Stars) ---
        {
            "category": "Core Grocery",
            "channel": "PLAY_STORE",
            "rating_range": (4, 5),
            "text": "Blinkit is my absolute go-to for daily grocery top-ups! Fresh Amul milk, brown bread, and onions delivered in under 10 minutes every single morning without fail. The dark store in my locality is super efficient. Order #BLINK-889104 arrived in pristine condition.",
            "title": "Unmatched 10-minute grocery delivery",
            "pii": "Order #BLINK-889104, Phone 9876543210"
        },
        {
            "category": "Core Grocery",
            "channel": "APP_STORE",
            "rating_range": (4, 5),
            "text": "Living alone in Gurgaon, Blinkit saves me every day. Whenever I run out of eggs, butter, or snacks late at night, I just tap reorder. The delivery rider is always polite and reaches my apartment within 8 minutes.",
            "title": "Life saver for daily essentials",
            "pii": "Pincode 122002, Flat 302 Sector 56"
        },
        # --- Tech Accessories Friction (1-3 Stars) ---
        {
            "category": "Tech Accessories",
            "channel": "REDDIT_INDIA_TECH",
            "rating_range": (1, 2),
            "text": "Why do people buy electronics on Blinkit? I ordered a Type-C fast charger for Rs. 799 because I was in an emergency meeting. Received a box with zero brand seal, and it stopped working after 2 hours! Customer support bot refused a return saying 10-min delivery items are non-returnable. Contact me at rahul.tech@gmail.com for proof.",
            "title": "Beware of buying tech accessories on 10-minute apps",
            "pii": "rahul.tech@gmail.com"
        },
        {
            "category": "Tech Accessories",
            "channel": "PLAY_STORE",
            "rating_range": (1, 3),
            "text": "Ordered Boat wireless earbuds on Blinkit during festive sale. The sound quality was distorted in the right earbud. Tried requesting a replacement immediately, but the app says no return window available for electronic gadgets. Unacceptable policy when selling Rs. 1500 items!",
            "title": "No return policy for defective earbuds",
            "pii": "TXN-998214"
        },
        # --- Beauty & Personal Care Friction (1-3 Stars) ---
        {
            "category": "Beauty & Personal Care",
            "channel": "REDDIT_DELHI",
            "rating_range": (1, 3),
            "text": "Has anyone bought luxury skincare or Cetaphil cleanser from Blinkit? I ordered yesterday and the packaging bottle seal was completely opened and leaking. I am terrified it might be a fake or expired product. Blinkit needs a proper verified authenticity tag if they want us to buy cosmetics.",
            "title": "Unsealed skincare bottle delivered",
            "pii": ""
        },
        {
            "category": "Beauty & Personal Care",
            "channel": "APP_STORE",
            "rating_range": (2, 3),
            "text": "Blinkit is great for instant veggies, but buying shampoo or face creams is risky. The product delivered was manufactured 18 months ago. When I raised a support ticket, the automated chatbot gave me a generic automated response without refunding my money.",
            "title": "Old stock cosmetics delivered",
            "pii": "Order ORD882910"
        },
        # --- Home Utilities & Appliances Friction (1-3 Stars) ---
        {
            "category": "Home Utilities",
            "channel": "REDDIT_BANGALORE",
            "rating_range": (1, 3),
            "text": "Bought an electric kettle on Blinkit when I had guests at home. The heating element malfunctioned on day one. Since there is no 3-day easy return option on Blinkit like Amazon, I had to physically run around to the manufacturer service center in Indiranagar.",
            "title": "Defective kettle - no return support",
            "pii": "Address Indiranagar Bangalore 560038"
        },
        {
            "category": "Home Utilities",
            "channel": "PLAY_STORE",
            "rating_range": (2, 3),
            "text": "Ordered a multi-socket extension cord and kitchen scissors. Extension cord had loose pins. While quick delivery is awesome, Blinkit must ensure basic quality control checks before dark store riders dispatch fragile home appliances.",
            "title": "Loose pins on extension cord",
            "pii": ""
        },
        # --- Pet Care & Gourmet ---
        {
            "category": "Pet Care",
            "channel": "REDDIT_GURGAON",
            "rating_range": (3, 4),
            "text": "Whiskas cat food is frequently out of stock on Blinkit dark stores near DLF Phase 3. When it is available, delivery is instant, but stock consistency for pet food needs serious improvement.",
            "title": "Pet food stockout issue",
            "pii": ""
        },
        {
            "category": "Gourmet & Cafe",
            "channel": "PUBLIC_UNBOXING",
            "rating_range": (4, 5),
            "text": "Tried ordering gourmet coffee beans and artisan sourdough bread on Blinkit Bistro. Arrived warm and fresh in 9 minutes! Fantastic expansion by Blinkit beyond standard grocery items.",
            "title": "Blinkit Bistro coffee delivered hot",
            "pii": ""
        },
        # --- Refund Chatbot & Support Friction (1-2 Stars) ---
        {
            "category": "App UX & Support",
            "channel": "REDDIT_INDIA",
            "rating_range": (1, 2),
            "text": "Blinkit chatbot refund workflow is frustrating! Three missing items in my grocery cart worth Rs. 450. The automated bot kept looping between 'checking with delivery executive' and 'issue resolved'. Couldn't reach a human support executive for 2 hours.",
            "title": "Chatbot refund loop horror",
            "pii": "Phone 09811223344"
        },

        # --- Rejection Templates (For Normalization Validation) ---
        # 1. Less than 8 words
        {
            "category": "General",
            "channel": "PLAY_STORE",
            "rating_range": (1, 1),
            "text": "Bad app. Very slow delivery.", # 5 words -> Should be REJECTED
            "title": "Bad app",
            "pii": ""
        },
        # 2. Contains Emojis
        {
            "category": "Core Grocery",
            "channel": "PLAY_STORE",
            "rating_range": (5, 5),
            "text": "Loved the instant grocery delivery! Fast milk and bread topup 👍 super app! 😊", # Contains Emojis -> Should be REJECTED
            "title": "Super app 👍",
            "pii": ""
        },
        # 3. Non-Latin Language (Devanagari / Hindi script)
        {
            "category": "Core Grocery",
            "channel": "PLAY_STORE",
            "rating_range": (5, 5),
            "text": "ब्लिंकिट की 10 मिनट डिलीवरी बहुत ही शानदार और तेज है। दूध और सब्जियां हमेशा ताजा मिलती हैं।", # Devanagari script -> Should be REJECTED
            "title": "बहुत अच्छी ऐप",
            "pii": ""
        }
    ]

    @classmethod
    def generate_corpus(cls, target_count: int = TARGET_CORPUS_COUNT) -> List[RawReviewEntry]:
        """Generates a multi-channel raw review corpus of target_count entries including rejection test samples."""
        raw_entries: List[RawReviewEntry] = []
        now = datetime.utcnow()

        for i in range(target_count):
            tpl = random.choice(cls.TEMPLATES)
            rating = random.randint(tpl["rating_range"][0], tpl["rating_range"][1])
            channel_key = tpl["channel"]
            channel_name = CHANNELS[channel_key]

            review_id = f"REV-{100000 + i}"
            author = f"User_{random.randint(1000, 9999)}"
            time_offset = timedelta(days=random.randint(0, 180), minutes=random.randint(0, 1440))
            timestamp = now - time_offset

            raw_text = tpl["text"]
            if tpl["pii"] and random.random() > 0.4:
                raw_text += f" (Customer contact info: {tpl['pii']})"

            community_tag = None
            if "REDDIT" in channel_key:
                community_tag = channel_name.replace("Reddit ", "")

            entry = RawReviewEntry(
                review_id=review_id,
                app_package=APP_PACKAGE,
                author_name=author,
                rating=rating,
                title=tpl["title"],
                raw_text=raw_text,
                timestamp=timestamp,
                source_channel=channel_name,
                community_tag=community_tag,
                thumbs_up_count=random.randint(0, 45),
                product_category=tpl["category"],
            )
            raw_entries.append(entry)

        return raw_entries
