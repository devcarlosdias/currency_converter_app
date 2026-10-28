#!/usr/bin/env python3
"""Gera planilha de precificação de camisetas (.xlsx)."""

from pathlib import Path

from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter

OUT = Path(__file__).resolve().parent / "precificacao-camisetas.xlsx"

HEADER_FILL = PatternFill("solid", fgColor="1F4E79")
HEADER_FONT = Font(color="FFFFFF", bold=True)
PARAM_FILL = PatternFill("solid", fgColor="E7EEF7")
THIN = Side(style="thin", color="CCCCCC")
BORDER = Border(left=THIN, right=THIN, top=THIN, bottom=THIN)
CURRENCY = '"R$" #,##0.00'
PCT = "0%"


def main() -> None:
    wb = Workbook()
    ws = wb.active
    ws.title = "Precificação"

    ws["A1"] = "Taxa da plataforma (%)"
    ws["B1"] = 0.10
    ws["B1"].number_format = PCT
    ws["A2"] = "Lucro desejado sobre o custo (%)"
    ws["B2"] = 0.30
    ws["B2"].number_format = PCT

    for row in (1, 2):
        ws[f"A{row}"].font = Font(bold=True)
        ws[f"A{row}"].fill = PARAM_FILL
        ws[f"B{row}"].fill = PARAM_FILL
        ws[f"B{row}"].border = BORDER

    ws["A4"] = (
        "Preço de venda = (custo compra + custo restauração) × (1 + taxa plataforma + lucro). "
        "Altere B1 e B2 para recalcular todas as linhas."
    )
    ws.merge_cells("A4:E4")
    ws["A4"].font = Font(italic=True, color="444444")

    headers = [
        "Código",
        "Camisa",
        "Custo de compra",
        "Custo de restauração",
        "Valor de venda",
    ]
    start_row = 6
    for col, title in enumerate(headers, start=1):
        cell = ws.cell(row=start_row, column=col, value=title)
        cell.fill = HEADER_FILL
        cell.font = HEADER_FONT
        cell.alignment = Alignment(horizontal="center", vertical="center")
        cell.border = BORDER

    examples = [
        ("CAM-001", "Camisa banda — M", 45.0, 12.0),
        ("CAM-002", "Camisa vintage — G", 60.0, 18.5),
        ("CAM-003", "Camisa esportiva — P", 35.0, 8.0),
    ]
    for i, (code, name, buy, restore) in enumerate(examples):
        r = start_row + 1 + i
        ws.cell(r, 1, code)
        ws.cell(r, 2, name)
        c_buy = ws.cell(r, 3, buy)
        c_buy.number_format = CURRENCY
        c_rest = ws.cell(r, 4, restore)
        c_rest.number_format = CURRENCY
        sale = ws.cell(r, 5)
        sale.value = f"=(C{r}+D{r})*(1+$B$1+$B$2)"
        sale.number_format = CURRENCY
        for c in range(1, 6):
            ws.cell(r, c).border = BORDER

    last_data = start_row + len(examples)
    template_row = last_data + 1
    ws.cell(template_row, 1, "")
    ws.cell(template_row, 2, "")
    ws.cell(template_row, 3, "")
    ws.cell(template_row, 3).number_format = CURRENCY
    ws.cell(template_row, 4, "")
    ws.cell(template_row, 4).number_format = CURRENCY
    ws.cell(template_row, 5, f"=(C{template_row}+D{template_row})*(1+$B$1+$B$2)")
    ws.cell(template_row, 5).number_format = CURRENCY

    ws.column_dimensions["A"].width = 14
    ws.column_dimensions["B"].width = 28
    ws.column_dimensions["C"].width = 18
    ws.column_dimensions["D"].width = 22
    ws.column_dimensions["E"].width = 16

    info = wb.create_sheet("Como usar")
    lines = [
        "Como usar esta planilha",
        "",
        "1. Na aba «Precificação», célula B1: taxa da plataforma (padrão 10%).",
        "2. Célula B2: percentual de lucro que você quer sobre o custo total da peça.",
        "3. Preencha código, nome, custo de compra e custo de restauração.",
        "4. A coluna «Valor de venda» calcula automaticamente:",
        "   (compra + restauração) + taxa sobre esse total + lucro sobre esse total.",
        "",
        "Exemplo com taxa 10% e lucro 30% sobre custo R$ 57,00:",
        "  Taxa (10% de 57) = R$ 5,70",
        "  Lucro (30% de 57) = R$ 17,10",
        "  Preço de venda = R$ 74,10",
        "",
        "Se a plataforma cobra % sobre o preço final de venda (e não sobre o custo),",
        "use esta fórmula na coluna de venda:",
        "  =(C6+D6)*(1+$B$2)/(1-$B$1)",
        "  (B2 continua sendo lucro sobre o custo; B1 é a taxa retida sobre a venda.)",
    ]
    for i, line in enumerate(lines, start=1):
        cell = info.cell(i, 1, line)
        if i == 1:
            cell.font = Font(bold=True, size=14)

    wb.save(OUT)
    print(f"Gerado: {OUT}")


if __name__ == "__main__":
    main()
