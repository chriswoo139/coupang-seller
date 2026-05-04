from __future__ import annotations

from pathlib import Path

import streamlit as st

from modules.database import fetch_all_competitors, init_db, seed_sample_data_if_empty
from modules.scoring import add_scores


init_db()
seed_sample_data_if_empty(Path(__file__).resolve().parents[1] / "data" / "sample_competitors.csv")

st.title("首页看板")

df = fetch_all_competitors()
scored = add_scores(df)

if scored.empty:
    st.warning("当前还没有竞品记录。")
    st.stop()

high_opportunity = scored[scored["product_opportunity_score"] >= 75]
avg_margin_proxy = scored["profit_score"].mean() / 100 * 35

col1, col2, col3, col4 = st.columns(4)
col1.metric("竞品总数", len(scored))
col2.metric("候选产品类型", scored["product_type"].nunique())
col3.metric("高机会产品数", len(high_opportunity))
col4.metric("平均利润率参考", f"{avg_margin_proxy:.1f}%")

st.subheader("TOP 10 推荐产品")
top_10 = scored.sort_values("product_opportunity_score", ascending=False).head(10)
st.dataframe(
    top_10[
        [
            "product_name",
            "product_type",
            "price",
            "review_count",
            "competition_score",
            "demand_score",
            "product_opportunity_score",
            "recommendation",
        ]
    ],
    use_container_width=True,
)

st.subheader("类目快照")
snapshot = (
    scored.groupby("product_type", dropna=False)
    .agg(
        competitor_count=("id", "count"),
        avg_price=("price", "mean"),
        avg_score=("product_opportunity_score", "mean"),
    )
    .reset_index()
    .sort_values("avg_score", ascending=False)
)
st.dataframe(snapshot, use_container_width=True)
