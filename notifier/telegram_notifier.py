import logging
import httpx
from typing import Optional
from models import AdItem
from config import Config

logger = logging.getLogger(__name__)

class TelegramNotifier:
    def __init__(self, config: Config):
        self.config = config
        self.base_url = f"https://api.telegram.org/bot{self.config.telegram_token}"

    def format_message(self, ad: AdItem) -> str:
        delivery_badge = "Disponível (OLX Pay / Envios)" if ad.has_delivery else "Apenas retirada"
        price_formatted = f"R$ {ad.price:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        
        # Benchmark
        benchmark_info = ""
        if ad.market_avg_price and ad.discount_pct is not None:
            avg_formatted = f"R$ {ad.market_avg_price:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
            diff = ad.market_avg_price - ad.price
            diff_formatted = f"R$ {abs(diff):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
            
            if ad.discount_pct > 0:
                benchmark_info = (
                    f"📊 <b>Média de Mercado:</b> {avg_formatted}\n"
                    f"📉 <b>Economia Estimada:</b> {diff_formatted} (<b>-{ad.discount_pct:.1f}%</b>)\n"
                )
            else:
                benchmark_info = (
                    f"📊 <b>Média de Mercado:</b> {avg_formatted}\n"
                    f"📈 <b>Variação:</b> +{abs(ad.discount_pct):.1f}% vs média\n"
                )

        rating_badge = f"{ad.deal_rating}\n" if ad.deal_rating else ""

        # Specs
        specs_info = ""
        if ad.processor or ad.ram or ad.storage:
            specs_info = f"⚙️ <b>Specs:</b> {ad.processor or ''} • {ad.ram or ''} • {ad.storage or ''}\n"

        return (
            f"🚨 <b>{rating_badge.strip() or 'NOVA OPORTUNIDADE ENCONTRADA!'}</b>\n\n"
            f"💻 <b>{ad.title}</b>\n"
            f"🏷️ <b>Origem:</b> {ad.source}\n"
            f"{specs_info}"
            f"💰 <b>Preço:</b> {price_formatted}\n"
            f"{benchmark_info}"
            f"📍 <b>Local:</b> {ad.location}\n"
            f"📦 <b>Entrega:</b> {delivery_badge}\n\n"
            f"🔗 <a href='{ad.url}'>Abrir anúncio no {ad.source}</a>"
        )

    async def send_alert(self, ad: AdItem) -> bool:
        message = self.format_message(ad)

        if self.config.dry_run or not self.config.telegram_token or not self.config.telegram_chat_id:
            logger.info(f"[DRY-RUN / TELEGRAM SIMULADO]\n{message}")
            print(f"\n[ALERTA DETECTADO]\n{message}\n")
            return True

        timeout = httpx.Timeout(15.0, connect=10.0)
        async with httpx.AsyncClient(timeout=timeout) as client:
            try:
                button_title = f"👉 Ver no {ad.source}"
                reply_markup = {
                    "inline_keyboard": [[
                        {"text": button_title, "url": ad.url}
                    ]]
                }

                # Se tiver imagem, tenta enviar sendPhoto com caption HTML
                if ad.image_url:
                    photo_payload = {
                        "chat_id": self.config.telegram_chat_id,
                        "photo": ad.image_url,
                        "caption": message,
                        "parse_mode": "HTML",
                        "reply_markup": reply_markup
                    }
                    resp = await client.post(f"{self.base_url}/sendPhoto", json=photo_payload)
                    if resp.status_code == 200 and resp.json().get("ok"):
                        return True
                    logger.warning(f"Falha ao enviar foto no Telegram ({resp.status_code}): {resp.text}. Tentando sendMessage...")

                # Fallback para mensagem de texto simples
                text_payload = {
                    "chat_id": self.config.telegram_chat_id,
                    "text": message,
                    "parse_mode": "HTML",
                    "disable_web_page_preview": False,
                    "reply_markup": reply_markup
                }
                resp = await client.post(f"{self.base_url}/sendMessage", json=text_payload)
                if resp.status_code == 200 and resp.json().get("ok"):
                    return True

                logger.error(f"Erro Telegram API: {resp.status_code} - {resp.text}")
                return False

            except Exception as e:
                logger.error(f"Exceção de rede ao comunicar com Telegram: {e}")
                return False
