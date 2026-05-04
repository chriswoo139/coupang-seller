from __future__ import annotations

import streamlit as st

from modules.database import fetch_all_competitors, init_db
from modules.scoring import add_scores


init_db()
st.title("选品评分")

with st.sidebar:
    st.subheader("利润假设参数")
    purchase_cost_ratio = st.slider("采购成本占比", 0.05, 0.5, 0.23, 0.01)
    fulfillment_fee_krw = st.number_input("履约费用", min_value=0.0, value=1200.0, step=50.0)
    ad_cost_per_order_krw = st.number_input("单单广告成本", min_value=0.0, value=1000.0, step=100.0)
    return_loss_rate = st.slider("退货损耗比例", 0.0, 0.2, 0.03, 0.01)

df = fetch_all_competitors()
if df.empty:
    st.warning("当前还没有竞品记录。")
    st.stop()

scored = add_scores(
    df,
    assumptions={
        "purchase_cost_ratio": purchase_cost_ratio,
        "fulfillment_fee_krw": fulfillment_fee_krw,
        "ad_cost_per_order_krw": ad_cost_per_order_krw,
        "return_loss_rate": return_loss_rate,
    },
)

sort_by = st.selectbox(
    "排序方式",
    ["product_opportunity_score", "profit_score", "competition_score", "demand_score"],
)
ascending = sort_by == "competition_score"
display = scored.sort_values(sort_by, ascending=ascending)

st.dataframe(
    display[
        [
            "product_name",
            "product_type",
            "price",
            "competition_score",
            "demand_score",
            "profit_score",
            "differentiation_score",
            "logistics_score",
            "compliance_score",
            "product_opportunity_score",
            "recommendation",
        ]
    ],
    use_container_width=True,
)

st.subheader("建议分布")
for recommendation in ["强烈建议测试", "可以小批量测试", "谨慎测试", "不建议进入"]:
    subset = display[display["recommendation"] == recommendation]
    st.write(f"- {recommendation}: {len(subset)} 个产品")
