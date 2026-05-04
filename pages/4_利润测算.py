from __future__ import annotations

import plotly.express as px
import streamlit as st

from modules.database import fetch_all_competitors, fetch_profit_history, init_db, insert_profit_calculation
from modules.profit_calculator import ProfitInput, calculate_profit, profit_input_to_dict, scenario_table


init_db()
st.title("利润测算")

competitors = fetch_all_competitors()
competitor_options = {"手动输入": None}
for _, row in competitors.iterrows():
    label = f"#{int(row['id'])} | {row['product_name']} | {row['product_type']}"
    competitor_options[label] = int(row["id"])

selected_label = st.selectbox("将本次测算关联到某个竞品记录", list(competitor_options.keys()))
selected_competitor_id = competitor_options[selected_label]
selected_competitor = None
default_price = 8900.0
default_package_count = 3

if selected_competitor_id is not None:
    selected_competitor = competitors[competitors["id"] == selected_competitor_id].iloc[0]
    default_price = float(selected_competitor["price"] or default_price)
    default_package_count = int(selected_competitor["package_count"] or default_package_count)

with st.form("profit_form"):
    scenario_name = st.text_input(
        "方案名称（scenario_name）",
        value="手动测算方案" if selected_competitor is None else f"{selected_competitor['product_name']} 测算方案",
    )
    col1, col2, col3 = st.columns(3)
    purchase_cost_rmb = col1.number_input("采购成本（purchase_cost_rmb）", min_value=0.0, value=2.8, step=0.1)
    package_cost_rmb = col2.number_input("包装成本（package_cost_rmb）", min_value=0.0, value=0.6, step=0.1)
    china_domestic_shipping_rmb = col3.number_input(
        "国内运费（china_domestic_shipping_rmb）", min_value=0.0, value=0.5, step=0.1
    )

    col4, col5, col6 = st.columns(3)
    international_shipping_rmb = col4.number_input(
        "国际物流（international_shipping_rmb）", min_value=0.0, value=1.3, step=0.1
    )
    exchange_rate = col5.number_input("汇率（exchange_rate）", min_value=1.0, value=190.0, step=1.0)
    coupang_price_krw = col6.number_input(
        "Coupang 售价（coupang_price_krw）", min_value=0.0, value=default_price, step=100.0
    )

    col7, col8, col9 = st.columns(3)
    coupang_fee_rate = col7.number_input("平台佣金比例（coupang_fee_rate）", min_value=0.0, max_value=1.0, value=0.11, step=0.01)
    fulfillment_fee_krw = col8.number_input("履约费用（fulfillment_fee_krw）", min_value=0.0, value=1200.0, step=50.0)
    ad_cost_per_order_krw = col9.number_input("单单广告成本（ad_cost_per_order_krw）", min_value=0.0, value=1000.0, step=100.0)

    col10, col11, col12 = st.columns(3)
    return_loss_rate = col10.number_input("退货损耗比例（return_loss_rate）", min_value=0.0, max_value=1.0, value=0.03, step=0.01)
    other_cost_krw = col11.number_input("其他成本（other_cost_krw）", min_value=0.0, value=500.0, step=50.0)
    package_count = col12.selectbox(
        "基础件数（package_count）",
        [1, 2, 3, 6],
        index=[1, 2, 3, 6].index(default_package_count) if default_package_count in [1, 2, 3, 6] else 2,
    )

    save_result = st.checkbox("保存到历史记录", value=True)
    submitted = st.form_submit_button("开始计算")

if submitted:
    base_inputs = ProfitInput(
        purchase_cost_rmb=purchase_cost_rmb,
        package_cost_rmb=package_cost_rmb,
        china_domestic_shipping_rmb=china_domestic_shipping_rmb,
        international_shipping_rmb=international_shipping_rmb,
        exchange_rate=exchange_rate,
        coupang_price_krw=coupang_price_krw,
        coupang_fee_rate=coupang_fee_rate,
        fulfillment_fee_krw=fulfillment_fee_krw,
        ad_cost_per_order_krw=ad_cost_per_order_krw,
        return_loss_rate=return_loss_rate,
        other_cost_krw=other_cost_krw,
        package_count=package_count,
    )
    result = calculate_profit(base_inputs)
    product_name = "" if selected_competitor is None else str(selected_competitor["product_name"])

    if save_result:
        record_id = insert_profit_calculation(
            payload=profit_input_to_dict(base_inputs),
            result=result,
            competitor_id=selected_competitor_id,
            scenario_name=scenario_name,
            product_name=product_name,
        )
        st.success(f"利润测算已保存，记录 ID：{record_id}")

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("总成本", f"{result['total_cost_krw']:,.0f} KRW")
    col2.metric("毛利润", f"{result['gross_profit_krw']:,.0f} KRW")
    col3.metric("净利润", f"{result['net_profit_krw']:,.0f} KRW")
    col4.metric("利润率", f"{result['margin_rate'] * 100:.1f}%")

    col5, col6, col7, col8 = st.columns(4)
    col5.metric("盈亏平衡 ROAS", result["break_even_roas"])
    col6.metric("可承受广告上限", f"{result['max_allowed_ad_cost']:,.0f} KRW")
    col7.metric("安全售价区间", result["safe_price_range"])
    col8.metric("是否适合低价引流", result["fit_for_low_price_strategy"])

    st.caption(f"多件装适配性：{result['fit_for_multi_pack']}")

    scenarios = scenario_table(base_inputs)
    st.subheader("1 / 2 / 3 / 6 件装对比")
    st.dataframe(scenarios, use_container_width=True)

    margin_chart = px.bar(
        scenarios,
        x="package_count",
        y="margin_rate",
        title="不同件数下的利润率对比",
        text_auto=".1%",
    )
    st.plotly_chart(margin_chart, use_container_width=True)

st.subheader("最近利润历史")
history = fetch_profit_history(limit=20)
if history.empty:
    st.caption("当前还没有保存的利润测算记录。")
else:
    st.dataframe(
        history[
            [
                "id",
                "scenario_name",
                "product_name",
                "package_count",
                "coupang_price_krw",
                "net_profit_krw",
                "margin_rate",
                "break_even_roas",
                "created_at",
            ]
        ],
        use_container_width=True,
    )
