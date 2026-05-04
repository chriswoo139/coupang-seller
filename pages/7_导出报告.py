from __future__ import annotations

import streamlit as st

from modules.database import fetch_all_competitors, init_db
from modules.report_generator import dataframe_to_excel_bytes, dataframe_to_markdown


init_db()
st.title("导出报告")

df = fetch_all_competitors()
if df.empty:
    st.warning("当前没有可导出的数据。")
    st.stop()

excel_bytes = dataframe_to_excel_bytes(df)
csv_bytes = df.to_csv(index=False).encode("utf-8-sig")
markdown_text = dataframe_to_markdown(df)

st.download_button(
    "下载 Excel 报告",
    data=excel_bytes,
    file_name="coupang_competitor_report.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
)
st.download_button(
    "下载 CSV",
    data=csv_bytes,
    file_name="coupang_competitors.csv",
    mime="text/csv",
)
st.download_button(
    "下载 Markdown 报告",
    data=markdown_text,
    file_name="coupang_competitor_report.md",
    mime="text/markdown",
)

st.subheader("Markdown 预览")
st.code(markdown_text, language="markdown")
