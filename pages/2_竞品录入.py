from __future__ import annotations

from pathlib import Path

import pandas as pd
import streamlit as st

from modules.competitor_model import COMPETITOR_FIELDS, normalize_dataframe
from modules.database import bulk_insert, fetch_all_competitors, init_db, insert_competitor
from modules.text_parser import parse_competitor_text


PROJECT_ROOT = Path(__file__).resolve().parents[1]
init_db()

st.title("竞品录入")

tab1, tab2, tab3, tab4 = st.tabs(["手动表单", "上传 CSV/Excel", "粘贴页面文本", "当前数据"])

with tab1:
    st.subheader("手动录入")
    with st.form("competitor_form"):
        col1, col2, col3 = st.columns(3)
        product_url = col1.text_input("竞品链接（product_url）")
        product_name = col2.text_input("商品名（product_name）")
        brand_name = col3.text_input("品牌名（brand_name）", value="No Brand")

        col4, col5, col6 = st.columns(3)
        category = col4.text_input("类目（category）", value="Women's Underwear & Accessories")
        product_type = col5.text_input("产品类型（product_type）", value="seamless panty")
        main_keyword = col6.text_input("主关键词（main_keyword）", value="women panty")

        col7, col8, col9 = st.columns(3)
        sub_keywords = col7.text_input("副关键词（sub_keywords）", value="no line panty, daily panty")
        price = col8.number_input("售价（price，KRW）", min_value=0.0, step=100.0, value=8900.0)
        package_count = col9.number_input("件数（package_count）", min_value=1, step=1, value=3)

        col10, col11, col12 = st.columns(3)
        rocket_type = col10.selectbox("配送类型（rocket_type）", ["Unknown", "Rocket", "Rocket Growth", "Seller Shipping"])
        review_count = col11.number_input("评价数（review_count）", min_value=0.0, step=1.0, value=120.0)
        rating = col12.number_input("评分（rating）", min_value=0.0, max_value=5.0, step=0.1, value=4.5)

        col13, col14, col15 = st.columns(3)
        image_count = col13.number_input("图片数（image_count）", min_value=0.0, step=1.0, value=5.0)
        option_count = col14.number_input("规格数（option_count）", min_value=0.0, step=1.0, value=3.0)
        coupon_or_discount = col15.selectbox("是否有优惠（coupon_or_discount）", ["No", "Yes"])

        col16, col17, col18 = st.columns(3)
        seller_count = col16.number_input("同款卖家数（seller_count）", min_value=0.0, step=1.0, value=1.0)
        rank_position = col17.number_input("关键词排名（rank_position）", min_value=0.0, step=1.0, value=10.0)
        estimated_sales_level = col18.selectbox("预估销量等级（estimated_sales_level）", ["Low", "Medium", "High"])

        title_keywords = st.text_input("标题关键词（title_keywords）", value="women panty, seamless, no line")
        image_style = st.text_input("主图风格（image_style）", value="White background, product-focused")
        main_selling_points = st.text_area("主要卖点（main_selling_points）", value="seamless, breathable, daily wear, soft touch")
        weak_points = st.text_area("竞品弱点（weak_points）", value="size unclear, color options limited")
        bad_review_points = st.text_area("差评集中点（bad_review_points）", value="size runs small, thin fabric")
        qna_points = st.text_area("问答关注点（qna_points）", value="is it breathable, is the size accurate")
        differentiation_opportunity = st.text_area(
            "差异化机会（differentiation_opportunity）",
            value="clearer size chart, cooler fabric message, 3-pack neutral colors",
        )
        compliance_risk = st.selectbox("合规风险（compliance_risk）", ["Low", "Medium", "High"])
        return_risk = st.selectbox("退货风险（return_risk）", ["Low", "Medium", "High"])

        submitted = st.form_submit_button("添加竞品")

    if submitted:
        insert_competitor(
            {
                "product_url": product_url,
                "product_name": product_name,
                "brand_name": brand_name,
                "category": category,
                "product_type": product_type,
                "main_keyword": main_keyword,
                "sub_keywords": sub_keywords,
                "price": price,
                "package_count": package_count,
                "rocket_type": rocket_type,
                "review_count": review_count,
                "rating": rating,
                "image_count": image_count,
                "option_count": option_count,
                "coupon_or_discount": coupon_or_discount,
                "seller_count": seller_count,
                "rank_position": rank_position,
                "estimated_sales_level": estimated_sales_level,
                "title_keywords": title_keywords,
                "image_style": image_style,
                "main_selling_points": main_selling_points,
                "weak_points": weak_points,
                "bad_review_points": bad_review_points,
                "qna_points": qna_points,
                "differentiation_opportunity": differentiation_opportunity,
                "compliance_risk": compliance_risk,
                "return_risk": return_risk,
            }
        )
        st.success("竞品记录已添加。")

with tab2:
    st.subheader("上传 CSV 或 Excel")
    uploaded = st.file_uploader("上传文件", type=["csv", "xlsx"])
    st.caption(f"模板路径：{PROJECT_ROOT / 'data' / 'competitors_template.xlsx'}")

    if uploaded is not None:
        if uploaded.name.lower().endswith(".csv"):
            upload_df = pd.read_csv(uploaded)
        else:
            upload_df = pd.read_excel(uploaded)

        normalized = normalize_dataframe(upload_df)
        st.dataframe(normalized.head(10), use_container_width=True)
        if st.button("导入上传数据"):
            inserted = bulk_insert(normalized)
            st.success(f"已导入 {inserted} 行数据。")

with tab3:
    st.subheader("粘贴 Coupang 页面文本")
    pasted_text = st.text_area(
        "请粘贴页面可见文本",
        height=220,
        placeholder="请粘贴商品标题、价格、评分、评价数以及页面可见卖点文本。",
    )
    if st.button("解析文本"):
        parsed = parse_competitor_text(pasted_text)
        if parsed:
            st.session_state["parsed_preview"] = normalize_dataframe(pd.DataFrame([parsed]))
        else:
            st.warning("未识别到结构化数据。")

    parsed_preview = st.session_state.get("parsed_preview")
    if parsed_preview is not None and not parsed_preview.empty:
        st.dataframe(parsed_preview, use_container_width=True)
        if st.button("保存解析结果"):
            bulk_insert(parsed_preview)
            st.success("解析后的记录已保存。")
            st.session_state.pop("parsed_preview", None)

with tab4:
    st.subheader("当前竞品数据")
    current = fetch_all_competitors()
    st.dataframe(
        current[["product_name", "product_type", "price", "review_count", "rating", "updated_at"]],
        use_container_width=True,
    )
    st.download_button(
        "下载模板字段 CSV",
        data=",".join(COMPETITOR_FIELDS),
        file_name="competitors_template_columns.csv",
        mime="text/csv",
    )
