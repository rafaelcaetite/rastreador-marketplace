import os
import pytest
from models import AdItem
from exporter.excel_exporter import ExcelExporter

def test_excel_exporter(tmp_path):
    exporter = ExcelExporter(output_dir=str(tmp_path))
    
    ad = AdItem(
        id="123",
        title="MacBook Air M2 8GB 256GB Impecável",
        price=4200.0,
        url="https://olx.com.br/123",
        location="São Paulo - SP",
        has_delivery=True,
        source="OLX",
        model_line="MacBook Air",
        processor="Apple M2",
        ram="8GB",
        storage="256GB",
        market_avg_price=5000.0,
        discount_pct=16.0,
        deal_rating="✅ BOM PREÇO"
    )

    path = exporter.export([ad], "Macbook")
    assert os.path.exists(path)
    assert path.endswith(".xlsx")
