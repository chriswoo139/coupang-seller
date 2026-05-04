from __future__ import annotations

import streamlit as st

from modules.coupang_api import CoupangOpenApiClient


st.title("Coupang Open API 准备状态")
st.caption("本页面仅用于你自己的店铺操作，不用于竞品采集。")

client = CoupangOpenApiClient()
status = client.credential_status()

col1, col2, col3, col4 = st.columns(4)
col1.metric("市场", status["market"])
col2.metric("Access Key", "已配置" if status["access_key_configured"] else "未配置")
col3.metric("Secret Key", "已配置" if status["secret_key_configured"] else "未配置")
col4.metric("Vendor ID", "已配置" if status["vendor_id_configured"] else "未配置")

st.info(status["usage_boundary"])

st.subheader("需要配置的环境变量")
st.code(
    "COUPANG_ACCESS_KEY=your_access_key\n"
    "COUPANG_SECRET_KEY=your_secret_key\n"
    "COUPANG_VENDOR_ID=your_vendor_id\n"
    "COUPANG_MARKET=KR",
    language="bash",
)

st.subheader("签名预览")
method = st.selectbox("请求方法", ["GET", "POST", "PUT"])
path = st.text_input(
    "API 路径",
    value="/v2/providers/seller_api/apis/api/v1/marketplace/meta/display-categories/0",
)
query = st.text_input("Query 参数字符串", value="")

if st.button("生成签名预览"):
    try:
        preview = client.sign_preview(method=method, path=path, query=query)
        st.json(preview)
    except ValueError as exc:
        st.error(str(exc))
