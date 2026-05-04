from __future__ import annotations

import os
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Iterable

import pandas as pd

from .competitor_model import COMPETITOR_FIELDS, normalize_dataframe, normalize_record


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"


def resolve_db_path() -> Path:
    override = os.getenv("DATABASE_PATH", "").strip()
    if override:
        return Path(override).expanduser()
    if os.getenv("VERCEL") or os.getenv("VERCEL_ENV"):
        return Path("/tmp/competitors.db")
    return DATA_DIR / "competitors.db"


DB_PATH = resolve_db_path()

TABLE_SQL = """
CREATE TABLE IF NOT EXISTS competitors (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_url TEXT,
    product_name TEXT,
    brand_name TEXT,
    category TEXT,
    product_type TEXT,
    main_keyword TEXT,
    sub_keywords TEXT,
    price REAL,
    package_count INTEGER,
    unit_price REAL,
    rocket_type TEXT,
    review_count REAL,
    rating REAL,
    image_count REAL,
    option_count REAL,
    coupon_or_discount TEXT,
    seller_count REAL,
    rank_position REAL,
    estimated_sales_level TEXT,
    title_keywords TEXT,
    image_style TEXT,
    main_selling_points TEXT,
    weak_points TEXT,
    bad_review_points TEXT,
    qna_points TEXT,
    differentiation_opportunity TEXT,
    compliance_risk TEXT,
    return_risk TEXT,
    created_at TEXT,
    updated_at TEXT
)
"""

PROFIT_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS profit_calculations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    competitor_id INTEGER,
    scenario_name TEXT,
    product_name TEXT,
    package_count INTEGER,
    purchase_cost_rmb REAL,
    package_cost_rmb REAL,
    china_domestic_shipping_rmb REAL,
    international_shipping_rmb REAL,
    exchange_rate REAL,
    coupang_price_krw REAL,
    coupang_fee_rate REAL,
    fulfillment_fee_krw REAL,
    ad_cost_per_order_krw REAL,
    return_loss_rate REAL,
    other_cost_krw REAL,
    total_cost_krw REAL,
    gross_profit_krw REAL,
    net_profit_krw REAL,
    margin_rate REAL,
    break_even_roas REAL,
    max_allowed_ad_cost REAL,
    safe_price_range TEXT,
    fit_for_low_price_strategy TEXT,
    fit_for_multi_pack TEXT,
    created_at TEXT
)
"""


def get_connection() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def init_db() -> None:
    with get_connection() as connection:
        connection.execute(TABLE_SQL)
        connection.execute(PROFIT_TABLE_SQL)
        connection.commit()


def insert_competitor(record: dict) -> None:
    normalized = normalize_record(record)
    fields = ", ".join(COMPETITOR_FIELDS)
    placeholders = ", ".join(["?"] * len(COMPETITOR_FIELDS))
    sql = f"INSERT INTO competitors ({fields}) VALUES ({placeholders})"

    with get_connection() as connection:
        connection.execute(sql, [normalized[field] for field in COMPETITOR_FIELDS])
        connection.commit()


def bulk_insert(records: Iterable[dict] | pd.DataFrame) -> int:
    if isinstance(records, pd.DataFrame):
        df = normalize_dataframe(records)
    else:
        df = normalize_dataframe(pd.DataFrame(list(records)))

    if df.empty:
        return 0

    fields = ", ".join(COMPETITOR_FIELDS)
    placeholders = ", ".join(["?"] * len(COMPETITOR_FIELDS))
    sql = f"INSERT INTO competitors ({fields}) VALUES ({placeholders})"

    with get_connection() as connection:
        connection.executemany(
            sql,
            [[row[field] for field in COMPETITOR_FIELDS] for row in df.to_dict(orient="records")],
        )
        connection.commit()

    return len(df)


def fetch_all_competitors() -> pd.DataFrame:
    query = "SELECT * FROM competitors ORDER BY updated_at DESC, id DESC"
    with get_connection() as connection:
        df = pd.read_sql_query(query, connection)
    return df


def fetch_product_types() -> list[str]:
    df = fetch_all_competitors()
    if df.empty:
        return []
    return sorted(value for value in df["product_type"].dropna().astype(str).unique() if value)


def fetch_by_product_type(product_type: str) -> pd.DataFrame:
    query = "SELECT * FROM competitors WHERE product_type = ? ORDER BY updated_at DESC, id DESC"
    with get_connection() as connection:
        df = pd.read_sql_query(query, connection, params=[product_type])
    return df


def fetch_competitor_by_id(competitor_id: int) -> dict | None:
    query = "SELECT * FROM competitors WHERE id = ?"
    with get_connection() as connection:
        row = connection.execute(query, [competitor_id]).fetchone()
    return dict(row) if row else None


def insert_profit_calculation(
    payload: dict,
    result: dict,
    competitor_id: int | None = None,
    scenario_name: str | None = None,
    product_name: str | None = None,
) -> int:
    created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    sql = """
    INSERT INTO profit_calculations (
        competitor_id, scenario_name, product_name, package_count,
        purchase_cost_rmb, package_cost_rmb, china_domestic_shipping_rmb, international_shipping_rmb,
        exchange_rate, coupang_price_krw, coupang_fee_rate, fulfillment_fee_krw,
        ad_cost_per_order_krw, return_loss_rate, other_cost_krw,
        total_cost_krw, gross_profit_krw, net_profit_krw, margin_rate,
        break_even_roas, max_allowed_ad_cost, safe_price_range,
        fit_for_low_price_strategy, fit_for_multi_pack, created_at
    ) VALUES (
        ?, ?, ?, ?,
        ?, ?, ?, ?,
        ?, ?, ?, ?,
        ?, ?, ?,
        ?, ?, ?, ?,
        ?, ?, ?,
        ?, ?, ?
    )
    """
    values = [
        competitor_id,
        scenario_name or "Manual Scenario",
        product_name or "",
        payload.get("package_count"),
        payload.get("purchase_cost_rmb"),
        payload.get("package_cost_rmb"),
        payload.get("china_domestic_shipping_rmb"),
        payload.get("international_shipping_rmb"),
        payload.get("exchange_rate"),
        payload.get("coupang_price_krw"),
        payload.get("coupang_fee_rate"),
        payload.get("fulfillment_fee_krw"),
        payload.get("ad_cost_per_order_krw"),
        payload.get("return_loss_rate"),
        payload.get("other_cost_krw"),
        result.get("total_cost_krw"),
        result.get("gross_profit_krw"),
        result.get("net_profit_krw"),
        result.get("margin_rate"),
        result.get("break_even_roas"),
        result.get("max_allowed_ad_cost"),
        result.get("safe_price_range"),
        result.get("fit_for_low_price_strategy"),
        result.get("fit_for_multi_pack"),
        created_at,
    ]
    with get_connection() as connection:
        cursor = connection.execute(sql, values)
        connection.commit()
        return int(cursor.lastrowid)


def fetch_profit_history(limit: int = 50) -> pd.DataFrame:
    query = """
    SELECT *
    FROM profit_calculations
    ORDER BY created_at DESC, id DESC
    LIMIT ?
    """
    with get_connection() as connection:
        df = pd.read_sql_query(query, connection, params=[limit])
    return df


def seed_sample_data_if_empty(sample_csv_path: Path) -> None:
    existing = fetch_all_competitors()
    if not existing.empty or not sample_csv_path.exists():
        return

    sample_df = pd.read_csv(sample_csv_path)
    bulk_insert(sample_df)
