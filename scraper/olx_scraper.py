import asyncio
import json
import logging
import re
import urllib.parse
from typing import List, Optional, Any
from bs4 import BeautifulSoup
from models import AdItem
from config import Config
from scraper.base_scraper import BaseScraper

logger = logging.getLogger(__name__)

class OLXScraper(BaseScraper):
    def __init__(self, config: Config):
        self.config = config
        self.base_url = "https://www.olx.com.br/brasil"

    def clean_price(self, raw_price: Any) -> float:
        if raw_price is None:
            return 0.0
        if isinstance(raw_price, (int, float)):
            return float(raw_price)

        text = str(raw_price).strip()
        # Remove R$ e espaços
        text = re.sub(r"[^\d,\.]", "", text)
        if not text:
            return 0.0

        # Se tem vírgula como decimal (ex: 3.850,50)
        if "," in text and "." in text:
            text = text.replace(".", "").replace(",", ".")
        elif "," in text:
            text = text.replace(",", ".")
        elif "." in text:
            # Caso "4.500" -> 4500 (milhar brasileiro)
            parts = text.split(".")
            if len(parts) == 2 and len(parts[1]) == 3:
                text = text.replace(".", "")

        try:
            return float(text)
        except ValueError:
            return 0.0

    def parse_next_data(self, data: dict) -> List[AdItem]:
        ads_found: List[AdItem] = []
        page_props = data.get("props", {}).get("pageProps", {})

        raw_ads = (
            page_props.get("ads")
            or page_props.get("listingProps", {}).get("adList")
            or page_props.get("initialData", {}).get("ads")
            or []
        )

        for item in raw_ads:
            ad_id = str(item.get("listId") or item.get("id") or "")
            if not ad_id:
                continue

            title = item.get("title") or item.get("subject") or ""
            raw_p = item.get("price") or item.get("priceValue")
            price = self.clean_price(raw_p)
            url = item.get("url") or ""

            location = item.get("location") or item.get("locationDisplay") or ""
            if not location:
                loc_obj = item.get("locations", {})
                uf = loc_obj.get("uf") or ""
                city = loc_obj.get("municipality") or ""
                location = f"{city} - {uf}" if city and uf else (city or uf or "Brasil")

            has_delivery = bool(
                item.get("olxDelivery") 
                or item.get("olxPay") 
                or item.get("isOlxDelivery")
                or item.get("hasOlxDelivery")
            )

            image_url = None
            images = item.get("images") or []
            if images and isinstance(images, list):
                first_img = images[0]
                if isinstance(first_img, dict):
                    image_url = first_img.get("original") or first_img.get("thumbnail")
                elif isinstance(first_img, str):
                    image_url = first_img

            ad = AdItem(
                id=ad_id,
                title=title,
                price=price,
                url=url,
                location=str(location).strip(),
                has_delivery=has_delivery,
                image_url=image_url
            )
            ads_found.append(ad)

        return ads_found

    def parse_html(self, html_content: str) -> List[AdItem]:
        soup = BeautifulSoup(html_content, "html.parser")
        
        # 1. Tenta extrair tag __NEXT_DATA__ (quando presente e estruturada)
        next_data_tag = soup.find("script", id="__NEXT_DATA__")
        if next_data_tag and next_data_tag.string:
            try:
                data = json.loads(next_data_tag.string)
                ads = self.parse_next_data(data)
                if ads:
                    return ads
            except Exception as e:
                logger.warning(f"Erro ao parsear JSON __NEXT_DATA__: {e}")

        # 2. Extrai de seções com class 'olx-adcard' (layout padrão atual da OLX)
        ads_found: List[AdItem] = []
        sections = soup.find_all("section", class_=lambda c: c and "olx-adcard" in str(c))
        if not sections:
            sections = soup.find_all("div", attrs={"data-ds-component": "DS-AdCard"})

        for s in sections:
            link = s.find("a", href=lambda h: h and re.search(r"-(\d{8,12})(?:\?|$)", str(h)))
            if not link:
                continue

            url = link.get("href", "")
            id_match = re.search(r"-(\d{8,12})(?:\?|$)", url)
            ad_id = id_match.group(1) if id_match else url

            # Título
            heading = s.find(["h2", "h3"]) or link
            title = heading.get_text(strip=True) if heading else ""

            # Preço
            price_tag = s.find(attrs={"aria-label": re.compile(r"Preço", re.I)}) or s.find(class_=lambda c: c and "price" in str(c).lower())
            raw_price = price_tag.get_text(strip=True) if price_tag else ""
            if not raw_price:
                price_match = re.search(r"R\$\s*([\d\.]+)", s.get_text())
                raw_price = price_match.group(0) if price_match else "0"
            price = self.clean_price(raw_price)

            # Localização
            full_text = s.get_text(" | ", strip=True)
            location = "Brasil"
            loc_match = re.search(r"\|\s*([A-Za-zÀ-ÖØ-öø-ÿ\s]+,\s*[A-Za-zÀ-ÖØ-öø-ÿ\s]+)\s*\|", full_text)
            if loc_match:
                location = loc_match.group(1).strip()

            # Entrega / OLX Pay
            card_text_lower = s.get_text().lower()
            has_delivery = (
                "frete" in card_text_lower
                or "entrega" in card_text_lower
                or "garantia da olx" in card_text_lower
                or "olx pay" in card_text_lower
            )

            # Imagem
            img = s.find("img")
            img_url = (img.get("src") or img.get("data-src")) if img else None

            if ad_id and title:
                ads_found.append(AdItem(
                    id=ad_id,
                    title=title,
                    price=price,
                    url=url,
                    location=location,
                    has_delivery=has_delivery,
                    image_url=img_url
                ))

        return ads_found

    def _fetch_html_sync(self, url: str) -> str:
        """Executa requisição impersonando TLS/HTTP2 de navegador moderno para contornar Cloudflare."""
        try:
            from curl_cffi import requests as cffi_requests
            resp = cffi_requests.get(url, impersonate="chrome124", timeout=20)
            if resp.status_code == 200:
                return resp.text
            logger.error(f"OLX retornou status {resp.status_code} via curl_cffi")
            return ""
        except Exception as e:
            logger.error(f"Erro ao consultar OLX via curl_cffi: {e}")
            return ""

    async def search(self, query: Optional[str] = None) -> List[AdItem]:
        search_term = query or self.config.query
        params = {
            "q": search_term,
            "sf": "1"  # ordenar por mais recentes
        }
        encoded_query = urllib.parse.urlencode(params)
        url = f"{self.base_url}?{encoded_query}"

        logger.info(f"Buscando anúncios na OLX: {url}")
        # Executa a requisição em threadpool assíncrona
        html_content = await asyncio.to_thread(self._fetch_html_sync, url)
        if not html_content:
            return []

        ads = self.parse_html(html_content)
        logger.info(f"Total de anúncios parseados da página: {len(ads)}")
        return ads
