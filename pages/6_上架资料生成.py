from __future__ import annotations

import streamlit as st

from modules.database import fetch_all_competitors, init_db
from modules.keyword_generator import generate_keywords
from modules.title_generator import generate_detail_structure, generate_titles


init_db()
st.title("上架资料生成")

df = fetch_all_competitors()
if df.empty:
    st.warning("当前没有可用的竞品数据。")
    st.stop()

product_names = df["product_name"].tolist()
selected_name = st.selectbox("选择一个产品记录", product_names)
selected_row = df[df["product_name"] == selected_name].iloc[0].to_dict()

st.subheader("产品上下文")
st.json(
    {
        "product_type": selected_row.get("product_type"),
        "main_keyword": selected_row.get("main_keyword"),
        "sub_keywords": selected_row.get("sub_keywords"),
        "main_selling_points": selected_row.get("main_selling_points"),
        "weak_points": selected_row.get("weak_points"),
    }
)

titles = generate_titles(selected_row)
keywords = generate_keywords(selected_row)
detail = generate_detail_structure(selected_row)

st.subheader("5 个韩语标题版本")
labels = [
    "SEO 强版本",
    "高转化版本",
    "自然简洁版",
    "低价引流版",
    "高客单套装版",
]
for label, title in zip(labels, titles):
    st.write(f"- {label}: {title}")

st.subheader("广告关键词建议")
st.write("手动广告关键词")
st.write(", ".join(keywords["manual_ad_keywords"]))
st.write("自动种子词")
st.write(", ".join(keywords["auto_ad_seed_keywords"]))
st.write("否定关键词")
st.write(", ".join(keywords["negative_keywords"]))
st.write("标题关键词")
st.write(", ".join(keywords["title_keywords"]))
st.write("详情页关键词")
st.write(", ".join(keywords["detail_page_keywords"]))

st.subheader("详情页结构建议")
st.write(f"- 主图：{detail['main_image']}")
st.write(f"- 第 2 张图：{detail['image_2']}")
st.write(f"- 第 3 张图：{detail['image_3']}")
st.write(f"- 第 4 张图：{detail['image_4']}")
st.write(f"- 第 5 张图：{detail['image_5']}")
st.write(f"- 尺码图：{detail['size_chart']}")
st.write(f"- 材质说明：{detail['material_note']}")
st.write(f"- 洗护说明：{detail['wash_care_note']}")

st.write("FAQ")
for item in detail["faq"]:
    st.write(f"- {item}")

st.write("韩语卖点文案")
for item in detail["korean_selling_points"]:
    st.write(f"- {item}")

st.caption(f"风险提醒：{detail['risk_watchouts']}")
