from __future__ import annotations

import hashlib
import hmac
import os
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

import requests


COUPANG_API_BASE = "https://api-gateway.coupang.com"


@dataclass
class CoupangOpenApiConfig:
    access_key: str = ""
    secret_key: str = ""
    vendor_id: str = ""
    market: str = "KR"

    @classmethod
    def from_env(cls) -> "CoupangOpenApiConfig":
        return cls(
            access_key=os.getenv("COUPANG_ACCESS_KEY", "").strip(),
            secret_key=os.getenv("COUPANG_SECRET_KEY", "").strip(),
            vendor_id=os.getenv("COUPANG_VENDOR_ID", "").strip(),
            market=os.getenv("COUPANG_MARKET", "KR").strip() or "KR",
        )

    def credentials_ready(self) -> bool:
        return all([self.access_key, self.secret_key, self.vendor_id])


class CoupangOpenApiClient:
    """仅用于自有店铺流程的官方 Coupang Open API 辅助客户端。"""

    def __init__(self, config: CoupangOpenApiConfig | None = None) -> None:
        self.config = config or CoupangOpenApiConfig.from_env()

    def credential_status(self) -> dict[str, Any]:
        return {
            "market": self.config.market,
            "access_key_configured": bool(self.config.access_key),
            "secret_key_configured": bool(self.config.secret_key),
            "vendor_id_configured": bool(self.config.vendor_id),
            "ready": self.config.credentials_ready(),
            "usage_boundary": "仅限你自己的店铺数据、商品注册、类目查询与同步流程，不可用于竞品采集。",
        }

    def build_authorization(
        self,
        method: str,
        path: str,
        query: str = "",
    ) -> dict[str, str]:
        if not self.config.access_key or not self.config.secret_key:
            raise ValueError("当前尚未配置 Coupang Open API 凭证。")

        method = method.upper()
        timestamp = datetime.now(timezone.utc).strftime("%y%m%dT%H%M%SZ")
        message = f"{timestamp}{method}{path}{query}"
        signature = hmac.new(
            self.config.secret_key.encode("utf-8"),
            message.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()
        authorization = (
            f"CEA algorithm=HmacSHA256, access-key={self.config.access_key}, "
            f"signed-date={timestamp}, signature={signature}"
        )
        return {
            "Authorization": authorization,
            "Content-Type": "application/json;charset=UTF-8",
        }

    def sign_preview(self, method: str, path: str, query: str = "") -> dict[str, Any]:
        headers = self.build_authorization(method=method, path=path, query=query)
        return {
            "method": method.upper(),
            "path": path,
            "query": query,
            "headers": headers,
        }

    def get_category_meta(self, display_category_code: str) -> dict[str, Any]:
        path = f"/v2/providers/seller_api/apis/api/v1/marketplace/meta/display-categories/{display_category_code}"
        headers = self.build_authorization("GET", path)
        response = requests.get(f"{COUPANG_API_BASE}{path}", headers=headers, timeout=20)
        response.raise_for_status()
        return response.json()

    def get_vendor_items(self, limit: int = 20) -> dict[str, Any]:
        path = "/v2/providers/openapi/apis/api/v4/vendors/products"
        query = f"?nextToken=&maxPerPage={limit}"
        headers = self.build_authorization("GET", path, query=query)
        response = requests.get(f"{COUPANG_API_BASE}{path}{query}", headers=headers, timeout=20)
        response.raise_for_status()
        return response.json()
