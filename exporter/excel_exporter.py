import csv
import datetime
import logging
import os
import re
from typing import List
from models import AdItem

logger = logging.getLogger(__name__)

class ExcelExporter:
    """Exportador para planilhas Excel (.xlsx) e CSV com layout estruturado e leve."""

    def __init__(self, output_dir: str = "data"):
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)

    def _sanitize_filename(self, text: str) -> str:
        clean = re.sub(r"[^\w\s-]", "", text.strip()).replace(" ", "_").lower()
        return clean or "ofertas"

    def export(self, ads: List[AdItem], query: str) -> str:
        sanitized = self._sanitize_filename(query)
        csv_filepath = os.path.join(self.output_dir, f"{sanitized}.csv")
        xlsx_filepath = os.path.join(self.output_dir, f"{sanitized}.xlsx")

        headers = [
            "Data/Hora",
            "Fonte",
            "Linha",
            "Processador",
            "Memória RAM",
            "Armazenamento",
            "Preço (R$)",
            "Média Mercado (R$)",
            "Desconto vs Média (%)",
            "Avaliação da Oferta",
            "Título do Anúncio",
            "Localização",
            "Entrega",
            "Link do Anúncio"
        ]

        # 1. Sempre gera CSV (zero dependência pesada de memória, universal)
        existing_urls = set()
        file_exists = os.path.exists(csv_filepath)
        if file_exists:
            try:
                with open(csv_filepath, mode="r", encoding="utf-8-sig") as f:
                    reader = csv.reader(f, delimiter=";")
                    for r in reader:
                        if len(r) >= 14:
                            existing_urls.add(r[13])
            except Exception:
                pass

        now_str = datetime.datetime.now().strftime("%d/%m/%Y %H:%M")

        with open(csv_filepath, mode="a" if file_exists else "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.writer(f, delimiter=";")
            if not file_exists:
                writer.writerow(headers)

            for ad in ads:
                if ad.url in existing_urls:
                    continue

                discount_text = f"{ad.discount_pct:.1f}%" if ad.discount_pct is not None else "0.0%"
                avg_text = f"{ad.market_avg_price:.2f}" if ad.market_avg_price else f"{ad.price:.2f}"
                price_text = f"{ad.price:.2f}"

                writer.writerow([
                    now_str,
                    ad.source,
                    ad.model_line or "MacBook",
                    ad.processor or "Não informado",
                    ad.ram or "Não informado",
                    ad.storage or "Não informado",
                    price_text,
                    avg_text,
                    discount_text,
                    ad.deal_rating or "⚖️ PREÇO NA MÉDIA",
                    ad.title,
                    ad.location,
                    "Sim" if ad.has_delivery else "Não",
                    ad.url
                ])
                existing_urls.add(ad.url)

        # 2. Tenta gerar/atualizar também o .xlsx se openpyxl carregar sem esgotar RAM
        try:
            from openpyxl import Workbook, load_workbook
            from openpyxl.styles import Font, PatternFill, Alignment
            from openpyxl.utils import get_column_letter

            if os.path.exists(xlsx_filepath):
                wb = load_workbook(xlsx_filepath)
                ws = wb.active
            else:
                wb = Workbook()
                ws = wb.active
                ws.title = query[:30]
                ws.append(headers)

                header_fill = PatternFill(start_color="1A365D", end_color="1A365D", fill_type="solid")
                header_font = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
                for cell in ws[1]:
                    cell.fill = header_fill
                    cell.font = header_font
                    cell.alignment = Alignment(horizontal="center", vertical="center")

            xlsx_urls = set()
            for r in ws.iter_rows(min_row=2, max_col=14, values_only=True):
                if r and len(r) >= 14 and r[13]:
                    xlsx_urls.add(str(r[13]))

            for ad in ads:
                if ad.url in xlsx_urls:
                    continue
                discount_text = f"{ad.discount_pct:.1f}%" if ad.discount_pct is not None else "0.0%"
                avg_val = ad.market_avg_price if ad.market_avg_price else ad.price
                ws.append([
                    now_str,
                    ad.source,
                    ad.model_line or "MacBook",
                    ad.processor or "Não informado",
                    ad.ram or "Não informado",
                    ad.storage or "Não informado",
                    ad.price,
                    avg_val,
                    discount_text,
                    ad.deal_rating or "⚖️ PREÇO NA MÉDIA",
                    ad.title,
                    ad.location,
                    "Sim" if ad.has_delivery else "Não",
                    ad.url
                ])
                xlsx_urls.add(ad.url)

            for col in ws.columns:
                max_len = 0
                col_letter = get_column_letter(col[0].column)
                for cell in col:
                    val = str(cell.value or "")
                    if len(val) > max_len:
                        max_len = len(val)
                ws.column_dimensions[col_letter].width = min(max(max_len + 3, 12), 45)

            wb.save(xlsx_filepath)
            return xlsx_filepath
        except Exception as e:
            logger.warning(f"Não foi possível salvar .xlsx ({e}), mantendo .csv como fallback.")
            return csv_filepath
