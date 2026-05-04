from __future__ import annotations

from dataclasses import asdict, dataclass

import pandas as pd


@dataclass
class ProfitInput:
    purchase_cost_rmb: float
    package_cost_rmb: float
    china_domestic_shipping_rmb: float
    international_shipping_rmb: float
    exchange_rate: float = 190.0
    coupang_price_krw: float = 0.0
    coupang_fee_rate: float = 0.11
    fulfillment_fee_krw: float = 0.0
    ad_cost_per_order_krw: float = 0.0
    return_loss_rate: float = 0.03
    other_cost_krw: float = 0.0
    package_count: int = 1


def profit_input_to_dict(inputs: ProfitInput) -> dict[str, float | int]:
    return asdict(inputs)


def calculate_profit(inputs: ProfitInput) -> dict[str, float | str]:
    goods_cost_krw = (
        inputs.purchase_cost_rmb
        + inputs.package_cost_rmb
        + inputs.china_domestic_shipping_rmb
        + inputs.international_shipping_rmb
    ) * inputs.exchange_rate
    platform_fee_krw = inputs.coupang_price_krw * inputs.coupang_fee_rate
    pre_return_cost_krw = goods_cost_krw + platform_fee_krw + inputs.fulfillment_fee_krw + inputs.other_cost_krw
    return_reserve_krw = inputs.coupang_price_krw * inputs.return_loss_rate
    total_cost_krw = pre_return_cost_krw + return_reserve_krw + inputs.ad_cost_per_order_krw
    gross_profit_krw = inputs.coupang_price_krw - pre_return_cost_krw
    net_profit_krw = inputs.coupang_price_krw - total_cost_krw
    margin_rate = (net_profit_krw / inputs.coupang_price_krw) if inputs.coupang_price_krw else 0.0
    max_allowed_ad_cost = max(inputs.coupang_price_krw - pre_return_cost_krw - return_reserve_krw, 0.0)
    break_even_roas = (inputs.coupang_price_krw / max_allowed_ad_cost) if max_allowed_ad_cost else 0.0

    low_safe_price = pre_return_cost_krw / 0.82 if pre_return_cost_krw else 0.0
    high_safe_price = pre_return_cost_krw / 0.72 if pre_return_cost_krw else 0.0

    low_price_fit = "适合" if margin_rate >= 0.12 and inputs.coupang_price_krw <= low_safe_price * 1.05 else "不适合"
    multi_pack_fit = "适合" if inputs.package_count >= 3 and margin_rate >= 0.18 else "可尝试"

    return {
        "goods_cost_krw": round(goods_cost_krw, 2),
        "platform_fee_krw": round(platform_fee_krw, 2),
        "return_reserve_krw": round(return_reserve_krw, 2),
        "total_cost_krw": round(total_cost_krw, 2),
        "gross_profit_krw": round(gross_profit_krw, 2),
        "net_profit_krw": round(net_profit_krw, 2),
        "margin_rate": round(margin_rate, 4),
        "break_even_roas": round(break_even_roas, 2),
        "max_allowed_ad_cost": round(max_allowed_ad_cost, 2),
        "safe_price_range": f"{low_safe_price:,.0f} - {high_safe_price:,.0f} KRW",
        "fit_for_low_price_strategy": low_price_fit,
        "fit_for_multi_pack": multi_pack_fit,
    }


def scenario_table(base_inputs: ProfitInput, package_options: list[int] | None = None) -> pd.DataFrame:
    options = package_options or [1, 2, 3, 6]
    rows: list[dict] = []

    for qty in options:
        scenario_inputs = ProfitInput(
            **{
                **asdict(base_inputs),
                "purchase_cost_rmb": base_inputs.purchase_cost_rmb * qty,
                "package_count": qty,
                "coupang_price_krw": base_inputs.coupang_price_krw * qty * (0.95 if qty >= 3 else 1.0),
                "fulfillment_fee_krw": base_inputs.fulfillment_fee_krw + (qty - 1) * 150,
                "ad_cost_per_order_krw": base_inputs.ad_cost_per_order_krw * (1.05 if qty == 1 else 0.9),
            }
        )
        result = calculate_profit(scenario_inputs)
        result["package_count"] = qty
        rows.append(result)

    df = pd.DataFrame(rows)
    ordered = [
        "package_count",
        "total_cost_krw",
        "gross_profit_krw",
        "net_profit_krw",
        "margin_rate",
        "break_even_roas",
        "max_allowed_ad_cost",
        "safe_price_range",
        "fit_for_low_price_strategy",
        "fit_for_multi_pack",
    ]
    return df[ordered]
