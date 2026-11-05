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
            headers = {}
            if self.config.ml_access_token:
                headers["Authorization"] = f"Bearer {self.config.ml_access_token}"

            resp = cffi_requests.get(url, headers=headers, impersonate="chrome124", timeout=20)
            if resp.status_code == 200:
                return resp.json()
            if resp.status_code == 401:
                logger.error("Mercado Livre: Token expirado ou inválido (401 Unauthorized).")
            elif resp.status_code == 403:
                if not self.config.ml_access_token:
                    logger.warning(
                        "Mercado Livre: A API oficial exige autenticação via token Bearer (MERCADOLIVRE_ACCESS_TOKEN). "
                        "Defina o token no seu arquivo .env para habilitar a busca no Mercado Livre. "
                        "Consulte https://developers.mercadolivre.com.br."
                    )
                else:
                    logger.warning("Mercado Livre API retornou status 403 Forbidden.")
            else:
                logger.warning(f"Mercado Livre API retornou status HTTP {resp.status_code}")
            return {}
        except Exception as e:
            logger.error(f"Erro ao consultar API Mercado Livre via curl_cffi: {e}")
            return {}

    async def search(self, query: Optional[str] = None) -> List[AdItem]:
        search_term = query or self.config.query
        ads_found: List[AdItem] = []

        if not self.config.ml_access_token:
            logger.warning(
                "Mercado Livre: Nenhum MERCADOLIVRE_ACCESS_TOKEN configurado. "
                "Para ativar a busca oficial no Mercado Livre, adicione o token ao seu .env. "
                "Ignorando Mercado Livre nesta varredura."
            )
            return []

        limit = 50
        max_pages = min(5, getattr(self.config, "max_pages", 1))

        for page in range(max_pages):
            offset = page * limit
            params = {
                "q": search_term,
                "limit": limit,
                "offset": offset
            }
            encoded_params = urllib.parse.urlencode(params)
            url = f"{self.api_url}?{encoded_params}"

            logger.info(f"Buscando no Mercado Livre (Página {page + 1}/{max_pages}): {url}")
            data = await asyncio.to_thread(self._fetch_api_sync, url)
            results = data.get("results", [])
            if not results:
                break

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

                # Data de criação
                date_created = item.get("date_created") or ""
                created_at = date_created.replace("T", " ").split(".")[0] if date_created else ""

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
                        image_url=thumb,
                        created_at=created_at
                    ))

            if len(results) < limit:
                break
            await asyncio.sleep(1.0)

        logger.info(f"Total de anúncios consolidados do Mercado Livre: {len(ads_found)}")
        return ads_found
