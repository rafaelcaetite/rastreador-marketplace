import pytest
from models import AdItem
from config import Config
from filters import AdFilter

@pytest.fixture
def filter_instance():
    cfg = Config(
        min_price=3000.0,
        max_price=5000.0,
        require_delivery=True,
        positive_keywords=["macbook", "m2"],
        negative_keywords=[
            "peça", "peças", "defeito", "quebrado", "sucata", "bloqueado", 
            "icloud", "compro", "apenas caixa", "capinha", "carregador", 
            "tela trincada", "acessório", "case"
        ]
    )
    return AdFilter(config=cfg)

def test_valid_ad(filter_instance):
    ad = AdItem(
        id="1",
        title="MacBook Air M2 256GB Midnight com caixa e nota",
        price=4200.0,
        url="https://olx.com.br/1",
        location="Curitiba - PR",
        has_delivery=True
    )
    is_valid, reason = filter_instance.is_valid(ad)
    assert is_valid is True
    assert reason == "OK"

def test_price_out_of_bounds(filter_instance):
    # Too cheap (e.g. accessory or scam)
    ad_cheap = AdItem(id="2", title="MacBook Air M2", price=150.0, url="", location="", has_delivery=True)
    valid, reason = filter_instance.is_valid(ad_cheap)
    assert valid is False
    assert "Preço fora da faixa" in reason

    # Too expensive (not a deal)
    ad_expensive = AdItem(id="3", title="MacBook Air M2", price=6200.0, url="", location="", has_delivery=True)
    valid, reason = filter_instance.is_valid(ad_expensive)
    assert valid is False
    assert "Preço fora da faixa" in reason

def test_missing_delivery(filter_instance):
    ad = AdItem(id="4", title="MacBook Air M2 impecável", price=4000.0, url="", location="Manaus - AM", has_delivery=False)
    valid, reason = filter_instance.is_valid(ad)
    assert valid is False
    assert "Sem entrega" in reason

def test_negative_keywords_rejected(filter_instance):
    cases = [
        "MacBook Air M2 para retirada de peças",
        "Macbook Air M2 com defeito na placa",
        "MacBook Air M2 bloqueado no iCloud",
        "Compro MacBook Air M2 pago à vista",
        "Apenas caixa do MacBook Air M2 vazia",
        "Case Capinha transparente para MacBook Air M2",
        "Carregador original Apple MacBook Air M2",
        "MacBook Air M2 tela trincada sem imagem"
    ]
    for title in cases:
        ad = AdItem(id="5", title=title, price=3500.0, url="", location="SP", has_delivery=True)
        valid, reason = filter_instance.is_valid(ad)
        assert valid is False, f"Expected '{title}' to be rejected, but was accepted."
        assert "Palavra-chave negativa" in reason

def test_positive_keywords_required(filter_instance):
    # Missing M2 (e.g. M1 or Intel)
    ad_m1 = AdItem(id="6", title="MacBook Air M1 256GB Cinza", price=3800.0, url="", location="SP", has_delivery=True)
    valid, reason = filter_instance.is_valid(ad_m1)
    assert valid is False
    assert "Falta palavra-chave obrigatória" in reason

    # Missing MacBook (e.g. Mac Mini M2)
    ad_mini = AdItem(id="7", title="Apple Mac Mini M2 8GB 256GB", price=3800.0, url="", location="SP", has_delivery=True)
    valid, reason = filter_instance.is_valid(ad_mini)
    assert valid is False
    assert "Falta palavra-chave obrigatória" in reason
