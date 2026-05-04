from __future__ import annotations

import plotly.express as px
import streamlit as st

from modules.database import fetch_all_competitors, fetch_product_types, init_db
from modules.scoring import add_scores, extract_issue_terms, price_analysis, summarize_opportunities


init_db()
st.title("竞品分析")

all_df = fetch_all_competitors()
product_types = fetch_product_types()

if all_df.empty:
    st.warning("当前没有可用的竞品数据。")
    st.stop()

selected_type = st.selectbox("选择产品类型", product_types)
filtered = all_df[all_df["product_type"] == selected_type].copy()
scored = add_scores(filtered)
price_stats = price_analysis(scored)

col1, col2, col3 = st.columns(3)
col1.metric("平均售价", f"{price_stats['average_price']:,.0f} KRW")
col2.metric("平均单件价", f"{price_stats['average_unit_price']:,.0f} KRW")
col3.metric("价格战风险", price_stats["price_war_risk"])

col4, col5, col6 = st.columns(3)
col4.metric("最低价", f"{price_stats['lowest_price']:,.0f} KRW")
col5.metric("最高价", f"{price_stats['highest_price']:,.0f} KRW")
col6.metric("建议区间", price_stats["recommended_price_range"])

chart_col1, chart_col2 = st.columns(2)

with chart_col1:
    fig_price = px.histogram(scored, x="price", nbins=12, title="价格分布")
    st.plotly_chart(fig_price, use_container_width=True)

with chart_col2:
    fig_review = px.histogram(scored, x="review_count", nbins=12, title="评价数量分布")
    st.plotly_chart(fig_review, use_container_width=True)

st.subheader("竞争概览")
st.dataframe(
    scored[
        [
            "product_name",
            "price",
            "review_count",
            "rating",
            "competition_score",
            "competition_level",
            "demand_score",
            "differentiation_score",
            "should_enter",
        ]
    ].sort_values("competition_score", ascending=False),
    use_container_width=True,
)

st.subheader("痛点词统计")
issue_terms = extract_issue_terms(scored)
if issue_terms:
    st.table({"痛点词": [term for term, _ in issue_terms], "次数": [count for _, count in issue_terms]})
else:
    st.info("当前评论/弱点文本不足，暂时无法提取痛点词。")

st.subheader("差异化建议")
for suggestion in summarize_opportunities(scored):
    st.write(f"- {suggestion}")
