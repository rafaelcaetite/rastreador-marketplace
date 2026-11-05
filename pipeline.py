import asyncio
import logging
from typing import Dict, Any, List
from models import AdItem
from config import Config
from database import DatabaseManager
from filters import AdFilter
from notifier.telegram_notifier import TelegramNotifier
from scraper.base_scraper import BaseScraper
from scraper.olx_scraper import OLXScraper
from scraper.ml_scraper import MercadoLivreScraper
from scraper.shopee_scraper import ShopeeScraper
from analyzer.spec_extractor import HardwareSpecExtractor
from analyzer.pricing_engine import PricingEngine
from exporter.excel_exporter import ExcelExporter
from exporter.sheets_exporter import GoogleSheetsExporter

logger = logging.getLogger(__name__)

class DealPipeline:
    def __init__(
        self,
        config: Config,
        db: DatabaseManager,
        ad_filter: AdFilter,
        notifier: TelegramNotifier,
        scrapers: List[BaseScraper] = None
    ):
        self.config = config
        self.db = db
        self.filter = ad_filter
        self.notifier = notifier
        self.spec_extractor = HardwareSpecExtractor()
        self.pricing_engine = PricingEngine()
        self.excel_exporter = ExcelExporter()
        self.sheets_exporter = GoogleSheetsExporter(config)

        if scrapers is not None:
            self.scrapers = scrapers
        else:
            self.scrapers = []
            if "olx" in config.active_sources:
                self.scrapers.append(OLXScraper(config))
            if "ml" in config.active_sources:
                self.scrapers.append(MercadoLivreScraper(config))
            if "shopee" in config.active_sources:
                self.scrapers.append(ShopeeScraper(config))

    async def run_cycle(self) -> Dict[str, Any]:
        """Executa um ciclo completo multi-marketplace de busca, validação prévia, análise e exportação."""
        logger.info(f"--- Iniciando ciclo de monitoramento para '{self.config.query}' ---")
        
        # 1. Coleta paralela em todos os marketplaces ativos
        scrape_tasks = [scraper.search(self.config.query) for scraper in self.scrapers]
        scraped_results = await asyncio.gather(*scrape_tasks, return_exceptions=True)

        raw_ads: List[AdItem] = []
        for res in scraped_results:
            if isinstance(res, list):
                raw_ads.extend(res)
            elif isinstance(res, Exception):
                logger.error(f"Erro no coletor: {res}")

        logger.info(f"Total de anúncios coletados brutos: {len(raw_ads)}")

        # 2. Validação e Filtragem Prévia (Exclui itens sem entrega, peças, capas e acessórios ANTES de qualquer exportação)
        valid_ads: List[AdItem] = []
        ignored_filter = 0

        for ad in raw_ads:
            is_valid, reason = self.filter.is_valid(ad)
            if not is_valid:
                logger.debug(f"Descartado [ID {ad.id}]: {reason} - '{ad.title}' (R$ {ad.price})")
                ignored_filter += 1
                continue
            valid_ads.append(ad)

        logger.info(f"Anúncios aprovados após validação de entrega e filtros anti-ruído: {len(valid_ads)}")

        # 3. Extração semântica de especificações apenas dos itens válidos
        for ad in valid_ads:
            specs = self.spec_extractor.extract(ad.title)
            ad.model_line = specs["model_line"]
            ad.processor = specs["processor"]
            ad.ram = specs["ram"]
            ad.storage = specs["storage"]
            ad.screen_size = specs["screen_size"]
            ad.sku_key = specs["sku_key"]

        # 4. Motor estatístico de preços (Benchmark calculado exclusivamente sobre produtos válidos)
        evaluated_ads = self.pricing_engine.evaluate_deals(valid_ads)

        # 5. Sincronização com Google Sheets e exportação local (.xlsx e .csv) apenas de itens aprovados
        if evaluated_ads:
            excel_path = self.excel_exporter.export(evaluated_ads, self.config.query)
            logger.info(f"📊 Arquivo local atualizado: {excel_path}")
            self.sheets_exporter.export(evaluated_ads, self.config.query)

        # 6. Deduplicação e notificação dos novos anúncios
        new_deals: List[AdItem] = []
        ignored_already_seen = 0

        for ad in evaluated_ads:
            if self.db.is_ad_seen(ad.id):
                ignored_already_seen += 1
                continue

            logger.info(
                f"🎯 OPORTUNIDADE VÁLIDA ({ad.source}): [ID {ad.id}] {ad.title} "
                f"- R$ {ad.price:,.2f} ({ad.deal_rating})"
            )
            alert_sent = await self.notifier.send_alert(ad)

            if alert_sent and not (self.config.dry_run and not self.config.db_path):
                self.db.mark_ad_seen(ad)

            new_deals.append(ad)

        summary = {
            "total_found": len(raw_ads),
            "valid_count": len(valid_ads),
            "new_deals": new_deals,
            "ignored_filter": ignored_filter,
            "ignored_already_seen": ignored_already_seen
        }
        logger.info(
            f"Ciclo concluído: {len(new_deals)} novas ofertas alertadas, "
            f"{ignored_filter} descartados por filtros/entrega, {ignored_already_seen} já processados anteriormente."
        )
        return summary
