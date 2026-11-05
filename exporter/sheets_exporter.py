import datetime
import logging
import os
from typing import List, Optional
from models import AdItem
from config import Config

logger = logging.getLogger(__name__)

class GoogleSheetsExporter:
    """Exportador para Google Sheets via gspread, com suporte a múltiplas abas por item."""

    def __init__(self, config: Config, credentials_file: str = "credentials.json"):
        self.config = config
        self.credentials_file = os.getenv("GOOGLE_CREDENTIALS_FILE", credentials_file)
        self.sheet_name = os.getenv("GOOGLE_SHEET_NAME", "Radar de Ofertas - Hardware")

    def is_available(self) -> bool:
        return os.path.exists(self.credentials_file)

    def export(self, ads: List[AdItem], query: str) -> bool:
        if not self.is_available():
            logger.info(
                f"[GOOGLE SHEETS] Arquivo '{self.credentials_file}' não encontrado. "
                f"Exportação salva no Excel local (data/). Configure credentials.json para sincronizar no Google Drive."
            )
            return False

        try:
            import gspread
            gc = gspread.service_account(filename=self.credentials_file)
            
            # 1. Abrir ou criar a planilha
            try:
                sh = gc.open(self.sheet_name)
            except gspread.SpreadsheetNotFound:
                sh = gc.create(self.sheet_name)
                logger.info(f"Nova planilha criada no Google Sheets: '{self.sheet_name}'")

            # 2. Obter ou criar a aba para o termo pesquisado
            tab_title = query.strip()[:30]
            try:
                worksheet = sh.worksheet(tab_title)
            except gspread.WorksheetNotFound:
                worksheet = sh.add_worksheet(title=tab_title, rows=1000, cols=15)
                # Cabeçalho estilizado
                headers = [
                    "Data/Hora", "Fonte", "Linha", "Processador", "RAM", "Armazenamento",
                    "Preço (R$)", "Média Mercado (R$)", "Desconto (%)", "Avaliação da Oferta",
                    "Título do Anúncio", "Localização", "Entrega", "Link do Anúncio"
                ]
                worksheet.append_row(headers)
                logger.info(f"Criada nova aba '{tab_title}' no Google Sheets.")

            # 3. Ler URLs já existentes para não duplicar
            existing_urls = set(worksheet.col_values(14))  # Coluna 14 = Link

            now_str = datetime.datetime.now().strftime("%d/%m/%Y %H:%M")
            rows_to_append = []

            for ad in ads:
                if ad.url in existing_urls:
                    continue

                discount_str = f"{ad.discount_pct:.1f}%" if ad.discount_pct is not None else "0.0%"
                avg_val = ad.market_avg_price if ad.market_avg_price else ad.price

                row = [
                    now_str,
                    ad.source,
                    ad.model_line or "MacBook",
                    ad.processor or "Não informado",
                    ad.ram or "Não informado",
                    ad.storage or "Não informado",
                    ad.price,
                    avg_val,
                    discount_str,
                    ad.deal_rating or "⚖️ PREÇO NA MÉDIA",
                    ad.title,
                    ad.location,
                    "Sim" if ad.has_delivery else "Não",
                    ad.url
                ]
                rows_to_append.append(row)
                existing_urls.add(ad.url)

            if rows_to_append:
                worksheet.append_rows(rows_to_append)
                logger.info(f"✅ Sincronizados {len(rows_to_append)} novos anúncios na aba '{tab_title}' do Google Sheets.")

            return True

        except Exception as e:
            logger.error(f"Erro ao sincronizar com Google Sheets: {e}")
            return False
