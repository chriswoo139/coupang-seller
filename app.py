from __future__ import annotations

from pathlib import Path

import streamlit as st

from modules.database import fetch_all_competitors, init_db, seed_sample_data_if_empty


PROJECT_ROOT = Path(__file__).resolve().parent


def bootstrap() -> None:
    init_db()
    seed_sample_data_if_empty(PROJECT_ROOT / "data" / "sample_competitors.csv")


def render_home() -> None:
    st.set_page_config(
        page_title="Coupang 选品研究工具",
        page_icon=":bar_chart:",
        layout="wide",
    )
    bootstrap()

    st.title("Coupang 选品研究工具 MVP")
    st.caption("适用于韩国 Coupang 女性内衣、洗护配件、文胸配件等类目的本地研究工具。")

    st.info(
        "本工具优先遵守合规要求：当前仅支持手动录入、文件导入和页面文本解析，"
        "不绕过登录、不抓取私有数据，也不会把 Coupang Open API 用于竞品采集。"
    )

    df = fetch_all_competitors()
    if df.empty:
        st.warning("当前还没有竞品数据，请先前往“竞品录入”页面添加数据。")
        return

    st.subheader("快速开始")
    col1, col2, col3 = st.columns(3)
    col1.metric("竞品记录数", len(df))
    col2.metric("产品类型数", df["product_type"].nunique())
    avg_price = float(df["price"].fillna(0).mean()) if "price" in df.columns else 0.0
    col3.metric("平均售价（KRW）", f"{avg_price:,.0f}")

    st.subheader("数据概览")
    preview_columns = [
        "product_name",
        "product_type",
        "main_keyword",
        "price",
        "review_count",
        "rating",
        "estimated_sales_level",
    ]
    st.dataframe(df[preview_columns].head(10), use_container_width=True)

    st.subheader("运行方式")
    st.code(
        "pip install -r requirements.txt\n"
        "streamlit run app.py",
        language="bash",
    )


if __name__ == "__main__":
    render_home()
