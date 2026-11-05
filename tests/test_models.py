import pytest
from models import AdItem
from config import Config

def test_ad_item_instantiation():
    ad = AdItem(
        id="123456",
        title="MacBook Air M2 8GB 256GB Impecável",
        price=4200.0,
        url="https://www.olx.com.br/item/123456",
        location="São Paulo - SP",
        has_delivery=True,
        image_url="https://img.olx.com.br/123.jpg",
        created_at="2026-11-05T08:00:00"
    )
    assert ad.id == "123456"
    assert ad.price == 4200.0
    assert ad.has_delivery is True
    assert "M2" in ad.title

def test_config_defaults(monkeypatch):
    monkeypatch.delenv("TELEGRAM_BOT_TOKEN", raising=False)
    monkeypatch.delenv("TELEGRAM_CHAT_ID", raising=False)
    cfg = Config.load_from_env()
    assert cfg.query == "Macbook Air M2"
    assert cfg.min_price == 3000.0
    assert cfg.max_price == 5000.0
    assert cfg.interval_minutes == 10
    assert cfg.require_delivery is True
    assert cfg.dry_run is True or cfg.telegram_token == ""
