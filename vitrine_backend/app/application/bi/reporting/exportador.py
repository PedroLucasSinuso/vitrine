from io import BytesIO
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, PatternFill


class ExportadorExcel:
    def exportar(self, dados: dict[str, list[dict]]) -> bytes:
        wb = Workbook()
        wb.remove(wb.active)

        cab_font = Font(bold=True, color="FFFFFF", size=11)
        cab_fill = PatternFill(start_color="059669", end_color="059669", fill_type="solid")
        cab_align = Alignment(horizontal="center", vertical="center")

        for nome_aba, linhas in dados.items():
            if not linhas:
                continue
            ws = wb.create_sheet(title=nome_aba[:31])
            cabecalhos = list(linhas[0].keys())
            ws.append(cabecalhos)

            for col_idx, cab in enumerate(cabecalhos, 1):
                cell = ws.cell(row=1, column=col_idx)
                cell.font = cab_font
                cell.fill = cab_fill
                cell.alignment = cab_align

            for linha in linhas:
                ws.append([linha.get(h, "") for h in cabecalhos])

            ws.auto_filter.ref = ws.dimensions

        buf = BytesIO()
        wb.save(buf)
        buf.seek(0)
        return buf.read()
