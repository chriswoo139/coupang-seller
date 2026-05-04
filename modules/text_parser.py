from __future__ import annotations

import re
from typing import Any


FIELD_ALIASES = {
    "product_url": ["product_url", "url", "link"],
    "product_name": ["product_name", "name", "title"],
    "brand_name": ["brand_name", "brand"],
    "category": ["category"],
    "product_type": ["product_type", "type"],
    "main_keyword": ["main_keyword", "keyword"],
    "price": ["price", "가격"],
    "review_count": ["review_count", "reviews", "review"],
    "rating": ["rating", "평점"],
    "package_count": ["package_count", "qty", "set"],
    "rocket_type": ["rocket_type", "delivery"],
}


def parse_competitor_text(text: str) -> dict[str, Any]:
    extracted: dict[str, Any] = {}
    if not text.strip():
        return extracted

    lines = [line.strip() for line in text.splitlines() if line.strip()]
    lowered_lines = [line.lower() for line in lines]

    for field, aliases in FIELD_ALIASES.items():
        for line in lines:
            lowered = line.lower()
            for alias in aliases:
                prefix = f"{alias}:"
                if lowered.startswith(prefix):
                    extracted[field] = line.split(":", 1)[1].strip()
                    break
            if field in extracted:
                break

    if "product_url" not in extracted:
        url_match = re.search(r"https?://\S+", text)
        if url_match:
            extracted["product_url"] = url_match.group(0)

    if "price" not in extracted:
        price_match = re.search(r"([0-9][0-9,]{2,})\s*(원|krw)?", text.lower())
        if price_match:
            extracted["price"] = price_match.group(1)

    if "review_count" not in extracted:
        review_match = re.search(r"(review|후기|리뷰)[^\d]*(\d[\d,]*)", text.lower())
        if review_match:
            extracted["review_count"] = review_match.group(2)

    if "rating" not in extracted:
        rating_match = re.search(r"([1-5](?:\.\d)?)\s*/?\s*5", text)
        if rating_match:
            extracted["rating"] = rating_match.group(1)

    if "package_count" not in extracted:
        package_match = re.search(r"(\d+)\s*(pcs|ea|개입|매|set)", text.lower())
        if package_match:
            extracted["package_count"] = package_match.group(1)

    if "product_name" not in extracted and lines:
        extracted["product_name"] = lines[0][:120]

    extracted.setdefault("category", "Women's Underwear & Accessories")
    extracted.setdefault("product_type", "Unknown")
    extracted.setdefault("main_keyword", "")
    extracted.setdefault("sub_keywords", "")
    extracted.setdefault("estimated_sales_level", "Medium")
    return extracted

