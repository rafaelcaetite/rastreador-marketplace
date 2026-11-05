import os
import pytest
from pathlib import Path
from config import Config
from scraper.olx_scraper import OLXScraper

@pytest.fixture
def mock_html():
    fixture_path = Path(__file__).parent / "fixtures" / "olx_mock_page.html"
    return fixture_path.read_text(encoding="utf-8")

def test_parse_next_data_json(mock_html):
    cfg = Config()
    scraper = OLXScraper(cfg)
    ads = scraper.parse_html(mock_html)

    assert len(ads) == 2
    
    first = ads[0]
    assert first.id == "13456789"
    assert first.title == "MacBook Air M2 256GB Cinza Espacial"
    assert first.price == 4200.0
    assert first.has_delivery is True
    assert first.location == "São Paulo, SP"
    assert first.image_url == "https://img.olx.com.br/images/12/123456789.jpg"

    second = ads[1]
    assert second.id == "98765432"
    assert second.price == 2000.0
    assert second.has_delivery is False

def test_clean_price():
    scraper = OLXScraper(Config())
    assert scraper.clean_price("R$ 4.500") == 4500.0
    assert scraper.clean_price("R$ 3.850,50") == 3850.50
    assert scraper.clean_price(4200) == 4200.0
    assert scraper.clean_price("4200") == 4200.0
    assert scraper.clean_price(None) == 0.0

def test_parse_olx_date():
    from datetime import datetime
    ref = datetime(2026, 11, 5, 12, 0, 0)
    
    # Hoje
    d_hoje = OLXScraper.parse_olx_date("Hoje, 10:27", now=ref)
    assert d_hoje.year == 2026
    assert d_hoje.month == 11
    assert d_hoje.day == 5
    assert d_hoje.hour == 10
    assert d_hoje.minute == 27

    # Ontem
    d_ontem = OLXScraper.parse_olx_date("Ontem, 19:56", now=ref)
    assert d_ontem.day == 4
    assert d_ontem.hour == 19
    assert d_ontem.minute == 56

    # Data por extenso
    d_full = OLXScraper.parse_olx_date("28 de out, 14:10", now=ref)
    assert d_full.month == 10
    assert d_full.day == 28
    assert d_full.hour == 14
    assert d_full.minute == 10
