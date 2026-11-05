import asyncio
import logging
import urllib.parse
from typing import List, Optional
from models import AdItem
from config import Config
from scraper.base_scraper import BaseScraper

logger = logging.getLogger(__name__)

class MercadoLivreScraper(BaseScraper):
    def __init__(self, config: Config):
        self.config = config
        self.api_url = "https://api.mercadolibre.com/sites/MLB/search"

    def _fetch_api_sync(self, url: str) -> dict:
        try:
            from curl_cffi import requests as cffi_requests
            resp = cffi_requests.get(url, impersonate="chrome124", timeout=20)
            if resp.status_code == 200:
                return resp.json()
            logger.warning(f"Mercado Livre API retornou status {resp.status_code}")
            return {}
        except Exception as e:
            logger.error(f"Erro ao consultar API Mercado Livre via curl_cffi: {e}")
            return {}

    async def search(self, query: Optional[str] = None) -> List[AdItem]:
        search_term = query or self.config.query
        params = {
            "q": search_term,
            "limit": 50
        }
        encoded_params = urllib.parse.urlencode(params)
        url = f"{self.api_url}?{encoded_params}"

        logger.info(f"Buscando anúncios no Mercado Livre: {url}")
        ads_found: List[AdItem] = []

        data = await asyncio.to_thread(self._fetch_api_sync, url)
        results = data.get("results", [])

        for item in results:
            ad_id = str(item.get("id"))
            title = item.get("title", "")
            price = float(item.get("price", 0.0))
            permalink = item.get("permalink", "")
            
            # Localização
            addr = item.get("address", {}) or {}
            city = addr.get("city_name") or ""
            state = addr.get("state_name") or ""
            location = f"{city} - {state}".strip(" -") or "Brasil"

            # Entrega (Mercado Envios / Frete Grátis)
            shipping = item.get("shipping", {}) or {}
            has_delivery = bool(shipping.get("free_shipping") or shipping.get("logistic_type"))

            # Thumbnail
            thumb = item.get("thumbnail")
            if thumb and "http://" in thumb:
                thumb = thumb.replace("http://", "https://")

            if ad_id and title and price > 0:
                ads_found.append(AdItem(
                    id=ad_id,
                    title=title,
                    price=price,
                    url=permalink,
                    location=location,
                    has_delivery=has_delivery,
                    source="Mercado Livre",
                    image_url=thumb
                ))

        logger.info(f"Total de anúncios parseados do Mercado Livre: {len(ads_found)}")
        return ads_found
