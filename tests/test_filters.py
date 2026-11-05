import pytest
from models import AdItem
from config import Config
from filters import AdFilter

@pytest.fixture
def filter_instance():
    cfg = Config(
        min_price=1000.0,
        max_price=30000.0,
        require_delivery=True,
        positive_keywords=["macbook"],
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
    # Too cheap
    ad_cheap = AdItem(id="2", title="MacBook Air M2", price=150.0, url="", location="", has_delivery=True)
    valid, reason = filter_instance.is_valid(ad_cheap)
    assert valid is False
    assert "Preço fora da faixa" in reason

    # Too expensive
    ad_expensive = AdItem(id="3", title="MacBook Air M2", price=35000.0, url="", location="", has_delivery=True)
    valid, reason = filter_instance.is_valid(ad_expensive)
    assert valid is False
    assert "Preço fora da faixa" in reason

def test_missing_delivery(filter_instance):
    ad = AdItem(id="4", title="MacBook Air M2 impecável", price=4000.0, url="", location="Manaus - AM", has_delivery=False)
    valid, reason = filter_instance.is_valid(ad)
    assert valid is False
    assert "Sem entrega" in reason

def test_negative_keywords_and_accessories_rejected(filter_instance):
    cases = [
        "MacBook Air M2 para retirada de peças",
        "Macbook Air M2 com defeito na placa",
        "MacBook Air M2 bloqueado no iCloud",
        "Compro MacBook Air M2 pago à vista",
        "Apenas caixa do MacBook Air M2 vazia",
        "Case Capinha transparente para MacBook Air M2",
        "Kit de cases para Macbook Air M2",
        "Kit capa protetora de acrilico para Macbook",
        "Capa protetora para MacBook Pro 14",
        "Carregador original Apple MacBook Air M2",
        "Fonte carregador USB-C para Macbook",
        "Película protetora fosca para tela Macbook",
        "MacBook Air M2 tela trincada sem imagem",
        "Mochila e capa sleeve para Macbook",
        "Hub adaptador USB-C para Macbook Air"
    ]
    for title in cases:
        ad = AdItem(id="5", title=title, price=3500.0, url="", location="SP", has_delivery=True)
        valid, reason = filter_instance.is_valid(ad)
        assert valid is False, f"Expected '{title}' to be rejected, but was accepted."
        assert any(k in reason.lower() for k in ["acessório", "peça", "defeito", "negativa"])

def test_macbook_with_accessories_accepted(filter_instance):
    valid_titles = [
        "MacBook Air M2, impecável + acessórios",
        "MacBook Air M2 8/256 Bat. 99% Impecável c/ Caixa, carregador",
        "Macbook Air M2 512gb ssd 24gb ram + acessórios",
        "Mac Book M2 - Usado em estado Excelente",
        "Mac Air M2 16gb 256gb",
        "MacBook Air M2 2022 Em Estado de Novo c/ carregador"
    ]
    for title in valid_titles:
        ad = AdItem(id="6", title=title, price=5200.0, url="", location="SP", has_delivery=True)
        valid, reason = filter_instance.is_valid(ad)
        assert valid is True, f"Expected '{title}' to be accepted, but got: {reason}"

def test_positive_keywords_required(filter_instance):
    # Missing MacBook
    ad_dell = AdItem(id="7", title="Dell XPS 13 Core i7 16GB", price=3800.0, url="", location="SP", has_delivery=True)
    valid, reason = filter_instance.is_valid(ad_dell)
    assert valid is False
    assert "Falta palavra-chave obrigatória" in reason
