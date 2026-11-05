import asyncio
import logging
import urllib.parse
from typing import List, Optional
from models import AdItem
from config import Config
from scraper.base_scraper import BaseScraper

logger = logging.getLogger(__name__)

class ShopeeScraper(BaseScraper):
    """Coletor de anúncios da Shopee Brasil."""

    def __init__(self, config: Config):
        self.config = config
        self.api_url = "https://shopee.com.br/api/v4/search/search_items"
        self.headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/128.0.0.0 Safari/537.36"
            ),
            "Accept": "application/json",
            "Referer": "https://shopee.com.br/",
            "X-Requested-With": "XMLHttpRequest",
            "X-API-SOURCE": "rweb"
        }

    def _fetch_sync(self, url: str) -> dict:
        try:
            from curl_cffi import requests as cffi_requests
            cookies = {}
            if self.config.shopee_cookie:
                for part in self.config.shopee_cookie.split(";"):
                    if "=" in part:
                        k, v = part.strip().split("=", 1)
                        cookies[k] = v

            resp = cffi_requests.get(
                url,
                headers=self.headers,
                cookies=cookies,
                impersonate="chrome124",
                timeout=20
            )
            if resp.status_code == 200:
                return resp.json()
            logger.warning(f"Shopee retornou status HTTP {resp.status_code}")
            return {}
        except Exception as e:
            logger.error(f"Falha de conexão com a Shopee: {e}")
            return {}

    async def search(self, query: Optional[str] = None) -> List[AdItem]:
        search_term = query or self.config.query
        params = {
            "by": "relevancy",
            "keyword": search_term,
            "limit": 50,
            "newest": 0,
            "order": "desc",
            "page_type": "search",
            "scenario": "PAGE_GLOBAL_SEARCH",
            "version": 2
        }
        encoded = urllib.parse.urlencode(params)
        url = f"{self.api_url}?{encoded}"

        logger.info(f"Consultando Shopee: {search_term}")
        data = await asyncio.to_thread(self._fetch_sync, url)
        
        items = data.get("items", [])
        ads_found: List[AdItem] = []

        for entry in items:
            item_data = entry.get("item_basic", {})
            if not item_data:
                continue

            item_id = str(item_data.get("itemid", ""))
            shop_id = str(item_data.get("shopid", ""))
            title = item_data.get("name", "")
            
            # Preço na Shopee vem multiplicado por 100.000
            raw_price = item_data.get("price", 0)
            price = float(raw_price) / 100000.0 if raw_price > 0 else 0.0

            slug = urllib.parse.quote(title.replace(" ", "-").lower(), safe="")
            link = f"https://shopee.com.br/{slug}-i.{shop_id}.{item_id}"

            # Localização do vendedor / estoque
            location = item_data.get("shop_location") or "Brasil"

            # Imagem do produto
            image_id = item_data.get("image")
            image_url = f"https://down-br.img.susercontent.com/file/{image_id}" if image_id else None

            # Entregas na Shopee contam com rastreio e Shopee Garante
            has_delivery = True

            if item_id and title and price > 0:
                ads_found.append(AdItem(
                    id=f"shopee-{item_id}",
                    title=title,
                    price=round(price, 2),
                    url=link,
                    location=location,
                    has_delivery=has_delivery,
                    source="Shopee",
                    image_url=image_url
                ))

        logger.info(f"Anúncios parseados da Shopee: {len(ads_found)}")
        return ads_found
