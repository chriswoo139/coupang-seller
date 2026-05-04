from __future__ import annotations

from datetime import datetime
from typing import Any

import pandas as pd


COMPETITOR_FIELDS = [
    "product_url",
    "product_name",
    "brand_name",
    "category",
    "product_type",
    "main_keyword",
    "sub_keywords",
    "price",
    "package_count",
    "unit_price",
    "rocket_type",
    "review_count",
    "rating",
    "image_count",
    "option_count",
    "coupon_or_discount",
    "seller_count",
    "rank_position",
    "estimated_sales_level",
    "title_keywords",
    "image_style",
    "main_selling_points",
    "weak_points",
    "bad_review_points",
    "qna_points",
    "differentiation_opportunity",
    "compliance_risk",
    "return_risk",
    "created_at",
    "updated_at",
]

NUMERIC_FIELDS = {
    "price",
    "unit_price",
    "review_count",
    "rating",
    "image_count",
    "option_count",
    "seller_count",
    "rank_position",
}

TEXT_FIELDS = [field for field in COMPETITOR_FIELDS if field not in NUMERIC_FIELDS]

DEFAULT_VALUES = {
    "brand_name": "No Brand",
    "category": "Women's Underwear & Accessories",
    "rocket_type": "Unknown",
    "estimated_sales_level": "Medium",
    "image_style": "White background",
    "coupon_or_discount": "No",
    "compliance_risk": "Low",
    "return_risk": "Medium",
}


def now_string() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def coerce_numeric(value: Any) -> float | None:
    if value is None or value == "":
        return None
    if isinstance(value, (int, float)):
        return float(value)

    cleaned = str(value).replace(",", "").replace("KRW", "").replace("₩", "").strip()
    if not cleaned:
        return None
    try:
        return float(cleaned)
    except ValueError:
        return None


def parse_package_count(value: Any) -> int:
    if value is None or value == "":
        return 1
    if isinstance(value, (int, float)):
        return max(int(value), 1)

    digits = "".join(char for char in str(value) if char.isdigit())
    return max(int(digits), 1) if digits else 1


def calculate_unit_price(price: Any, package_count: Any) -> float | None:
    numeric_price = coerce_numeric(price)
    qty = parse_package_count(package_count)
    if numeric_price is None or qty <= 0:
        return None
    return round(numeric_price / qty, 2)


def normalize_record(record: dict[str, Any]) -> dict[str, Any]:
    normalized: dict[str, Any] = {}
    timestamp = now_string()

    for field in COMPETITOR_FIELDS:
        value = record.get(field)

        if field in NUMERIC_FIELDS:
            normalized[field] = coerce_numeric(value)
            continue

        if field == "created_at":
            normalized[field] = value or timestamp
            continue

        if field == "updated_at":
            normalized[field] = timestamp
            continue

        normalized[field] = str(value).strip() if value not in (None, "") else DEFAULT_VALUES.get(field, "")

    package_count = record.get("package_count", normalized.get("package_count", 1))
    normalized["package_count"] = parse_package_count(package_count)
    normalized["unit_price"] = calculate_unit_price(
        normalized.get("price"), normalized.get("package_count")
    )

    if not normalized["product_name"]:
        normalized["product_name"] = normalized.get("main_keyword", "Unnamed Product")

    if not normalized["product_type"]:
        normalized["product_type"] = normalized.get("category", "Unknown")

    return normalized


def normalize_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame(columns=COMPETITOR_FIELDS)

    working = df.copy()
    renamed_columns = {column: column.strip() for column in working.columns}
    working.rename(columns=renamed_columns, inplace=True)

    for field in COMPETITOR_FIELDS:
        if field not in working.columns:
            working[field] = None

    records = [normalize_record(row) for row in working.to_dict(orient="records")]
    return pd.DataFrame(records, columns=COMPETITOR_FIELDS)


def competitor_template_frame() -> pd.DataFrame:
    return pd.DataFrame(columns=COMPETITOR_FIELDS)

