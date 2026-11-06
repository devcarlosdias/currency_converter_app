#!/usr/bin/env python3
"""Gera planilha Los Hermanos: Dashboard moderno + Inventário com faixas de preço."""

from datetime import date
from pathlib import Path

from openpyxl import Workbook
from openpyxl.formatting.rule import FormulaRule
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.datavalidation import DataValidation

OUT = Path(__file__).resolve().parent / "precificacao-camisetas.xlsx"

# Cores
HEADER_FILL = PatternFill("solid", fgColor="0F2C4C")
HEADER_FONT = Font(color="FFFFFF", bold=True, size=10)
PARAM_FILL = PatternFill("solid", fgColor="E8EEF6")
CARD_BG = PatternFill("solid", fgColor="F7F9FC")
CARD_EDGE = PatternFill("solid", fgColor="E3EAF3")
NOW_FILL = PatternFill("solid", fgColor="E8F6F1")
QUERY_FILL = PatternFill("solid", fgColor="EEF2FF")
TOTAL_FILL = PatternFill("solid", fgColor="EAF2FB")
YELLOW_PASTEL = PatternFill("solid", fgColor="FFF3B0")  # 0%
BLUE_PASTEL = PatternFill("solid", fgColor="D6EAF8")  # 15%
GREEN_PASTEL = PatternFill("solid", fgColor="D5F5E3")  # 30%
PURPLE_PASTEL = PatternFill("solid", fgColor="E8DAEF")  # >30%
RED_LOSS = PatternFill("solid", fgColor="F5B7B1")  # <0%
WARN_FILL = PatternFill("solid", fgColor="FCF3CF")
THIN = Side(style="thin", color="D0D7E2")
BORDER = Border(left=THIN, right=THIN, top=THIN, bottom=THIN)
CURRENCY = '"R$" #,##0.00'
PCT = "0%"
DATE_FMT = "DD/MM/YYYY"

# Inventário columns (1-based)
# A entrada, B modelo, C tamanho, D medida, E autenticidade,
# F mercado, G compra, H restauração,
# I preço 0%, J preço 15%, K sugerido 30%,
# L venda, M data venda, N lucro
COL = {
    "entrada": 1,
    "modelo": 2,
    "tamanho": 3,
    "medida": 4,
    "autenticidade": 5,
    "mercado": 6,
    "compra": 7,
    "restauracao": 8,
    "preco_0": 9,
    "preco_15": 10,
    "sugerido_30": 11,
    "venda": 12,
    "data_venda": 13,
    "lucro": 14,
}

HEADERS = [
    "Data de entrada",
    "Modelo",
    "Tamanho",
    "Medida",
    "Autenticidade",
    "Valor de mercado",
    "Custo de compra",
    "Custo de restauração",
    "Preço mín. (0% lucro)",
    "Preço 15% lucro",
    "Valor sugerido (30%)",
    "Valor de venda",
    "Data da venda",
    "Lucro bruto real",
]

FIRST_DATA = 6
LAST_DATA = 105
NCOLS = len(HEADERS)


def style_header_row(ws, row: int, ncols: int) -> None:
    for col in range(1, ncols + 1):
        cell = ws.cell(row=row, column=col)
        cell.fill = HEADER_FILL
        cell.font = HEADER_FONT
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        cell.border = BORDER


def inv_sum_costs(has_modelo: bool = True) -> str:
    base = f'(Inventário!B{FIRST_DATA}:B{LAST_DATA}<>"")*(Inventário!G{FIRST_DATA}:G{LAST_DATA}+Inventário!H{FIRST_DATA}:H{LAST_DATA})'
    return f"=SUMPRODUCT({base})"


def month_inv(start_cell: str, end_cell: str) -> str:
    return (
        f'=SUMPRODUCT((Inventário!B{FIRST_DATA}:B{LAST_DATA}<>"")'
        f"*(Inventário!A{FIRST_DATA}:A{LAST_DATA}>={start_cell})"
        f"*(Inventário!A{FIRST_DATA}:A{LAST_DATA}<={end_cell})"
        f"*(Inventário!G{FIRST_DATA}:G{LAST_DATA}+Inventário!H{FIRST_DATA}:H{LAST_DATA}))"
    )


def month_profit(start_cell: str, end_cell: str) -> str:
    return (
        f"=SUMPRODUCT((Inventário!M{FIRST_DATA}:M{LAST_DATA}>={start_cell})"
        f"*(Inventário!M{FIRST_DATA}:M{LAST_DATA}<={end_cell})"
        f'*(Inventário!L{FIRST_DATA}:L{LAST_DATA}<>"")'
        f"*(Inventário!L{FIRST_DATA}:L{LAST_DATA}"
        f"-(Inventário!G{FIRST_DATA}:G{LAST_DATA}+Inventário!H{FIRST_DATA}:H{LAST_DATA})))"
    )


def month_sales(start_cell: str, end_cell: str) -> str:
    return (
        f"=SUMPRODUCT((Inventário!M{FIRST_DATA}:M{LAST_DATA}>={start_cell})"
        f"*(Inventário!M{FIRST_DATA}:M{LAST_DATA}<={end_cell})"
        f'*(Inventário!L{FIRST_DATA}:L{LAST_DATA}<>"")'
        f"*(Inventário!L{FIRST_DATA}:L{LAST_DATA}))"
    )


def capital_disponivel() -> str:
    # venda - lucro = custos recuperados
    return (
        f'=SUMPRODUCT((Inventário!L{FIRST_DATA}:L{LAST_DATA}<>"")'
        f"*(Inventário!G{FIRST_DATA}:G{LAST_DATA}+Inventário!H{FIRST_DATA}:H{LAST_DATA}))"
    )


def capital_estoque() -> str:
    return (
        f'=SUMPRODUCT((Inventário!B{FIRST_DATA}:B{LAST_DATA}<>"")'
        f'*(Inventário!L{FIRST_DATA}:L{LAST_DATA}="")'
        f"*(Inventário!G{FIRST_DATA}:G{LAST_DATA}+Inventário!H{FIRST_DATA}:H{LAST_DATA}))"
    )


def lucro_total() -> str:
    return (
        f'=SUMPRODUCT((Inventário!L{FIRST_DATA}:L{LAST_DATA}<>"")'
        f"*(Inventário!L{FIRST_DATA}:L{LAST_DATA}"
        f"-(Inventário!G{FIRST_DATA}:G{LAST_DATA}+Inventário!H{FIRST_DATA}:H{LAST_DATA})))"
    )


def build_inventario(wb: Workbook) -> None:
    ws = wb.create_sheet("Inventário", 0)

    ws["A1"] = "Taxa da plataforma (%)"
    ws["B1"] = 0.10
    ws["B1"].number_format = PCT
    ws["A2"] = "Lucro alvo padrão (coluna verde)"
    ws["B2"] = 0.30
    ws["B2"].number_format = PCT
    ws["C1"] = "Lucro 15% (coluna azul)"
    ws["D1"] = 0.15
    ws["D1"].number_format = PCT
    ws["C2"] = "Lucro 0% (coluna amarela)"
    ws["D2"] = 0.00
    ws["D2"].number_format = PCT

    for addr in ("A1", "A2", "C1", "C2"):
        ws[addr].font = Font(bold=True)
        ws[addr].fill = PARAM_FILL
    for addr in ("B1", "B2", "D1", "D2"):
        ws[addr].fill = PARAM_FILL
        ws[addr].border = BORDER

    ws["A3"] = (
        "Amarelo = preço sem lucro (só cobre taxa + custos). "
        "Azul = 15% de lucro. Verde = 30% (sugerido). "
        "Lucro bruto real = venda − (compra + restauração); "
        "vermelho se margem <0%, amarelo =0%, azul ≥15%, verde ≥30%, roxo >30%."
    )
    ws.merge_cells("A3:N3")
    ws["A3"].font = Font(italic=True, color="555555", size=10)

    header_row = 5
    for col, title in enumerate(HEADERS, start=1):
        ws.cell(header_row, col, title)
    style_header_row(ws, header_row, NCOLS)
    # Color header accents for price bands
    ws.cell(header_row, COL["preco_0"]).fill = PatternFill("solid", fgColor="C9A227")
    ws.cell(header_row, COL["preco_15"]).fill = PatternFill("solid", fgColor="2E86AB")
    ws.cell(header_row, COL["sugerido_30"]).fill = PatternFill("solid", fgColor="1E8449")
    ws.row_dimensions[header_row].height = 36

    examples = [
        (date(2026, 1, 10), "Brasil 2022 — Home", "G", "Largura 54 cm", "Original", 350.0, 180.0, 25.0, 280.0, date(2026, 2, 5)),
        (date(2026, 2, 1), "Flamengo retrô", "M", "Largura 50 cm", "Réplica", 120.0, 45.0, 10.0, None, None),
        (date(2026, 2, 15), "Real Madrid away", "GG", "Largura 58 cm", "Original", 400.0, 220.0, 30.0, None, None),
        (date(2026, 3, 1), "Holanda vintage", "G", "Largura 55 cm", "Original", 280.0, 90.0, 15.0, 150.0, date.today()),
    ]

    for i, row_data in enumerate(examples):
        r = FIRST_DATA + i
        entrada, modelo, tamanho, medida, auth, mercado, compra, restauro, venda, data_venda = row_data
        ws.cell(r, COL["entrada"], entrada)
        ws.cell(r, COL["modelo"], modelo)
        ws.cell(r, COL["tamanho"], tamanho)
        ws.cell(r, COL["medida"], medida)
        ws.cell(r, COL["autenticidade"], auth)
        ws.cell(r, COL["mercado"], mercado)
        ws.cell(r, COL["compra"], compra)
        ws.cell(r, COL["restauracao"], restauro)
        if venda is not None:
            ws.cell(r, COL["venda"], venda)
        if data_venda is not None:
            ws.cell(r, COL["data_venda"], data_venda)

    for r in range(FIRST_DATA, LAST_DATA + 1):
        # 0%: (custo)*(1+taxa+0)
        ws.cell(r, COL["preco_0"], f"=(G{r}+H{r})*(1+$B$1+$D$2)")
        # 15%
        ws.cell(r, COL["preco_15"], f"=(G{r}+H{r})*(1+$B$1+$D$1)")
        # 30% sugerido
        ws.cell(r, COL["sugerido_30"], f"=(G{r}+H{r})*(1+$B$1+$B$2)")
        # Lucro
        ws.cell(r, COL["lucro"], f'=IF(L{r}="","",L{r}-(G{r}+H{r}))')

        for c in range(1, NCOLS + 1):
            ws.cell(r, c).border = BORDER

        for c in (
            COL["mercado"],
            COL["compra"],
            COL["restauracao"],
            COL["preco_0"],
            COL["preco_15"],
            COL["sugerido_30"],
            COL["venda"],
            COL["lucro"],
        ):
            ws.cell(r, c).number_format = CURRENCY

        ws.cell(r, COL["entrada"]).number_format = DATE_FMT
        ws.cell(r, COL["data_venda"]).number_format = DATE_FMT

        # Pastel fills on price columns
        ws.cell(r, COL["preco_0"]).fill = YELLOW_PASTEL
        ws.cell(r, COL["preco_15"]).fill = BLUE_PASTEL
        ws.cell(r, COL["sugerido_30"]).fill = GREEN_PASTEL

    # Conditional formatting on Lucro (col N) by margin = lucro/(G+H)
    # margin < 0 → red
    # margin = 0 → yellow
    # 0.15 <= margin < 0.30 → blue
    # margin >= 0.30 (and not >0.30) → green
    # margin > 0.30 → purple
    lucro_range = f"N{FIRST_DATA}:N{LAST_DATA}"

    # Order matters: more specific first; stopIfTrue=True on each
    ws.conditional_formatting.add(
        lucro_range,
        FormulaRule(
            formula=[f'AND(N{FIRST_DATA}<>"",(G{FIRST_DATA}+H{FIRST_DATA})>0,N{FIRST_DATA}/(G{FIRST_DATA}+H{FIRST_DATA})>0.3)'],
            fill=PURPLE_PASTEL,
            stopIfTrue=True,
        ),
    )
    ws.conditional_formatting.add(
        lucro_range,
        FormulaRule(
            formula=[f'AND(N{FIRST_DATA}<>"",(G{FIRST_DATA}+H{FIRST_DATA})>0,N{FIRST_DATA}/(G{FIRST_DATA}+H{FIRST_DATA})>=0.3)'],
            fill=GREEN_PASTEL,
            stopIfTrue=True,
        ),
    )
    ws.conditional_formatting.add(
        lucro_range,
        FormulaRule(
            formula=[f'AND(N{FIRST_DATA}<>"",(G{FIRST_DATA}+H{FIRST_DATA})>0,N{FIRST_DATA}/(G{FIRST_DATA}+H{FIRST_DATA})>=0.15)'],
            fill=BLUE_PASTEL,
            stopIfTrue=True,
        ),
    )
    ws.conditional_formatting.add(
        lucro_range,
        FormulaRule(
            formula=[f'AND(N{FIRST_DATA}<>"",(G{FIRST_DATA}+H{FIRST_DATA})>0,N{FIRST_DATA}/(G{FIRST_DATA}+H{FIRST_DATA})<0)'],
            fill=RED_LOSS,
            stopIfTrue=True,
        ),
    )
    ws.conditional_formatting.add(
        lucro_range,
        FormulaRule(
            formula=[f'AND(N{FIRST_DATA}<>"",(G{FIRST_DATA}+H{FIRST_DATA})>0,N{FIRST_DATA}/(G{FIRST_DATA}+H{FIRST_DATA})=0)'],
            fill=YELLOW_PASTEL,
            stopIfTrue=True,
        ),
    )

    dv_auth = DataValidation(type="list", formula1='"Original,Réplica"', allow_blank=True)
    ws.add_data_validation(dv_auth)
    dv_auth.add(f"E{FIRST_DATA}:E{LAST_DATA}")

    dv_size = DataValidation(type="list", formula1='"P,M,G,GG,XGG"', allow_blank=True)
    ws.add_data_validation(dv_size)
    dv_size.add(f"C{FIRST_DATA}:C{LAST_DATA}")

    widths = {
        "A": 14,
        "B": 26,
        "C": 9,
        "D": 14,
        "E": 13,
        "F": 15,
        "G": 14,
        "H": 16,
        "I": 16,
        "J": 15,
        "K": 16,
        "L": 14,
        "M": 13,
        "N": 15,
    }
    for col, width in widths.items():
        ws.column_dimensions[col].width = width

    # Legend
    ws["A4"] = "Legenda preços / lucro:"
    ws["A4"].font = Font(bold=True, size=9)
    ws["B4"] = "0% — amarelo"
    ws["B4"].fill = YELLOW_PASTEL
    ws["C4"] = "15% — azul"
    ws["C4"].fill = BLUE_PASTEL
    ws["D4"] = "30% — verde"
    ws["D4"].fill = GREEN_PASTEL
    ws["E4"] = "lucro >30% — roxo"
    ws["E4"].fill = PURPLE_PASTEL
    ws["F4"] = "lucro <0% — vermelho"
    ws["F4"].fill = RED_LOSS

    ws.freeze_panes = "A6"
    ws.auto_filter.ref = f"A5:{get_column_letter(NCOLS)}{LAST_DATA}"


def _kpi_block(ws, start_row: int, start_col: int, title: str, formula: str, subtitle: str, fill: PatternFill) -> None:
    title_cell = ws.cell(start_row, start_col, title)
    title_cell.font = Font(bold=True, size=10, color="5D6D7E")
    value_cell = ws.cell(start_row + 1, start_col, formula)
    value_cell.number_format = CURRENCY
    value_cell.font = Font(bold=True, size=18, color="1A1A1A")
    value_cell.fill = fill
    value_cell.border = BORDER
    value_cell.alignment = Alignment(horizontal="left", vertical="center")
    ws.merge_cells(
        start_row=start_row + 1,
        start_column=start_col,
        end_row=start_row + 1,
        end_column=start_col + 1,
    )
    ws.row_dimensions[start_row + 1].height = 32
    sub = ws.cell(start_row + 2, start_col, subtitle)
    sub.font = Font(italic=True, size=9, color="7F8C8D")
    ws.merge_cells(
        start_row=start_row + 2,
        start_column=start_col,
        end_row=start_row + 2,
        end_column=start_col + 1,
    )


def build_dashboard(wb: Workbook) -> None:
    ws = wb.create_sheet("Dashboard", 0)

    ws["A1"] = "Los Hermanos"
    ws["A1"].font = Font(bold=True, size=22, color="0F2C4C")
    ws["A2"] = "Dashboard de inventário e vendas"
    ws["A2"].font = Font(size=11, color="5D6D7E")

    # —— Visão geral (sempre) ——
    ws["A4"] = "VISÃO GERAL"
    ws["A4"].font = Font(bold=True, size=12, color="FFFFFF")
    ws["A4"].fill = HEADER_FILL
    ws.merge_cells("A4:D4")

    _kpi_block(ws, 5, 1, "Investimento total", inv_sum_costs(), "Compra + restauração de todas as peças", TOTAL_FILL)
    _kpi_block(ws, 5, 3, "Investimento disponível", capital_disponivel(), "Custos recuperados nas vendas (venda − lucro)", WARN_FILL)
    _kpi_block(ws, 9, 1, "Capital em estoque", capital_estoque(), "Custos de peças ainda não vendidas", CARD_BG)
    _kpi_block(ws, 9, 3, "Lucro bruto total", lucro_total(), "Soma do lucro de todas as vendas", GREEN_PASTEL)

    # —— Mês atual (automático) ——
    ws["A14"] = "MÊS ATUAL (automático)"
    ws["A14"].font = Font(bold=True, size=12, color="FFFFFF")
    ws["A14"].fill = PatternFill("solid", fgColor="148F77")
    ws.merge_cells("A14:D14")

    ws["A15"] = "Período"
    ws["A15"].font = Font(bold=True, size=9, color="5D6D7E")
    ws["B15"] = '=TEXT(TODAY(),"MMMM/YYYY")'
    ws["B15"].font = Font(bold=True, size=12, color="0E6655")
    ws["B15"].fill = NOW_FILL
    ws["B15"].border = BORDER

    # Hidden helpers for current month
    ws["F14"] = "Início mês atual"
    ws["G14"] = '=DATE(YEAR(TODAY()),MONTH(TODAY()),1)'
    ws["F15"] = "Fim mês atual"
    ws["G15"] = "=EOMONTH(TODAY(),0)"
    for addr in ("F14", "F15", "G14", "G15"):
        ws[addr].font = Font(color="CCCCCC", size=8)
    ws["G14"].number_format = DATE_FMT
    ws["G15"].number_format = DATE_FMT

    _kpi_block(ws, 16, 1, "Investido neste mês", month_inv("$G$14", "$G$15"), "Peças com entrada no mês atual", NOW_FILL)
    _kpi_block(ws, 16, 3, "Lucro neste mês", month_profit("$G$14", "$G$15"), "Vendas concluídas no mês atual", GREEN_PASTEL)
    _kpi_block(ws, 20, 1, "Vendas neste mês", month_sales("$G$14", "$G$15"), "Soma dos valores de venda do mês", BLUE_PASTEL)

    # —— Consulta por mês ——
    ws["A24"] = "CONSULTA POR MÊS"
    ws["A24"].font = Font(bold=True, size=12, color="FFFFFF")
    ws["A24"].fill = PatternFill("solid", fgColor="3B4F7A")
    ws.merge_cells("A24:D24")

    ws["A25"] = "Escolha o mês"
    ws["A25"].font = Font(bold=True, size=9, color="5D6D7E")
    ws["B25"] = date(2026, 2, 1)
    ws["B25"].number_format = "MMM/YYYY"
    ws["B25"].fill = QUERY_FILL
    ws["B25"].border = BORDER
    ws["C25"] = "Qualquer dia do mês serve"
    ws["C25"].font = Font(italic=True, size=9, color="7F8C8D")

    ws["F24"] = "Início consulta"
    ws["G24"] = "=DATE(YEAR(B25),MONTH(B25),1)"
    ws["F25"] = "Fim consulta"
    ws["G25"] = "=EOMONTH(B25,0)"
    for addr in ("F24", "F25", "G24", "G25"):
        ws[addr].font = Font(color="CCCCCC", size=8)
    ws["G24"].number_format = DATE_FMT
    ws["G25"].number_format = DATE_FMT

    _kpi_block(ws, 26, 1, "Investido na consulta", month_inv("$G$24", "$G$25"), "Entradas no mês escolhido", QUERY_FILL)
    _kpi_block(ws, 26, 3, "Lucro na consulta", month_profit("$G$24", "$G$25"), "Vendas no mês escolhido", GREEN_PASTEL)
    _kpi_block(ws, 30, 1, "Vendas na consulta", month_sales("$G$24", "$G$25"), "Total vendido no mês escolhido", BLUE_PASTEL)

    # Params + legend
    ws["A34"] = "Parâmetros (Inventário)"
    ws["A34"].font = Font(bold=True, size=11, color="0F2C4C")
    ws["A35"] = "Taxa plataforma"
    ws["B35"] = "=Inventário!B1"
    ws["B35"].number_format = PCT
    ws["A36"] = "Lucro 0% / 15% / 30%"
    ws["B36"] = "=Inventário!D2"
    ws["C36"] = "=Inventário!D1"
    ws["D36"] = "=Inventário!B2"
    for addr in ("B36", "C36", "D36"):
        ws[addr].number_format = PCT
        ws[addr].border = BORDER
    ws["B36"].fill = YELLOW_PASTEL
    ws["C36"].fill = BLUE_PASTEL
    ws["D36"].fill = GREEN_PASTEL

    ws["A38"] = "Legenda do lucro bruto (Inventário)"
    ws["A38"].font = Font(bold=True, size=11, color="0F2C4C")
    legend = [
        (39, "< 0% (prejuízo)", RED_LOSS),
        (40, "0% (empate)", YELLOW_PASTEL),
        (41, "15% até < 30%", BLUE_PASTEL),
        (42, "30%", GREEN_PASTEL),
        (43, "> 30%", PURPLE_PASTEL),
    ]
    for row, label, fill in legend:
        ws.cell(row, 1, label).fill = fill
        ws.cell(row, 1).border = BORDER

    ws["A45"] = "Dica: o mês atual atualiza sozinho. Use a consulta para comparar outro período sem perder o recorte de agora."
    ws["A45"].font = Font(italic=True, size=9, color="7F8C8D")
    ws.merge_cells("A45:D45")

    ws.column_dimensions["A"].width = 28
    ws.column_dimensions["B"].width = 18
    ws.column_dimensions["C"].width = 28
    ws.column_dimensions["D"].width = 18
    ws.column_dimensions["E"].width = 3
    ws.column_dimensions["F"].width = 14
    ws.column_dimensions["G"].width = 14


def build_ajuda(wb: Workbook) -> None:
    ws = wb.create_sheet("Como usar")
    lines = [
        "Como usar",
        "",
        "Dashboard",
        "• Visão geral: totais de investimento, capital disponível, estoque e lucro.",
        "• Mês atual: calcula sozinho com a data de hoje (TODAY).",
        "• Consulta por mês: escolha qualquer data em B25 para ver outro período.",
        "",
        "Inventário — preços coloridos",
        "• Amarelo — Preço mín. (0% lucro): cobre custos + taxa, sem lucro.",
        "• Azul — Preço com 15% de lucro.",
        "• Verde — Valor sugerido com 30% de lucro.",
        "• Lucro bruto real: venda − (compra + restauração).",
        "  Cor do lucro: vermelho <0%, amarelo =0%, azul 15–30%, verde =30%, roxo >30%.",
        "",
        "Fórmula: (compra + restauração) × (1 + taxa + lucro%)",
        "Taxa padrão 10% (célula B1 do Inventário).",
    ]
    for i, line in enumerate(lines, start=1):
        cell = ws.cell(i, 1, line)
        if i == 1:
            cell.font = Font(bold=True, size=14)
        elif line in ("Dashboard", "Inventário — preços coloridos"):
            cell.font = Font(bold=True, size=12)
    ws.column_dimensions["A"].width = 95


def main() -> None:
    wb = Workbook()
    default = wb.active
    wb.remove(default)

    build_inventario(wb)
    build_dashboard(wb)
    build_ajuda(wb)

    wb._sheets = [wb["Dashboard"], wb["Inventário"], wb["Como usar"]]
    wb.save(OUT)
    print(f"Gerado: {OUT}")


if __name__ == "__main__":
    main()
