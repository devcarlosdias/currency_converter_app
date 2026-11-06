#!/usr/bin/env python3
"""Gera planilha Los Hermanos: Dashboard + Inventário."""

from datetime import date
from pathlib import Path

from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.worksheet.datavalidation import DataValidation

OUT = Path(__file__).resolve().parent / "precificacao-camisetas.xlsx"

HEADER_FILL = PatternFill("solid", fgColor="1F4E79")
HEADER_FONT = Font(color="FFFFFF", bold=True, size=11)
PARAM_FILL = PatternFill("solid", fgColor="E7EEF7")
CARD_FILL = PatternFill("solid", fgColor="F5F8FC")
ACCENT_FILL = PatternFill("solid", fgColor="D6EAF8")
PROFIT_FILL = PatternFill("solid", fgColor="D5F5E3")
WARN_FILL = PatternFill("solid", fgColor="FCF3CF")
THIN = Side(style="thin", color="CCCCCC")
BORDER = Border(left=THIN, right=THIN, top=THIN, bottom=THIN)
CURRENCY = '"R$" #,##0.00'
PCT = "0%"
DATE_FMT = "DD/MM/YYYY"

# Inventário columns (1-based)
COL = {
    "entrada": 1,  # A Data de entrada
    "modelo": 2,  # B
    "tamanho": 3,  # C
    "medida": 4,  # D
    "autenticidade": 5,  # E Original / Réplica
    "mercado": 6,  # F
    "compra": 7,  # G
    "restauracao": 8,  # H
    "sugerido": 9,  # I
    "venda": 10,  # J
    "data_venda": 11,  # K
    "lucro": 12,  # L
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
    "Valor sugerido",
    "Valor de venda",
    "Data da venda",
    "Lucro bruto real",
]

FIRST_DATA = 6
LAST_DATA = 105  # 100 linhas de inventário


def style_header_row(ws, row: int, ncols: int) -> None:
    for col in range(1, ncols + 1):
        cell = ws.cell(row=row, column=col)
        cell.fill = HEADER_FILL
        cell.font = HEADER_FONT
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        cell.border = BORDER


def money(cell) -> None:
    cell.number_format = CURRENCY
    cell.border = BORDER


def build_inventario(wb: Workbook) -> None:
    ws = wb.create_sheet("Inventário", 0)

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

    ws["A3"] = (
        "Valor sugerido = (custo de compra + custo de restauração) × (1 + taxa + lucro). "
        "Lucro bruto real = valor de venda − (compra + restauração). "
        "Altere B1 e B2 para recalcular os sugeridos."
    )
    ws.merge_cells("A3:L3")
    ws["A3"].font = Font(italic=True, color="555555", size=10)

    header_row = 5
    for col, title in enumerate(HEADERS, start=1):
        ws.cell(header_row, col, title)
    style_header_row(ws, header_row, len(HEADERS))
    ws.row_dimensions[header_row].height = 32

    examples = [
        # entrada, modelo, tamanho, medida, autenticidade, mercado, compra, restauro, venda, data_venda
        (date(2026, 1, 10), "Brasil 2022 — Home", "G", "Largura 54 cm", "Original", 350.0, 180.0, 25.0, 280.0, date(2026, 2, 5)),
        (date(2026, 2, 1), "Flamengo retrô", "M", "Largura 50 cm", "Réplica", 120.0, 45.0, 10.0, None, None),
        (date(2026, 2, 15), "Real Madrid away", "GG", "Largura 58 cm", "Original", 400.0, 220.0, 30.0, None, None),
    ]

    for i, row_data in enumerate(examples):
        r = FIRST_DATA + i
        entrada, modelo, tamanho, medida, auth, mercado, compra, restauro, venda, data_venda = row_data
        ws.cell(r, COL["entrada"], entrada).number_format = DATE_FMT
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
            ws.cell(r, COL["data_venda"], data_venda).number_format = DATE_FMT

    # Preenche fórmulas e formatos em todas as linhas de dados
    for r in range(FIRST_DATA, LAST_DATA + 1):
        # Valor sugerido
        sug = ws.cell(r, COL["sugerido"])
        sug.value = f"=(G{r}+H{r})*(1+$B$1+$B$2)"
        # Lucro bruto real (só faz sentido com venda preenchida)
        lucro = ws.cell(r, COL["lucro"])
        lucro.value = f'=IF(J{r}="","",J{r}-(G{r}+H{r}))'

        for c in range(1, 13):
            ws.cell(r, c).border = BORDER
        for c in (COL["mercado"], COL["compra"], COL["restauracao"], COL["sugerido"], COL["venda"], COL["lucro"]):
            ws.cell(r, c).number_format = CURRENCY
        ws.cell(r, COL["entrada"]).number_format = DATE_FMT
        ws.cell(r, COL["data_venda"]).number_format = DATE_FMT

    # Validações
    dv_auth = DataValidation(
        type="list",
        formula1='"Original,Réplica"',
        allow_blank=True,
    )
    dv_auth.error = "Escolha Original ou Réplica"
    dv_auth.errorTitle = "Autenticidade"
    ws.add_data_validation(dv_auth)
    dv_auth.add(f"E{FIRST_DATA}:E{LAST_DATA}")

    dv_size = DataValidation(
        type="list",
        formula1='"P,M,G,GG,XGG"',
        allow_blank=True,
    )
    ws.add_data_validation(dv_size)
    dv_size.add(f"C{FIRST_DATA}:C{LAST_DATA}")

    widths = {
        "A": 15,
        "B": 28,
        "C": 10,
        "D": 16,
        "E": 14,
        "F": 16,
        "G": 15,
        "H": 18,
        "I": 15,
        "J": 15,
        "K": 14,
        "L": 16,
    }
    for col, width in widths.items():
        ws.column_dimensions[col].width = width

    ws.freeze_panes = "A6"
    ws.auto_filter.ref = f"A5:L{LAST_DATA}"


def build_dashboard(wb: Workbook) -> None:
    ws = wb.create_sheet("Dashboard", 0)

    ws["A1"] = "Los Hermanos — Dashboard"
    ws["A1"].font = Font(bold=True, size=18, color="1F4E79")
    ws.merge_cells("A1:D1")

    ws["A3"] = "Mês de referência"
    ws["A3"].font = Font(bold=True)
    ws["B3"] = date(2026, 2, 1)  # qualquer dia do mês; usuário altera
    ws["B3"].number_format = "MMM/YYYY"
    ws["B3"].fill = WARN_FILL
    ws["B3"].border = BORDER
    ws["C3"] = "← coloque qualquer dia do mês desejado"
    ws["C3"].font = Font(italic=True, color="666666", size=10)

    # Helper dates
    ws["A4"] = "Início do mês"
    ws["B4"] = "=DATE(YEAR(B3),MONTH(B3),1)"
    ws["B4"].number_format = DATE_FMT
    ws["A5"] = "Fim do mês"
    ws["B5"] = "=EOMONTH(B3,0)"
    ws["B5"].number_format = DATE_FMT
    for r in (4, 5):
        ws[f"A{r}"].font = Font(color="888888", size=9)
        ws[f"B{r}"].font = Font(color="888888", size=9)

    inv_total = f'=SUMPRODUCT((Inventário!B{FIRST_DATA}:B{LAST_DATA}<>"")*(Inventário!G{FIRST_DATA}:G{LAST_DATA}+Inventário!H{FIRST_DATA}:H{LAST_DATA}))'
    inv_mes = (
        f'=SUMPRODUCT((Inventário!B{FIRST_DATA}:B{LAST_DATA}<>"")'
        f"*(Inventário!A{FIRST_DATA}:A{LAST_DATA}>=$B$4)"
        f"*(Inventário!A{FIRST_DATA}:A{LAST_DATA}<=$B$5)"
        f"*(Inventário!G{FIRST_DATA}:G{LAST_DATA}+Inventário!H{FIRST_DATA}:H{LAST_DATA}))"
    )
    lucro_mes = (
        f'=SUMPRODUCT((Inventário!K{FIRST_DATA}:K{LAST_DATA}>=$B$4)'
        f"*(Inventário!K{FIRST_DATA}:K{LAST_DATA}<=$B$5)"
        f"*(Inventário!J{FIRST_DATA}:J{LAST_DATA}<>\"\")"
        f"*(Inventário!J{FIRST_DATA}:J{LAST_DATA}-(Inventário!G{FIRST_DATA}:G{LAST_DATA}+Inventário!H{FIRST_DATA}:H{LAST_DATA})))"
    )
    # Capital recuperado / investimento disponível = venda - lucro = custos das peças vendidas
    capital_disp = (
        f'=SUMPRODUCT((Inventário!J{FIRST_DATA}:J{LAST_DATA}<>"")'
        f"*(Inventário!G{FIRST_DATA}:G{LAST_DATA}+Inventário!H{FIRST_DATA}:H{LAST_DATA}))"
    )
    # Also useful: capital ainda parado em estoque
    capital_estoque = (
        f'=SUMPRODUCT((Inventário!B{FIRST_DATA}:B{LAST_DATA}<>"")'
        f'*(Inventário!J{FIRST_DATA}:J{LAST_DATA}="")'
        f"*(Inventário!G{FIRST_DATA}:G{LAST_DATA}+Inventário!H{FIRST_DATA}:H{LAST_DATA}))"
    )
    lucro_total = (
        f'=SUMPRODUCT((Inventário!J{FIRST_DATA}:J{LAST_DATA}<>"")'
        f"*(Inventário!J{FIRST_DATA}:J{LAST_DATA}-(Inventário!G{FIRST_DATA}:G{LAST_DATA}+Inventário!H{FIRST_DATA}:H{LAST_DATA})))"
    )
    vendas_mes = (
        f'=SUMPRODUCT((Inventário!K{FIRST_DATA}:K{LAST_DATA}>=$B$4)'
        f"*(Inventário!K{FIRST_DATA}:K{LAST_DATA}<=$B$5)"
        f"*(Inventário!J{FIRST_DATA}:J{LAST_DATA}<>\"\")"
        f"*(Inventário!J{FIRST_DATA}:J{LAST_DATA}))"
    )

    metrics = [
        (8, "Investimento total", "Tudo que já entrou de custo (compra + restauração)", inv_total, ACCENT_FILL),
        (11, "Investido no mês", "Custos das peças que entraram no mês de referência", inv_mes, CARD_FILL),
        (14, "Lucro no mês", "Lucro bruto real das vendas no mês (venda − custos)", lucro_mes, PROFIT_FILL),
        (
            17,
            "Investimento disponível",
            "Valor de venda − lucro = custos recuperados nas vendas (capital para reinvestir)",
            capital_disp,
            WARN_FILL,
        ),
    ]

    for row, title, subtitle, formula, fill in metrics:
        ws.cell(row, 1, title).font = Font(bold=True, size=12, color="1F4E79")
        ws.merge_cells(start_row=row, start_column=1, end_row=row, end_column=3)
        ws.cell(row + 1, 1, formula)
        ws.cell(row + 1, 1).number_format = CURRENCY
        ws.cell(row + 1, 1).font = Font(bold=True, size=20, color="1A1A1A")
        ws.cell(row + 1, 1).fill = fill
        ws.cell(row + 1, 1).border = BORDER
        ws.merge_cells(start_row=row + 1, start_column=1, end_row=row + 1, end_column=3)
        ws.cell(row + 2, 1, subtitle).font = Font(italic=True, color="666666", size=10)
        ws.merge_cells(start_row=row + 2, start_column=1, end_row=row + 2, end_column=3)

    # Extra KPIs
    ws["A21"] = "Resumo extra"
    ws["A21"].font = Font(bold=True, size=12, color="1F4E79")

    extras = [
        (22, "Lucro bruto total (todas as vendas)", lucro_total),
        (23, "Vendas no mês (R$)", vendas_mes),
        (24, "Capital ainda em estoque", capital_estoque),
    ]
    for row, label, formula in extras:
        ws.cell(row, 1, label).font = Font(bold=True)
        ws.cell(row, 2, formula).number_format = CURRENCY
        ws.cell(row, 2).border = BORDER
        ws.cell(row, 2).fill = CARD_FILL

    ws["A26"] = "Parâmetros (editáveis na aba Inventário)"
    ws["A26"].font = Font(bold=True, size=12, color="1F4E79")
    ws["A27"] = "Taxa da plataforma"
    ws["B27"] = "=Inventário!B1"
    ws["B27"].number_format = PCT
    ws["A28"] = "Lucro desejado sobre o custo"
    ws["B28"] = "=Inventário!B2"
    ws["B28"].number_format = PCT

    ws["A30"] = "Como ler o dashboard"
    ws["A30"].font = Font(bold=True, size=12)
    tips = [
        "1. Em B3, escolha o mês (qualquer data daquele mês).",
        "2. Investimento total = soma de todos os custos já registrados.",
        "3. Investido no mês = custos das peças com Data de entrada naquele mês.",
        "4. Lucro no mês = (valor de venda − compra − restauração) das peças vendidas no mês.",
        "5. Investimento disponível = o que voltou de custo nas vendas (venda − lucro), para girar de novo.",
        "6. Cadastre e edite peças na aba Inventário.",
    ]
    for i, tip in enumerate(tips):
        ws.cell(31 + i, 1, tip).font = Font(size=10, color="444444")

    ws.column_dimensions["A"].width = 42
    ws.column_dimensions["B"].width = 16
    ws.column_dimensions["C"].width = 36
    ws.column_dimensions["D"].width = 14


def build_ajuda(wb: Workbook) -> None:
    ws = wb.create_sheet("Como usar")
    lines = [
        "Como usar",
        "",
        "Dashboard (guia principal)",
        "• Escolha o mês em B3 para filtrar investido/lucro do período.",
        "• Os cartões atualizam com base na aba Inventário.",
        "",
        "Inventário",
        "• Data de entrada: quando a peça chegou / foi recebida.",
        "• Autenticidade: Original ou Réplica (lista suspensa).",
        "• Valor de mercado: referência do que a peça costuma valer.",
        "• Custo de compra + Custo de restauração: seu desembolso.",
        "• Valor sugerido: calculado com taxa da plataforma (B1) e lucro desejado (B2).",
        "• Valor de venda e Data da venda: preencha quando vender.",
        "• Lucro bruto real: venda − (compra + restauração).",
        "",
        "Fórmula do valor sugerido (igual à versão anterior):",
        "  (compra + restauração) × (1 + taxa + lucro)",
        "Ex.: custos R$ 57, taxa 10%, lucro 30% → sugerido R$ 74,10",
    ]
    for i, line in enumerate(lines, start=1):
        cell = ws.cell(i, 1, line)
        if i == 1:
            cell.font = Font(bold=True, size=14)
        elif line and not line.startswith("•") and not line.startswith(" ") and not line.startswith("Ex") and not line.startswith("("):
            if line.endswith(")") or line in ("Dashboard (guia principal)", "Inventário"):
                cell.font = Font(bold=True, size=12)
    ws.column_dimensions["A"].width = 90


def main() -> None:
    wb = Workbook()
    # remove default
    default = wb.active
    wb.remove(default)

    build_inventario(wb)
    build_dashboard(wb)
    build_ajuda(wb)

    # Order: Dashboard, Inventário, Como usar
    wb.move_sheet("Dashboard", offset=-wb.sheetnames.index("Dashboard"))
    # Ensure Inventário is second
    wb._sheets = [
        wb["Dashboard"],
        wb["Inventário"],
        wb["Como usar"],
    ]

    wb.save(OUT)
    print(f"Gerado: {OUT}")


if __name__ == "__main__":
    main()
