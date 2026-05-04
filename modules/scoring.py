from __future__ import annotations

from collections import Counter
from typing import Any

import pandas as pd

from .profit_calculator import ProfitInput, calculate_profit


def clamp(value: float, minimum: float = 0.0, maximum: float = 100.0) -> float:
    return max(minimum, min(value, maximum))


def _safe_float(value: Any, fallback: float = 0.0) -> float:
    if value in (None, ""):
        return fallback
    try:
        return float(value)
    except (TypeError, ValueError):
        return fallback


def _keyword_count(text: Any) -> int:
    if not text:
        return 0
    parts = [item.strip() for item in str(text).replace("/", ",").split(",") if item.strip()]
    return len(parts)


def _risk_score(text: Any) -> int:
    mapping = {"low": 20, "medium": 60, "high": 90}
    return mapping.get(str(text).strip().lower(), 40)


def _sales_level_score(level: Any) -> int:
    mapping = {"low": 35, "medium": 60, "high": 85}
    return mapping.get(str(level).strip().lower(), 55)


def estimate_competition_score(row: pd.Series, context: pd.DataFrame) -> float:
    review_max = max(_safe_float(context["review_count"].max(), 1.0), 1.0)
    rating_max = max(_safe_float(context["rating"].max(), 5.0), 5.0)
    rank_max = max(_safe_float(context["rank_position"].max(), 1.0), 1.0)
    price_min = max(_safe_float(context["price"].min(), 1.0), 1.0)
    price_now = max(_safe_float(row.get("price"), price_min), 1.0)

    review_component = (_safe_float(row.get("review_count")) / review_max) * 28
    rating_component = (_safe_float(row.get("rating")) / rating_max) * 18
    price_component = (price_min / price_now) * 18
    image_component = min(_safe_float(row.get("image_count")) / 10, 1.0) * 12
    rank_component = ((rank_max - _safe_float(row.get("rank_position"), rank_max)) / rank_max) * 14
    sameness_component = min(_keyword_count(row.get("title_keywords")) / 6, 1.0) * 10

    return round(clamp(review_component + rating_component + price_component + image_component + rank_component + sameness_component), 1)


def estimate_demand_score(row: pd.Series) -> float:
    review_component = min(_safe_float(row.get("review_count")) / 2000, 1.0) * 24
    growth_component = _sales_level_score(row.get("estimated_sales_level")) * 0.18
    keyword_component = min((_keyword_count(row.get("sub_keywords")) + 1) / 8, 1.0) * 14
    replenishment_component = 12 if any(token in str(row.get("product_type", "")).lower() for token in ["panty", "underwear", "safety", "clip", "hook", "laundry"]) else 8
    female_repeat_component = 12
    bundle_component = 10 if _safe_float(row.get("package_count"), 1) >= 3 else 7
    rocket_component = 8 if "rocket" in str(row.get("rocket_type", "")).lower() else 5
    short_video_component = 8 if any(token in str(row.get("main_selling_points", "")).lower() for token in ["cool", "ice", "seamless", "no-line", "wash", "anti-slip"]) else 5

    return round(clamp(
        review_component
        + growth_component
        + keyword_component
        + replenishment_component
        + female_repeat_component
        + bundle_component
        + rocket_component
        + short_video_component
    ), 1)


def estimate_differentiation_score(row: pd.Series) -> float:
    weak_points = str(row.get("weak_points", ""))
    bad_reviews = str(row.get("bad_review_points", ""))
    qna_points = str(row.get("qna_points", ""))
    opportunities = str(row.get("differentiation_opportunity", ""))

    issue_hits = sum(
        keyword in f"{weak_points} {bad_reviews} {qna_points}".lower()
        for keyword in ["size", "thin", "hot", "wash", "deform", "cheap", "color", "strap", "slip", "tight"]
    )
    opportunity_depth = min(_keyword_count(opportunities) + issue_hits, 6)
    compliance_penalty = _risk_score(row.get("compliance_risk")) * 0.15
    return_risk_penalty = _risk_score(row.get("return_risk")) * 0.1

    base_score = 40 + opportunity_depth * 10 - compliance_penalty - return_risk_penalty
    return round(clamp(base_score), 1)


def estimate_logistics_score(row: pd.Series) -> float:
    product_type = str(row.get("product_type", "")).lower()
    if any(token in product_type for token in ["hook", "clip", "laundry", "extension"]):
        base = 85
    elif any(token in product_type for token in ["panty", "underwear", "safety"]):
        base = 78
    else:
        base = 72

    if "fragile" in str(row.get("return_risk", "")).lower():
        base -= 12
    if "size" in str(row.get("return_risk", "")).lower():
        base -= 8
    return round(clamp(base), 1)


def estimate_compliance_score(row: pd.Series) -> float:
    risk = _risk_score(row.get("compliance_risk"))
    return round(clamp(100 - risk), 1)


def estimate_profit_score(row: pd.Series, assumptions: dict[str, float] | None = None) -> float:
    defaults = {
        "purchase_cost_ratio": 0.23,
        "package_cost_rmb": 0.6,
        "china_domestic_shipping_rmb": 0.5,
        "international_shipping_rmb": 1.2,
        "exchange_rate": 190.0,
        "coupang_fee_rate": 0.11,
        "fulfillment_fee_krw": 1200.0,
        "ad_cost_per_order_krw": 1000.0,
        "return_loss_rate": 0.03,
        "other_cost_krw": 500.0,
    }
    if assumptions:
        defaults.update(assumptions)

    price_krw = _safe_float(row.get("price"), 0.0)
    purchase_cost_rmb = (price_krw / defaults["exchange_rate"]) * defaults["purchase_cost_ratio"]

    result = calculate_profit(
        ProfitInput(
            purchase_cost_rmb=purchase_cost_rmb,
            package_cost_rmb=defaults["package_cost_rmb"],
            china_domestic_shipping_rmb=defaults["china_domestic_shipping_rmb"],
            international_shipping_rmb=defaults["international_shipping_rmb"],
            exchange_rate=defaults["exchange_rate"],
            coupang_price_krw=price_krw,
            coupang_fee_rate=defaults["coupang_fee_rate"],
            fulfillment_fee_krw=defaults["fulfillment_fee_krw"],
            ad_cost_per_order_krw=defaults["ad_cost_per_order_krw"],
            return_loss_rate=defaults["return_loss_rate"],
            other_cost_krw=defaults["other_cost_krw"],
            package_count=int(_safe_float(row.get("package_count"), 1)),
        )
    )

    margin_component = clamp(result["margin_rate"] * 220, 0, 55)
    profit_component = clamp(result["net_profit_krw"] / 120, 0, 30)
    ad_tolerance_component = clamp(result["max_allowed_ad_cost"] / 80, 0, 15)
    return round(clamp(margin_component + profit_component + ad_tolerance_component), 1)


def add_scores(df: pd.DataFrame, assumptions: dict[str, float] | None = None) -> pd.DataFrame:
    if df.empty:
        return df.copy()

    enriched = df.copy()
    enriched["competition_score"] = enriched.apply(lambda row: estimate_competition_score(row, enriched), axis=1)
    enriched["competition_level"] = enriched["competition_score"].apply(score_level_for_competition)
    enriched["demand_score"] = enriched.apply(estimate_demand_score, axis=1)
    enriched["demand_level"] = enriched["demand_score"].apply(score_level)
    enriched["differentiation_score"] = enriched.apply(estimate_differentiation_score, axis=1)
    enriched["profit_score"] = enriched.apply(lambda row: estimate_profit_score(row, assumptions), axis=1)
    enriched["logistics_score"] = enriched.apply(estimate_logistics_score, axis=1)
    enriched["compliance_score"] = enriched.apply(estimate_compliance_score, axis=1)
    enriched["product_opportunity_score"] = (
        enriched["demand_score"] * 0.25
        + (100 - enriched["competition_score"]) * 0.20
        + enriched["profit_score"] * 0.25
        + enriched["differentiation_score"] * 0.15
        + enriched["logistics_score"] * 0.10
        + enriched["compliance_score"] * 0.05
    ).round(1)
    enriched["recommendation"] = enriched["product_opportunity_score"].apply(score_recommendation)
    enriched["should_enter"] = enriched["competition_score"].apply(lambda score: "否" if score >= 78 else "是")
    return enriched


def score_level(score: float) -> str:
    if score >= 75:
        return "高"
    if score >= 50:
        return "中"
    return "低"


def score_level_for_competition(score: float) -> str:
    if score >= 85:
        return "极高"
    if score >= 70:
        return "高"
    if score >= 45:
        return "中"
    return "低"


def score_recommendation(score: float) -> str:
    if score >= 80:
        return "强烈建议测试"
    if score >= 68:
        return "可以小批量测试"
    if score >= 55:
        return "谨慎测试"
    return "不建议进入"


def price_analysis(df: pd.DataFrame) -> dict[str, Any]:
    if df.empty:
        return {}

    avg_price = df["price"].fillna(0).mean()
    avg_unit = df["unit_price"].fillna(0).mean()
    min_price = df["price"].fillna(0).min()
    max_price = df["price"].fillna(0).max()
    price_gap_ratio = ((max_price - min_price) / avg_price) if avg_price else 0.0

    low_band = avg_price * 0.92
    high_band = avg_price * 1.08

    if price_gap_ratio < 0.18:
        risk = "高"
    elif price_gap_ratio < 0.35:
        risk = "中"
    else:
        risk = "低"

    return {
        "average_price": round(avg_price, 1),
        "lowest_price": round(min_price, 1),
        "highest_price": round(max_price, 1),
        "average_unit_price": round(avg_unit, 1),
        "recommended_price_range": f"{low_band:,.0f} - {high_band:,.0f} KRW",
        "price_war_risk": risk,
    }


def summarize_opportunities(df: pd.DataFrame) -> list[str]:
    text = " ".join(
        df[column].fillna("").astype(str).str.lower().str.cat(sep=" ")
        for column in ["weak_points", "bad_review_points", "differentiation_opportunity"]
        if column in df.columns
    )
    keywords = {
        "size": "补充更清晰的韩文尺码图，并增加腰围/臀围对应说明。",
        "hot": "强化透气、冰丝、夏季舒适感等卖点表达。",
        "wash": "加入洗护说明，或与文胸洗衣袋做组合销售。",
        "cheap": "提升包装和视觉质感，增强礼品感与信任感。",
        "color": "推出更稳妥的基础色组合，如黑色、肤色、米色套装。",
        "strap": "突出防滑夹稳定性和佩戴场景说明。",
        "deform": "增加洗后不易变形的说明和使用证明图。",
    }

    suggestions = [message for token, message in keywords.items() if token in text]
    if not suggestions:
        suggestions = [
            "优化白底主图，让产品占比更大、视觉更干净。",
            "加强韩语 SEO 标题结构，用核心词 + 痛点词组合。",
            "增加 3 件装 / 6 件装组合，提高客单价。",
        ]
    return suggestions[:5]


def extract_issue_terms(df: pd.DataFrame, top_n: int = 10) -> list[tuple[str, int]]:
    combined = " ".join(
        df[column].fillna("").astype(str).str.lower().str.cat(sep=" ")
        for column in ["bad_review_points", "weak_points", "qna_points"]
        if column in df.columns
    )
    tokens = [
        token.strip(" ,./")
        for token in combined.replace("/", " ").replace(",", " ").split()
        if len(token.strip(" ,./")) >= 3
    ]
    stop_words = {"and", "the", "with", "for", "too", "very", "size", "good"}
    filtered = [token for token in tokens if token not in stop_words]
    return Counter(filtered).most_common(top_n)
