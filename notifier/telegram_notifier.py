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
        delivery_badge = "Disponível (OLX Pay)" if ad.has_delivery else "Apenas retirada"
        price_formatted = f"R$ {ad.price:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        
        return (
            f"🚨 <b>NOVA OPORTUNIDADE ENCONTRADA!</b>\n\n"
            f"💻 <b>{ad.title}</b>\n"
            f"💰 <b>Preço:</b> {price_formatted}\n"
            f"📍 <b>Local:</b> {ad.location}\n"
            f"📦 <b>Entrega:</b> {delivery_badge}\n\n"
            f"🔗 <a href='{ad.url}'>Abrir anúncio na OLX</a>"
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
                # Se tiver imagem, tenta enviar sendPhoto com caption HTML
                if ad.image_url:
                    photo_payload = {
                        "chat_id": self.config.telegram_chat_id,
                        "photo": ad.image_url,
                        "caption": message,
                        "parse_mode": "HTML",
                        "reply_markup": {
                            "inline_keyboard": [[
                                {"text": "👉 Ver na OLX", "url": ad.url}
                            ]]
                        }
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
                    "reply_markup": {
                        "inline_keyboard": [[
                            {"text": "👉 Ver na OLX", "url": ad.url}
                        ]]
                    }
                }
                resp = await client.post(f"{self.base_url}/sendMessage", json=text_payload)
                if resp.status_code == 200 and resp.json().get("ok"):
                    return True

                logger.error(f"Erro Telegram API: {resp.status_code} - {resp.text}")
                return False

            except Exception as e:
                logger.error(f"Exceção de rede ao comunicar com Telegram: {e}")
                return False
