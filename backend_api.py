from __future__ import annotations

import os
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from modules.coupang_api import CoupangOpenApiClient
from modules.database import (
    DATA_DIR,
    fetch_all_competitors,
    fetch_competitor_by_id,
    fetch_profit_history,
    init_db,
    insert_profit_calculation,
    seed_sample_data_if_empty,
)
from modules.keyword_generator import generate_keywords
from modules.profit_calculator import ProfitInput, calculate_profit, scenario_table
from modules.scoring import add_scores, price_analysis, summarize_opportunities
from modules.title_generator import generate_detail_structure, generate_titles


app = FastAPI(
    title="Coupang 选品研究工具 API",
    version="0.3.0",
    description="用于选品研究、利润测算、自有店铺 Open API 准备和网页端展示的数据接口。",
)

init_db()
seed_sample_data_if_empty(DATA_DIR / "sample_competitors.csv")

default_origins = [
    "http://127.0.0.1:5173",
    "http://localhost:5173",
    "http://127.0.0.1:4173",
    "http://localhost:4173",
    "http://127.0.0.1:8501",
    "http://localhost:8501",
    "https://coupang-seller-tool.vercel.app",
    "https://frontend-three-khaki-40okns514r.vercel.app",
]
extra_origins = [origin.strip() for origin in os.getenv("ALLOWED_ORIGINS", "").split(",") if origin.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=default_origins + extra_origins,
    allow_origin_regex=r"https://.*\.vercel\.app",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def strip_api_prefix_for_serverless(request, call_next):
    if request.scope.get("path", "").startswith("/api/"):
        request.scope["path"] = request.scope["path"][4:]
    return await call_next(request)


class ProfitCalculationRequest(BaseModel):
    competitor_id: int | None = None
    scenario_name: str = "Manual Scenario"
    product_name: str = ""
    purchase_cost_rmb: float = Field(ge=0)
    package_cost_rmb: float = Field(ge=0)
    china_domestic_shipping_rmb: float = Field(ge=0)
    international_shipping_rmb: float = Field(ge=0)
    exchange_rate: float = Field(default=190, gt=0)
    coupang_price_krw: float = Field(ge=0)
    coupang_fee_rate: float = Field(default=0.11, ge=0, le=1)
    fulfillment_fee_krw: float = Field(default=0, ge=0)
    ad_cost_per_order_krw: float = Field(default=0, ge=0)
    return_loss_rate: float = Field(default=0.03, ge=0, le=1)
    other_cost_krw: float = Field(default=0, ge=0)
    package_count: int = Field(default=1, ge=1)


class SignPreviewRequest(BaseModel):
    method: str
    path: str
    query: str = ""


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/competitors")
def list_competitors() -> list[dict[str, Any]]:
    df = fetch_all_competitors()
    return df.fillna("").to_dict(orient="records")


@app.get("/competitors/scored")
def list_scored_competitors() -> list[dict[str, Any]]:
    df = add_scores(fetch_all_competitors())
    return df.fillna("").to_dict(orient="records")


@app.get("/competitors/{competitor_id}/analysis")
def competitor_analysis(competitor_id: int) -> dict[str, Any]:
    all_df = fetch_all_competitors()
    target = fetch_competitor_by_id(competitor_id)
    if not target:
        raise HTTPException(status_code=404, detail="未找到竞品记录")

    product_type = target["product_type"]
    scoped = add_scores(all_df[all_df["product_type"] == product_type].copy())
    target_df = scoped[scoped["id"] == competitor_id]
    if target_df.empty:
        raise HTTPException(status_code=404, detail="当前竞品暂无分析结果")

    return {
        "competitor": target_df.fillna("").iloc[0].to_dict(),
        "price_analysis": price_analysis(scoped),
        "top_5_opportunities": summarize_opportunities(scoped),
        "peer_count": int(len(scoped)),
    }


@app.get("/competitors/{competitor_id}/listing-assets")
def competitor_listing_assets(competitor_id: int) -> dict[str, Any]:
    competitor = fetch_competitor_by_id(competitor_id)
    if not competitor:
        raise HTTPException(status_code=404, detail="未找到竞品记录")

    return {
        "competitor": competitor,
        "titles": generate_titles(competitor),
        "keywords": generate_keywords(competitor),
        "detail_structure": generate_detail_structure(competitor),
    }


@app.post("/profit/calculate")
def profit_calculation(request: ProfitCalculationRequest) -> dict[str, Any]:
    payload = request.model_dump()
    profit_input = ProfitInput(**{key: payload[key] for key in ProfitInput.__annotations__.keys()})
    result = calculate_profit(profit_input)
    scenarios = scenario_table(profit_input).to_dict(orient="records")
    record_id = insert_profit_calculation(
        payload=payload,
        result=result,
        competitor_id=request.competitor_id,
        scenario_name=request.scenario_name,
        product_name=request.product_name,
    )
    return {"record_id": record_id, "result": result, "scenarios": scenarios}


@app.get("/profit/history")
def profit_history(limit: int = 50) -> list[dict[str, Any]]:
    df = fetch_profit_history(limit=limit)
    return df.fillna("").to_dict(orient="records")


@app.get("/coupang/openapi/status")
def coupang_openapi_status() -> dict[str, Any]:
    return CoupangOpenApiClient().credential_status()


@app.post("/coupang/openapi/sign-preview")
def coupang_openapi_sign_preview(request: SignPreviewRequest) -> dict[str, Any]:
    client = CoupangOpenApiClient()
    try:
        return client.sign_preview(
            method=request.method,
            path=request.path,
            query=request.query,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
