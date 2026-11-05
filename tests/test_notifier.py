import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from models import AdItem
from config import Config
from notifier.telegram_notifier import TelegramNotifier

@pytest.fixture
def sample_ad():
    return AdItem(
        id="12345",
        title="MacBook Air M2 256GB Midnight Impecável",
        price=4300.0,
        url="https://olx.com.br/item/12345",
        location="São Paulo - SP",
        has_delivery=True,
        image_url="https://img.olx.com.br/123.jpg"
    )

def test_format_message(sample_ad):
    cfg = Config(dry_run=True)
    notifier = TelegramNotifier(cfg)
    msg = notifier.format_message(sample_ad)
    assert "MacBook Air M2" in msg
    assert "4.300,00" in msg
    assert "São Paulo - SP" in msg
    assert "Disponível (OLX Pay)" in msg
    assert sample_ad.url in msg

@pytest.mark.anyio
async def test_send_alert_dry_run(sample_ad):
    cfg = Config(dry_run=True)
    notifier = TelegramNotifier(cfg)
    success = await notifier.send_alert(sample_ad)
    assert success is True

@pytest.mark.anyio
async def test_send_alert_telegram_api_call(sample_ad):
    cfg = Config(telegram_token="dummy_token", telegram_chat_id="dummy_chat_id", dry_run=False)
    notifier = TelegramNotifier(cfg)

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"ok": True}
        mock_post.return_value = mock_response

        success = await notifier.send_alert(sample_ad)
        assert success is True
        assert mock_post.called
        call_url = mock_post.call_args[0][0]
        assert "dummy_token" in call_url
