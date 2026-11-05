import json
import logging
import re
import urllib.parse
from typing import List, Optional, Any
import httpx
from bs4 import BeautifulSoup
from models import AdItem
from config import Config

logger = logging.getLogger(__name__)

class OLXScraper:
    def __init__(self, config: Config):
        self.config = config
        self.base_url = "https://www.olx.com.br/brasil"
        self.headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/128.0.0.0 Safari/537.36"
            ),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
            "Cache-Control": "no-cache",
            "sec-ch-ua": '"Chromium";v="128", "Not;A=Brand";v="24", "Google Chrome";v="128"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
            "sec-fetch-dest": "document",
            "sec-fetch-mode": "navigate",
            "sec-fetch-site": "none",
            "sec-fetch-user": "?1",
            "upgrade-insecure-requests": "1",
        }

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

        # Tenta múltiplos caminhos possíveis no schema do Next.js da OLX
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

            # Localização
            location = item.get("location") or item.get("locationDisplay") or ""
            if not location:
                loc_obj = item.get("locations", {})
                uf = loc_obj.get("uf") or ""
                city = loc_obj.get("municipality") or ""
                location = f"{city} - {uf}" if city and uf else (city or uf or "Brasil")

            # OLX Pay / Entrega
            has_delivery = bool(
                item.get("olxDelivery") 
                or item.get("olxPay") 
                or item.get("isOlxDelivery")
                or item.get("hasOlxDelivery")
            )

            # Imagem principal
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

    def parse_dom_fallback(self, soup: BeautifulSoup) -> List[AdItem]:
        ads_found: List[AdItem] = []
        cards = soup.find_all("div", attrs={"data-ds-component": "DS-AdCard"})
        if not cards:
            cards = soup.find_all("section", attrs={"data-lurker-list": True})

        for card in cards:
            link_tag = card.find("a", href=True)
            if not link_tag:
                continue

            url = link_tag["href"]
            # Extrair id da URL (ex: ...-13456789)
            id_match = re.search(r"-(\d{6,12})(?:\?|$)", url)
            ad_id = id_match.group(1) if id_match else url

            title_tag = card.find(["h2", "h3"])
            title = title_tag.get_text(strip=True) if title_tag else ""

            price_tag = card.find(attrs={"aria-label": re.compile(r"Preço", re.I)})
            raw_price = price_tag.get_text(strip=True) if price_tag else ""
            price = self.clean_price(raw_price)

            img_tag = card.find("img")
            img_url = img_tag.get("src") if img_tag else None

            # Checar badge de entrega
            has_delivery = "entrega" in card.get_text().lower() or "olx pay" in card.get_text().lower()

            if title and price > 0:
                ads_found.append(AdItem(
                    id=ad_id,
                    title=title,
                    price=price,
                    url=url,
                    location="Brasil",
                    has_delivery=has_delivery,
                    image_url=img_url
                ))

        return ads_found

    def parse_html(self, html_content: str) -> List[AdItem]:
        soup = BeautifulSoup(html_content, "html.parser")
        
        # 1. Tenta extrair tag __NEXT_DATA__
        next_data_tag = soup.find("script", id="__NEXT_DATA__")
        if next_data_tag and next_data_tag.string:
            try:
                data = json.loads(next_data_tag.string)
                ads = self.parse_next_data(data)
                if ads:
                    return ads
            except Exception as e:
                logger.warning(f"Erro ao parsear JSON __NEXT_DATA__: {e}")

        # 2. Fallback para parsing do DOM
        return self.parse_dom_fallback(soup)

    async def search(self, query: Optional[str] = None) -> List[AdItem]:
        search_term = query or self.config.query
        params = {
            "q": search_term,
            "sf": "1"  # ordenar por mais recentes
        }
        encoded_query = urllib.parse.urlencode(params)
        url = f"{self.base_url}?{encoded_query}"

        timeout = httpx.Timeout(20.0, connect=10.0)
        async with httpx.AsyncClient(headers=self.headers, timeout=timeout, follow_redirects=True) as client:
            logger.info(f"Buscando anúncios na OLX: {url}")
            resp = await client.get(url)
            if resp.status_code != 200:
                logger.error(f"OLX retornou status {resp.status_code}")
                return []
            
            return self.parse_html(resp.text)
