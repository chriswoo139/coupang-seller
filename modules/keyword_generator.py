from __future__ import annotations

from typing import Any


PRODUCT_KEYWORD_MAP = {
    "팬티": ["여성 팬티", "심리스 팬티", "노라인 팬티", "편한 여성 팬티", "여름 팬티"],
    "underwear": ["여성 팬티", "심리스 팬티", "노라인 팬티", "데일리 속옷"],
    "세탁망": ["브라 세탁망", "속옷 세탁망", "브라 변형 방지 세탁망", "세탁 보호망"],
    "hook": ["브라 연장 후크", "브라 후크 연장", "속옷 후크 조절", "브라 밴드 연장"],
    "clip": ["브라끈 클립", "브라끈 흘러내림 방지", "어깨끈 고정 클립", "브라끈 정리"],
    "안전": ["여성 안전바지", "속바지", "스커트 속바지", "편한 안전바지"],
}

NEGATIVE_KEYWORDS = [
    "남성",
    "남자",
    "아동",
    "키즈",
    "의료",
    "치료",
    "교정",
    "성인용",
    "섹시 코스튬",
]


def _match_base_keywords(product_type: str) -> list[str]:
    lowered = product_type.lower()
    for key, keywords in PRODUCT_KEYWORD_MAP.items():
        if key in lowered:
            return keywords
    return ["여성 속옷", "데일리 이너웨어", "실용 생활용품"]


def generate_keywords(product: dict[str, Any]) -> dict[str, list[str] | str]:
    product_type = str(product.get("product_type", ""))
    main_keyword = str(product.get("main_keyword", "")).strip()
    sub_keywords = [item.strip() for item in str(product.get("sub_keywords", "")).split(",") if item.strip()]
    selling_points = [item.strip() for item in str(product.get("main_selling_points", "")).split(",") if item.strip()]

    base_keywords = _match_base_keywords(product_type)
    manual_ad_keywords = list(dict.fromkeys(([main_keyword] if main_keyword else []) + base_keywords[:4] + sub_keywords[:4]))

    pain_terms = ["말림 없는", "자국 없는", "편안한 착용감", "세탁 변형 방지", "흘러내림 방지", "압박 없는"]
    auto_seed_keywords = list(dict.fromkeys(base_keywords + sub_keywords + pain_terms + selling_points[:4]))
    detail_keywords = list(dict.fromkeys(base_keywords[:3] + pain_terms[:4] + selling_points[:3]))
    title_keywords = list(dict.fromkeys(([main_keyword] if main_keyword else []) + base_keywords[:3] + selling_points[:2]))

    return {
        "manual_ad_keywords": manual_ad_keywords[:10],
        "auto_ad_seed_keywords": auto_seed_keywords[:15],
        "negative_keywords": NEGATIVE_KEYWORDS,
        "title_keywords": title_keywords[:8],
        "detail_page_keywords": detail_keywords[:12],
    }

