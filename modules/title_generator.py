from __future__ import annotations

from typing import Any


def _clean_parts(parts: list[str]) -> str:
    return " ".join(part.strip() for part in parts if part and str(part).strip())


def generate_titles(product: dict[str, Any]) -> list[str]:
    brand = str(product.get("brand_name") or "무브랜드")
    product_type = str(product.get("product_type") or "여성 속옷")
    material = str(product.get("material") or product.get("main_selling_points") or "").split(",")[0].strip()
    package_count = int(product.get("package_count") or 1)
    colors = str(product.get("colors") or product.get("color") or "").strip()
    selling_point = str(product.get("main_selling_points") or "").split(",")[0].strip()
    scene = str(product.get("scene") or product.get("use_scene") or "데일리").strip()
    count_text = f"{package_count}매" if any(token in product_type.lower() for token in ["팬티", "underwear", "safety"]) else f"{package_count}개입"

    seo = _clean_parts([brand, product_type, material, selling_point, count_text, scene])
    conversion = _clean_parts([brand, "편안한", product_type, selling_point, count_text])
    natural = _clean_parts([brand, product_type, material, count_text])
    budget = _clean_parts([brand, product_type, count_text, "가성비", scene])
    premium = _clean_parts([brand, product_type, material, count_text, colors, "세트"])

    return [seo, conversion, natural, budget, premium]


def generate_detail_structure(product: dict[str, Any]) -> dict[str, Any]:
    product_type = str(product.get("product_type") or "여성 속옷")
    selling_points = [point.strip() for point in str(product.get("main_selling_points", "")).split(",") if point.strip()]
    weak_points = str(product.get("weak_points", ""))
    bad_reviews = str(product.get("bad_review_points", ""))
    qna_points = str(product.get("qna_points", ""))
    opportunities = str(product.get("differentiation_opportunity", ""))

    faq = [
        "세탁기 사용이 가능한가요? -> 망 세탁 또는 약한 코스를 권장합니다.",
        "사이즈는 어떻게 고르면 되나요? -> 허리와 힙 기준 사이즈표를 먼저 확인해 주세요.",
        "피부 자극이 심하지 않나요? -> 소재 정보와 봉제 위치를 상세페이지에서 투명하게 안내하세요.",
    ]

    if "hook" in product_type.lower() or "클립" in product_type:
        faq[0] = "대부분의 브라에 호환되나요? -> 후크 간격과 길이 규격을 상세히 표시하세요."

    angle = opportunities or "편안함, 실용성, 데일리 사용성을 강조한 구성"
    risk_note = weak_points or bad_reviews or qna_points

    return {
        "main_image": f"{product_type} 제품을 화면 가득 크게 보여주는 깔끔한 화이트 배경 메인컷.",
        "image_2": f"가장 중요한 핵심 포인트를 한 장으로 명확하게 보여주기: {selling_points[0] if selling_points else '편안함과 실용성'}.",
        "image_3": "기존 제품의 불편함과 개선 포인트를 비교하는 깔끔한 한글 인포그래픽.",
        "image_4": "구성품, 컬러 옵션, 사용 전후 또는 착용/사용 장면을 정리한 이미지.",
        "image_5": "세탁 관리, 변형 방지, 일상 사용성을 보여주는 신뢰형 이미지.",
        "size_chart": "허리/힙 기준의 간단한 한글 사이즈표와 핏 참고 문구를 함께 구성.",
        "material_note": "원단 혼용률, 신축성, 촉감, 통기성, 비침 여부를 명확히 표기.",
        "wash_care_note": "중성세제 사용, 세탁망 권장, 고온 건조 금지 등 관리 팁을 안내.",
        "faq": faq,
        "korean_selling_points": [
            "자국 부담이 적고 편안한 데일리 착용감",
            "화이트 배경 중심의 깔끔하고 신뢰감 있는 상품 표현",
            "세탁 및 관리 포인트를 한눈에 이해할 수 있는 구성",
            "과한 표현 없이 실용성과 편안함을 강조한 상세페이지",
            f"차별화 포인트: {angle}",
        ],
        "risk_watchouts": risk_note or "사이즈 기대치, 소재 비침, 과장된 표현 사용 여부를 주의하세요.",
    }
