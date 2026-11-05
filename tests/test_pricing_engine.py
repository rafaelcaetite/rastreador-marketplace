import pytest
from models import AdItem
from analyzer.pricing_engine import PricingEngine

def test_pricing_engine_calculates_benchmarks():
    engine = PricingEngine()
    
    # Conjunto de 3 MacBooks Air M2 idênticos com preços diferentes
    sku = "MacBook Air | Apple M2 | 8GB | 256GB"
    ad1 = AdItem(id="1", title="MacBook Air M2", price=5000.0, url="", location="", has_delivery=True, sku_key=sku)
    ad2 = AdItem(id="2", title="MacBook Air M2", price=5200.0, url="", location="", has_delivery=True, sku_key=sku)
    ad3 = AdItem(id="3", title="MacBook Air M2", price=3800.0, url="", location="", has_delivery=True, sku_key=sku) # Super oferta
    ad4 = AdItem(id="4", title="MacBook Air M2", price=6200.0, url="", location="", has_delivery=True, sku_key=sku) # Caro

    processed = engine.evaluate_deals([ad1, ad2, ad3, ad4])

    # Média: (5000 + 5200 + 3800 + 6200) / 4 = 5050.0
    for ad in processed:
        assert ad.market_avg_price == 5050.0

    # ad3 (3800): Desconto = (5050 - 3800) / 5050 = ~24.75%
    ad3_proc = next(a for a in processed if a.id == "3")
    assert round(ad3_proc.discount_pct, 1) == 24.8
    assert "SUPER OPORTUNIDADE" in ad3_proc.deal_rating

    # ad4 (6200): Caro
    ad4_proc = next(a for a in processed if a.id == "4")
    assert ad4_proc.discount_pct < 0
    assert "ACIMA DA MÉDIA" in ad4_proc.deal_rating

    # ad1 (5000): Na média (desconto de ~1%)
    ad1_proc = next(a for a in processed if a.id == "1")
    assert "PREÇO NA MÉDIA" in ad1_proc.deal_rating
