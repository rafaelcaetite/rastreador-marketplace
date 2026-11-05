import pytest
from unittest.mock import AsyncMock
from models import AdItem
from config import Config
from database import DatabaseManager
from filters import AdFilter
from notifier.telegram_notifier import TelegramNotifier
from pipeline import DealPipeline
from scraper.base_scraper import BaseScraper

class MockScraper(BaseScraper):
    def __init__(self, items):
        self.items = items
    async def search(self, query):
        return self.items

@pytest.fixture
def test_pipeline(tmp_path):
    db_file = tmp_path / "pipeline_test.db"
    cfg = Config(
        min_price=3000.0,
        max_price=5000.0,
        require_delivery=True,
        dry_run=True,
        db_path=str(db_file),
        positive_keywords=["macbook"],
    )
    db = DatabaseManager(str(db_file))
    flt = AdFilter(cfg)
    notif = TelegramNotifier(cfg)
    mock_scraper = MockScraper([])
    return DealPipeline(config=cfg, db=db, ad_filter=flt, notifier=notif, scrapers=[mock_scraper])

@pytest.mark.anyio
async def test_pipeline_execution_cycle(test_pipeline):
    ad_valid = AdItem(
        id="101",
        title="MacBook Air M2 8GB 256GB Impecável",
        price=4100.0,
        url="https://olx.com.br/101",
        location="SP",
        has_delivery=True,
        source="OLX"
    )
    ad_invalid = AdItem(
        id="102",
        title="MacBook Air M2 com tela trincada peças",
        price=3500.0,
        url="https://olx.com.br/102",
        location="RJ",
        has_delivery=True,
        source="Mercado Livre"
    )

    test_pipeline.scrapers[0].items = [ad_valid, ad_invalid]
        
    # 1º Ciclo: Deve alertar apenas ad_valid
    results = await test_pipeline.run_cycle()
    assert len(results["new_deals"]) == 1
    assert results["new_deals"][0].id == "101"
    assert results["ignored_filter"] == 1
    assert results["ignored_already_seen"] == 0

    # Verifica se o ID 101 foi gravado no banco de dados
    assert test_pipeline.db.is_ad_seen("101") is True

    # 2º Ciclo: Executa novamente com os mesmos anúncios
    results_second = await test_pipeline.run_cycle()
    assert len(results_second["new_deals"]) == 0
    assert results_second["ignored_already_seen"] == 1
