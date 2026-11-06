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
YELLOW_PASTEL = PatternFill("solid", fgColor="FFF3B0")  # 0%–4,99%
BLUE_PASTEL = PatternFill("solid", fgColor="D6EAF8")  # 5%–15%
GREEN_PASTEL = PatternFill("solid", fgColor="D5F5E3")  # 15,01%–30%
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
# L venda, M data venda, N taxa cobrada, O lucro após taxa
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
    "taxa": 14,
    "lucro": 15,
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
    "Taxa cobrada (R$)",
    "Lucro após taxa",
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
    # Lucro já abate a taxa (coluna O); filtra por data da venda (M)
    return (
        f"=SUMPRODUCT((Inventário!M{FIRST_DATA}:M{LAST_DATA}>={start_cell})"
        f"*(Inventário!M{FIRST_DATA}:M{LAST_DATA}<={end_cell})"
        f'*(Inventário!L{FIRST_DATA}:L{LAST_DATA}<>"")'
        f"*(Inventário!O{FIRST_DATA}:O{LAST_DATA}))"
    )


def month_sales(start_cell: str, end_cell: str) -> str:
    return (
        f"=SUMPRODUCT((Inventário!M{FIRST_DATA}:M{LAST_DATA}>={start_cell})"
        f"*(Inventário!M{FIRST_DATA}:M{LAST_DATA}<={end_cell})"
        f'*(Inventário!L{FIRST_DATA}:L{LAST_DATA}<>"")'
        f"*(Inventário!L{FIRST_DATA}:L{LAST_DATA}))"
    )


def capital_disponivel() -> str:
    # custos recuperados nas peças vendidas
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
    # Soma do lucro após taxa (coluna O)
    return (
        f'=SUMPRODUCT((Inventário!L{FIRST_DATA}:L{LAST_DATA}<>"")'
        f"*(Inventário!O{FIRST_DATA}:O{LAST_DATA}))"
    )


def taxas_total() -> str:
    return (
        f'=SUMPRODUCT((Inventário!L{FIRST_DATA}:L{LAST_DATA}<>"")'
        f"*(Inventário!N{FIRST_DATA}:N{LAST_DATA}))"
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
        "Preços sugeridos já embutem a taxa: custo × (1 + margem) ÷ (1 − taxa). "
        "Assim, vender no preço 0% zera o lucro após a taxa. "
        "Taxa cobrada = venda × taxa. Lucro = venda − taxa − custos. "
        "Cores: vermelho <0%; amarelo 0–4,99%; azul 5–15%; verde 15,01–30%; roxo >30%."
    )
    ws.merge_cells("A3:O3")
    ws["A3"].font = Font(italic=True, color="555555", size=10)

    header_row = 5
    for col, title in enumerate(HEADERS, start=1):
        ws.cell(header_row, col, title)
    style_header_row(ws, header_row, NCOLS)
    # Color header accents for price bands
    ws.cell(header_row, COL["preco_0"]).fill = PatternFill("solid", fgColor="C9A227")
    ws.cell(header_row, COL["preco_15"]).fill = PatternFill("solid", fgColor="2E86AB")
    ws.cell(header_row, COL["sugerido_30"]).fill = PatternFill("solid", fgColor="1E8449")
    ws.cell(header_row, COL["taxa"]).fill = PatternFill("solid", fgColor="922B21")
    ws.row_dimensions[header_row].height = 36

    # Itens reais: (modelo, tamanho, autenticidade, compra, restauração, venda)
    # Campos não informados (entrada, medida, mercado, data venda) ficam em branco.
    items = [
        ("Bayern", "M", "Original", 99.38, 0.0, 139.13),
        ("Boca Juniors", "G", "Thai", 60.00, 0.0, 84.00),
        ("Borussia", "G", "Thai", 41.42, 0.0, 57.99),
        ("Barcelona", "M", "Thai", 31.00, 0.0, 43.40),
        ("São Paulo 2018", "G", "Original", 20.82, 0.0, 29.15),
        ("Palmeiras", "GG", "Thai", 22.00, 0.0, 30.80),
        ("Brasil Basquete", "G", "Thai - Indefinido", 20.00, 0.0, 28.00),
        ("Brasil 2018", "M", "Original", 20.00, 0.0, 28.00),
        ("Corinthians 2013 - Chicão", "M", "Original", 226.95, 0.0, 317.73),
        ("Ribeirão Preto", "M", "Thai - Indefinido", 10.77, 0.0, 15.08),
        ("Corinthians Retro - 1980", "XGG", "Original - Retrô", 107.56, 0.0, 150.58),
        ("Italia", "G", "Thai - Indefinido", 31.20, 0.0, 43.68),
        ("Corinthians - Batavo Cauã", "G", "Original", 51.38, 0.0, 71.93),
        ("Japão", "G", "Thai", 49.06, 0.0, 68.68),
        ("Corinthians 2013", "P", "Original", 70.38, 0.0, 98.53),
        ("Corinthains - Batavo", "M", "Thai - Indefinido", 33.37, 0.0, 46.72),
        ("Porto 2002", "M", "Original", 51.38, 0.0, 71.93),
        ("Blusa Milan", "P", "Original", 40.93, 0.0, 57.30),
        ("Conjunto Marchester United", "XGG", "Original", 250.00, 0.0, 350.00),
        ("Inter", "XGG", "Original", 55.74, 0.0, 78.04),
        ("Flamengo", "XGG", "Original", 55.74, 0.0, 78.04),
        ("Liverpool", "P", "Original", 40.00, 0.0, 56.00),
        ("Corinthians", "G", "Original", 61.00, 0.0, 85.40),
        ("Calça Milan", "P", "Original", 50.93, 0.0, 71.30),
        ("Coritiba", "M", "Original", 40.00, 0.0, 56.00),
        ("Corinthains", None, "Original", 70.58, 0.0, 98.81),
        ("Corinthians", None, "Original", 70.58, 0.0, 98.81),
        ("Corinthians", None, "Original", 70.58, 0.0, 98.81),
        ("Inter cinza", None, "Original", 51.45, 0.0, 72.03),
        ("Corinthians Amarela", None, "Original", 51.00, 0.0, 71.40),
        ("Espanha", None, "Original", 81.87, 0.0, 114.62),
        ("Argentina", None, "Original", 81.87, 0.0, 114.62),
        ("Palmeiras Verde limão", None, "Original", 67.56, 0.0, 94.58),
        ("Palmeiras", None, "Thai", 40.00, 0.0, 56.00),
        ("Gremio", "G", "Original", 95.81, 0.0, 134.13),
        ("Fluminense", "M", "Original", 95.81, 0.0, 134.13),
        ("Corinthians Preto 2013", "P", "Original", 64.81, 0.0, 90.73),
        ("Palmeiras Listrada", "P", "Original", 38.38, 0.0, 53.73),
        ("Santos 2002", None, "Original", 98.33, 0.0, 137.66),
        ("Manchester United", None, "Original", 98.33, 0.0, 137.66),
        ("Flamengo 2013", "P", "Original", 66.22, 0.0, 92.71),
        ("Corinthians Roxa", "G", "Original", 89.00, 0.0, 124.60),
        ("Nigéria", "G", "Original", 250.00, 0.0, 350.00),
        ("Holanda", "M", "Original", 250.00, 0.0, 350.00),
        ("Paris Saint German 2018", "G", "Original", 105.00, 0.0, 147.00),
    ]

    for i, row_data in enumerate(items):
        r = FIRST_DATA + i
        modelo, tamanho, auth, compra, restauro, venda = row_data
        ws.cell(r, COL["modelo"], modelo)
        if tamanho:
            ws.cell(r, COL["tamanho"], tamanho)
        ws.cell(r, COL["autenticidade"], auth)
        ws.cell(r, COL["compra"], compra)
        ws.cell(r, COL["restauracao"], restauro)
        ws.cell(r, COL["venda"], venda)

    for r in range(FIRST_DATA, LAST_DATA + 1):
        # Preço para margem líquida alvo APÓS a taxa da plataforma:
        # venda × (1 − taxa) = custo × (1 + margem)  ⇒  venda = custo × (1 + margem) / (1 − taxa)
        # 0%: cobre custos + taxa, lucro líquido = 0
        ws.cell(r, COL["preco_0"], f"=(G{r}+H{r})*(1+$D$2)/(1-$B$1)")
        # 15% líquido após taxa
        ws.cell(r, COL["preco_15"], f"=(G{r}+H{r})*(1+$D$1)/(1-$B$1)")
        # 30% líquido após taxa (sugerido)
        ws.cell(r, COL["sugerido_30"], f"=(G{r}+H{r})*(1+$B$2)/(1-$B$1)")
        # Taxa cobrada pela plataforma nesta venda
        ws.cell(r, COL["taxa"], f'=IF(L{r}="","",L{r}*$B$1)')
        # Lucro após taxa = venda − taxa − custos
        ws.cell(r, COL["lucro"], f'=IF(L{r}="","",L{r}-N{r}-(G{r}+H{r}))')

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
            COL["taxa"],
            COL["lucro"],
        ):
            ws.cell(r, c).number_format = CURRENCY

        ws.cell(r, COL["entrada"]).number_format = DATE_FMT
        ws.cell(r, COL["data_venda"]).number_format = DATE_FMT

        # Pastel fills on price columns
        ws.cell(r, COL["preco_0"]).fill = YELLOW_PASTEL
        ws.cell(r, COL["preco_15"]).fill = BLUE_PASTEL
        ws.cell(r, COL["sugerido_30"]).fill = GREEN_PASTEL
        ws.cell(r, COL["taxa"]).fill = PatternFill("solid", fgColor="FADBD8")

    # Conditional formatting on Lucro (col O) by margin = lucro/(G+H)
    # < 0 → vermelho
    # 0 a 4,99% → amarelo
    # 5% a 15% → azul
    # 15,01% a 30% → verde
    # > 30% → roxo
    lucro_range = f"O{FIRST_DATA}:O{LAST_DATA}"
    g = f"(G{FIRST_DATA}+H{FIRST_DATA})"
    o = f"O{FIRST_DATA}"
    margin = f"{o}/{g}"

    ws.conditional_formatting.add(
        lucro_range,
        FormulaRule(
            formula=[f'AND({o}<>"",{g}>0,{margin}>0.3)'],
            fill=PURPLE_PASTEL,
            stopIfTrue=True,
        ),
    )
    ws.conditional_formatting.add(
        lucro_range,
        FormulaRule(
            formula=[f'AND({o}<>"",{g}>0,{margin}>0.15)'],
            fill=GREEN_PASTEL,
            stopIfTrue=True,
        ),
    )
    ws.conditional_formatting.add(
        lucro_range,
        FormulaRule(
            formula=[f'AND({o}<>"",{g}>0,{margin}>=0.05)'],
            fill=BLUE_PASTEL,
            stopIfTrue=True,
        ),
    )
    ws.conditional_formatting.add(
        lucro_range,
        FormulaRule(
            formula=[f'AND({o}<>"",{g}>0,{margin}<0)'],
            fill=RED_LOSS,
            stopIfTrue=True,
        ),
    )
    ws.conditional_formatting.add(
        lucro_range,
        FormulaRule(
            formula=[f'AND({o}<>"",{g}>0,{margin}>=0)'],
            fill=YELLOW_PASTEL,
            stopIfTrue=True,
        ),
    )

    dv_auth = DataValidation(
        type="list",
        formula1='"Original,Original - Retrô,Thai,Thai - Indefinido,Réplica"',
        allow_blank=True,
    )
    ws.add_data_validation(dv_auth)
    dv_auth.add(f"E{FIRST_DATA}:E{LAST_DATA}")

    dv_size = DataValidation(type="list", formula1='"P,M,G,GG,XGG"', allow_blank=True)
    ws.add_data_validation(dv_size)
    dv_size.add(f"C{FIRST_DATA}:C{LAST_DATA}")

    widths = {
        "A": 14,
        "B": 32,
        "C": 9,
        "D": 14,
        "E": 16,
        "F": 15,
        "G": 14,
        "H": 16,
        "I": 16,
        "J": 15,
        "K": 16,
        "L": 14,
        "M": 13,
        "N": 15,
        "O": 15,
    }
    for col, width in widths.items():
        ws.column_dimensions[col].width = width

    # Legend — faixas do lucro após taxa
    ws["A4"] = "Legenda lucro:"
    ws["A4"].font = Font(bold=True, size=9)
    ws["B4"] = "<0% vermelho"
    ws["B4"].fill = RED_LOSS
    ws["C4"] = "0–4,99% amarelo"
    ws["C4"].fill = YELLOW_PASTEL
    ws["D4"] = "5–15% azul"
    ws["D4"].fill = BLUE_PASTEL
    ws["E4"] = "15,01–30% verde"
    ws["E4"].fill = GREEN_PASTEL
    ws["F4"] = ">30% roxo"
    ws["F4"].fill = PURPLE_PASTEL

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
    _kpi_block(ws, 5, 3, "Investimento disponível", capital_disponivel(), "Custos recuperados nas vendas", WARN_FILL)
    _kpi_block(ws, 9, 1, "Capital em estoque", capital_estoque(), "Custos de peças ainda não vendidas", CARD_BG)
    _kpi_block(ws, 9, 3, "Lucro total (após taxa)", lucro_total(), "Venda − taxa da plataforma − custos", GREEN_PASTEL)
    _kpi_block(ws, 9, 5, "Taxas pagas", taxas_total(), "Soma da taxa cobrada em cada venda", PatternFill("solid", fgColor="FADBD8"))

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
    _kpi_block(ws, 16, 3, "Lucro neste mês", month_profit("$G$14", "$G$15"), "Lucro após taxa nas vendas do mês", GREEN_PASTEL)
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
    _kpi_block(ws, 26, 3, "Lucro na consulta", month_profit("$G$24", "$G$25"), "Lucro após taxa no mês escolhido", GREEN_PASTEL)
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

    ws["A38"] = "Legenda do lucro após taxa (Inventário)"
    ws["A38"].font = Font(bold=True, size=11, color="0F2C4C")
    legend = [
        (39, "< 0% (prejuízo)", RED_LOSS),
        (40, "0% a 4,99%", YELLOW_PASTEL),
        (41, "5% a 15%", BLUE_PASTEL),
        (42, "15,01% a 30%", GREEN_PASTEL),
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
    ws.column_dimensions["E"].width = 16
    ws.column_dimensions["F"].width = 14
    ws.column_dimensions["G"].width = 14


def build_ajuda(wb: Workbook) -> None:
    ws = wb.create_sheet("Como usar")
    lines = [
        "Como usar",
        "",
        "Dashboard",
        "• Visão geral: totais de investimento, capital disponível, estoque, lucro após taxa e taxas pagas.",
        "• Mês atual: calcula sozinho com a data de hoje (TODAY).",
        "• Consulta por mês: escolha qualquer data em B25 para ver outro período.",
        "",
        "Inventário — preços e lucro",
        "• Amarelo / Azul / Verde — preços sugeridos para 0%, 15% e 30% de lucro líquido.",
        "• Taxa cobrada (R$) = valor de venda × taxa da plataforma (B1).",
        "• Lucro após taxa = venda − taxa cobrada − (compra + restauração).",
        "  Cores: vermelho <0%; amarelo 0–4,99%; azul 5–15%; verde 15,01–30%; roxo >30%.",
        "",
        "Fórmula de preço sugerido: (compra + restauração) × (1 + lucro%) ÷ (1 − taxa)",
        "Assim o preço 0% cobre custos e a taxa, sem prejuízo. Taxa padrão 10% (B1).",
    ]
    for i, line in enumerate(lines, start=1):
        cell = ws.cell(i, 1, line)
        if i == 1:
            cell.font = Font(bold=True, size=14)
        elif line in ("Dashboard", "Inventário — preços e lucro"):
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
