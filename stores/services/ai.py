"""AI Snap & Sell: turn a product photo + title + price into a full listing.

Uses Claude vision when an Anthropic credential is configured (settings.AI_ENABLED),
and otherwise falls back to a deterministic template writer so the feature always works.
"""

import base64
import json
import logging
import re

from django.conf import settings

logger = logging.getLogger(__name__)

LISTING_SCHEMA = {
    "type": "object",
    "properties": {
        "title": {"type": "string"},
        "title_bn": {"type": "string"},
        "description_en": {"type": "string"},
        "description_bn": {"type": "string"},
        "highlights": {"type": "array", "items": {"type": "string"}},
        "variants": {"type": "array", "items": {"type": "string"}},
        "tags": {"type": "array", "items": {"type": "string"}},
        "seo_title": {"type": "string"},
        "seo_description": {"type": "string"},
    },
    "required": [
        "title", "title_bn", "description_en", "description_bn", "highlights",
        "variants", "tags", "seo_title", "seo_description",
    ],
    "additionalProperties": False,
}

SYSTEM_PROMPT = (
    "You write product listings for small online shops in Bangladesh. Buyers read on mobile, "
    "mostly pay cash on delivery, and trust listings that are specific and honest. Write a clear "
    "English title and a natural Bangla title (not a word-for-word translation). Descriptions are "
    "2 short paragraphs each: what it is and who it suits, then material, care or usage details you "
    "can actually see or that the seller gave. Never invent certifications, brand names or "
    "guarantees. Give 3-5 highlights, the likely variants (sizes or colours) if any are visible or "
    "typical, 6-10 lowercase search tags, an SEO title under 60 characters and an SEO description "
    "under 155 characters."
)

MEDIA_TYPES = {"jpeg": "image/jpeg", "jpg": "image/jpeg", "png": "image/png", "webp": "image/webp", "gif": "image/gif"}

CATEGORY_HINTS = {
    "Fashion": {
        "bn": "পোশাক", "variants": ["S", "M", "L", "XL"],
        "highlights": ["Comfortable everyday fit", "Colour-fast fabric", "Easy to style for any occasion"],
        "tags": ["fashion", "clothing", "bangladesh fashion", "online shopping bd"],
    },
    "Cosmetics & beauty": {
        "bn": "সৌন্দর্য পণ্য", "variants": [],
        "highlights": ["Suitable for daily use", "Travel-friendly packaging", "Check the ingredient list before use"],
        "tags": ["beauty", "skincare", "cosmetics bd", "self care"],
    },
    "Home décor": {
        "bn": "ঘর সাজানোর পণ্য", "variants": [],
        "highlights": ["Adds warmth to any room", "Carefully packed for delivery", "Makes a thoughtful gift"],
        "tags": ["home decor", "interior", "gift", "handmade bd"],
    },
    "Handicrafts": {
        "bn": "হস্তশিল্প", "variants": [],
        "highlights": ["Handmade by local artisans", "Each piece is slightly unique", "Great as a gift"],
        "tags": ["handicraft", "handmade", "artisan", "deshi craft"],
    },
}
DEFAULT_HINT = {
    "bn": "পণ্য", "variants": [],
    "highlights": ["Quality checked before dispatch", "Cash on delivery available", "Fast delivery across Bangladesh"],
    "tags": ["online shopping bd", "cash on delivery"],
}


def generate_listing(title, price, category="", image=None):
    """Return a dict matching LISTING_SCHEMA plus a "source" key ("ai" or "template")."""
    title = (title or "").strip()
    if settings.AI_ENABLED:
        try:
            listing = _generate_with_claude(title, price, category, image)
            if listing:
                listing["source"] = "ai"
                return listing
        except Exception:  # never let an AI hiccup break product creation
            logger.exception("Claude listing generation failed; using template writer")
    listing = _generate_from_template(title, price, category)
    listing["source"] = "template"
    return listing


def _image_block(image):
    if not image:
        return None
    ext = (getattr(image, "name", "") or "").rsplit(".", 1)[-1].lower()
    media_type = getattr(image, "content_type", None) or MEDIA_TYPES.get(ext)
    if media_type not in MEDIA_TYPES.values():
        return None
    image.seek(0)
    data = base64.standard_b64encode(image.read()).decode("utf-8")
    image.seek(0)
    return {"type": "image", "source": {"type": "base64", "media_type": media_type, "data": data}}


def _generate_with_claude(title, price, category, image):
    import anthropic

    client = anthropic.Anthropic()
    content = []
    block = _image_block(image)
    if block:
        content.append(block)
    content.append({
        "type": "text",
        "text": (
            f"Seller's title: {title or '(none, describe from the photo)'}\n"
            f"Price: BDT {price}\n"
            f"Category: {category or 'not given'}\n"
            "Write the listing."
        ),
    })
    response = client.messages.create(
        model=settings.AI_MODEL,
        max_tokens=4000,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": content}],
        output_config={"effort": "low", "format": {"type": "json_schema", "schema": LISTING_SCHEMA}},
        # Route safety-classifier refusals to a fallback model server-side.
        extra_headers={"anthropic-beta": "server-side-fallback-2026-07-01"},
        extra_body={"fallbacks": "default"},
    )
    if response.stop_reason in ("refusal", "max_tokens"):
        logger.warning("Claude listing stopped early: %s", response.stop_reason)
        return None
    text = next((b.text for b in response.content if b.type == "text"), "")
    return _clean(json.loads(text))


def _clean(data):
    data["seo_title"] = data.get("seo_title", "")[:70]
    data["seo_description"] = data.get("seo_description", "")[:170]
    data["tags"] = [t.strip().lower() for t in data.get("tags", []) if t.strip()][:12]
    return data


def _generate_from_template(title, price, category):
    hint = CATEGORY_HINTS.get(category, DEFAULT_HINT)
    nice_title = re.sub(r"\s+", " ", title).strip().title() or "New Arrival"
    words = [w.lower() for w in re.findall(r"[A-Za-z]{3,}", nice_title)]
    price_txt = f"৳{int(price):,}" if price not in (None, "") else ""
    tags = list(dict.fromkeys(words + hint["tags"]))[:10]
    return _clean({
        "title": nice_title,
        "title_bn": f"{nice_title} — প্রিমিয়াম {hint['bn']}",
        "description_en": (
            f"Meet the {nice_title}: picked for everyday use and made to look as good in person as it does "
            f"in the photo. A dependable choice at {price_txt}, whether you're treating yourself or buying a gift.\n\n"
            "Every order is quality checked before dispatch. Pay cash on delivery or with bKash and Nagad, "
            "and get it delivered anywhere in Bangladesh."
        ),
        "description_bn": (
            f"আমাদের {nice_title} প্রতিদিনের ব্যবহারের জন্য বাছাই করা, ছবিতে যেমন দেখছেন হাতে পেলেও তেমনই পাবেন। "
            f"মাত্র {price_txt} দামে নিজের জন্য বা উপহার হিসেবে দারুণ পছন্দ।\n\n"
            "প্রতিটি অর্ডার পাঠানোর আগে যাচাই করা হয়। ক্যাশ অন ডেলিভারি, বিকাশ বা নগদে পেমেন্ট করুন — "
            "সারা বাংলাদেশে হোম ডেলিভারি।"
        ),
        "highlights": hint["highlights"],
        "variants": hint["variants"],
        "tags": tags,
        "seo_title": f"{nice_title} | Buy Online in Bangladesh",
        "seo_description": (
            f"Order {nice_title} online for {price_txt}. Cash on delivery, bKash and Nagad accepted. "
            "Fast delivery across Bangladesh."
        ),
    })
