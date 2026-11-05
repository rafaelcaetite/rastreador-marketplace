import logging
from typing import Dict, Any, List
from models import AdItem
from config import Config
from database import DatabaseManager
from filters import AdFilter
from notifier.telegram_notifier import TelegramNotifier
from scraper.olx_scraper import OLXScraper

logger = logging.getLogger(__name__)

class DealPipeline:
    def __init__(
        self,
        config: Config,
        db: DatabaseManager,
        ad_filter: AdFilter,
        notifier: TelegramNotifier,
        scraper: OLXScraper = None
    ):
        self.config = config
        self.db = db
        self.filter = ad_filter
        self.notifier = notifier
        self.scraper = scraper or OLXScraper(config)

    async def run_cycle(self) -> Dict[str, Any]:
        """Executa um ciclo completo de busca, filtragem, deduplicação e alerta."""
        logger.info(f"--- Iniciando ciclo de checagem para '{self.config.query}' ---")
        
        raw_ads = await self.scraper.search()
        logger.info(f"Anúncios brutos retornados pela OLX: {len(raw_ads)}")

        new_deals: List[AdItem] = []
        ignored_filter = 0
        ignored_already_seen = 0

        for ad in raw_ads:
            # 1. Checa se já foi visto no SQLite
            if self.db.is_ad_seen(ad.id):
                ignored_already_seen += 1
                continue

            # 2. Aplica regras de filtragem
            is_valid, reason = self.filter.is_valid(ad)
            if not is_valid:
                logger.debug(f"Descartado [ID {ad.id}]: {reason} - '{ad.title}' (R$ {ad.price})")
                ignored_filter += 1
                continue

            # 3. Anúncio aprovado: envia alerta
            logger.info(f"🎯 OPORTUNIDADE VÁLIDA: [ID {ad.id}] {ad.title} - R$ {ad.price}")
            alert_sent = await self.notifier.send_alert(ad)

            # 4. Registra no banco para não alertar novamente (salvo se dry_run explícito sem salvar)
            if alert_sent and not (self.config.dry_run and not self.config.db_path):
                self.db.mark_ad_seen(ad)

            new_deals.append(ad)

        summary = {
            "total_found": len(raw_ads),
            "new_deals": new_deals,
            "ignored_filter": ignored_filter,
            "ignored_already_seen": ignored_already_seen
        }
        logger.info(
            f"Ciclo concluído: {len(new_deals)} novas oportunidades, "
            f"{ignored_filter} descartados por filtro, {ignored_already_seen} já vistos anteriormente."
        )
        return summary
