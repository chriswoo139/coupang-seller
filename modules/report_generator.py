from __future__ import annotations

from io import BytesIO
from pathlib import Path

import pandas as pd
from openpyxl.styles import Font, PatternFill

from .scoring import add_scores


def dataframe_to_excel_bytes(df: pd.DataFrame) -> bytes:
    output = BytesIO()
    scored = add_scores(df)

    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        scored.to_excel(writer, sheet_name="Competitors", index=False)

        summary = pd.DataFrame(
            [
                ["Total Competitors", len(scored)],
                ["Average Price (KRW)", round(scored["price"].fillna(0).mean(), 1) if not scored.empty else 0],
                ["Average Opportunity Score", round(scored["product_opportunity_score"].mean(), 1) if not scored.empty else 0],
                ["High Opportunity Count", int((scored["product_opportunity_score"] >= 75).sum()) if not scored.empty else 0],
            ],
            columns=["Metric", "Value"],
        )
        summary.to_excel(writer, sheet_name="Summary", index=False)

        workbook = writer.book
        for sheet_name in ["Competitors", "Summary"]:
            sheet = workbook[sheet_name]
            for cell in sheet[1]:
                cell.font = Font(bold=True, color="FFFFFF")
                cell.fill = PatternFill("solid", fgColor="1F4E78")
            for column_cells in sheet.columns:
                max_length = max(len(str(cell.value or "")) for cell in column_cells)
                sheet.column_dimensions[column_cells[0].column_letter].width = min(max(max_length + 2, 12), 36)

    return output.getvalue()


def dataframe_to_markdown(df: pd.DataFrame) -> str:
    scored = add_scores(df)
    if scored.empty:
        return "# Coupang Product Research Report\n\nNo competitor data available.\n"

    top_items = scored.sort_values("product_opportunity_score", ascending=False).head(10)
    lines = [
        "# Coupang Product Research Report",
        "",
        f"- Total competitors: {len(scored)}",
        f"- Average price (KRW): {scored['price'].fillna(0).mean():.0f}",
        f"- Average opportunity score: {scored['product_opportunity_score'].mean():.1f}",
        "",
        "## Top Opportunities",
    ]

    for _, row in top_items.iterrows():
        lines.append(
            f"- {row['product_name']} | {row['product_type']} | score {row['product_opportunity_score']:.1f} | {row['recommendation']}"
        )

    return "\n".join(lines) + "\n"


def write_markdown_report(df: pd.DataFrame, output_path: Path) -> Path:
    output_path.write_text(dataframe_to_markdown(df), encoding="utf-8")
    return output_path
