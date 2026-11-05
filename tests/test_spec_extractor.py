import pytest
from analyzer.spec_extractor import HardwareSpecExtractor

@pytest.fixture
def extractor():
    return HardwareSpecExtractor()

def test_extract_macbook_air_m2(extractor):
    title = "MacBook Air M2 13,6? | 16GB RAM | 256GB SSD | Impecável"
    specs = extractor.extract(title)

    assert specs["model_line"] == "MacBook Air"
    assert specs["processor"] == "Apple M2"
    assert specs["ram"] == "16GB"
    assert specs["storage"] == "256GB"
    assert specs["sku_key"] == "MacBook Air | Apple M2 | 16GB | 256GB"

def test_extract_macbook_pro_m1_pro(extractor):
    title = "Apple MacBook Pro 14 M1 Pro 16gb 512gb ssd Space Gray 2021"
    specs = extractor.extract(title)

    assert specs["model_line"] == "MacBook Pro"
    assert specs["processor"] == "Apple M1 Pro"
    assert specs["ram"] == "16GB"
    assert specs["storage"] == "512GB"
    assert "14" in (specs["screen_size"] or "")

def test_extract_intel_macbook(extractor):
    title = "MacBook Pro 13 2019 Intel Core i5 8GB 128GB SSD"
    specs = extractor.extract(title)

    assert specs["model_line"] == "MacBook Pro"
    assert "Intel" in specs["processor"]
    assert specs["ram"] == "8GB"
    assert specs["storage"] == "128GB"

def test_extract_unknown_defaults(extractor):
    title = "Notebook Apple seminovo funcionando tudo"
    specs = extractor.extract(title)

    assert specs["model_line"] == "MacBook"
    assert specs["processor"] == "Não especificado"
    assert specs["ram"] == "Não especificado"
    assert specs["storage"] == "Não especificado"
