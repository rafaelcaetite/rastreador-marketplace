from dataclasses import dataclass
from typing import Optional

@dataclass
class AdItem:
    id: str
    title: str
    price: float
    url: str
    location: str
    has_delivery: bool
    source: str = "OLX"
    image_url: Optional[str] = None
    created_at: Optional[str] = None
    
    # Especificações de Hardware Categorizadas
    model_line: Optional[str] = None      # ex: "MacBook Air", "MacBook Pro"
    processor: Optional[str] = None       # ex: "Apple M2", "Apple M1 Pro", "Intel Core i5"
    ram: Optional[str] = None             # ex: "8GB", "16GB", "24GB"
    storage: Optional[str] = None         # ex: "256GB", "512GB", "1TB"
    screen_size: Optional[str] = None     # ex: '13.6"', '15"', '16"'
    sku_key: Optional[str] = None         # Chave canônica para comparação de mercado

    # Métricas de Benchmark e Avaliação
    market_avg_price: Optional[float] = None
    discount_pct: Optional[float] = None
    deal_rating: Optional[str] = None     # ex: "🔥 SUPER OPORTUNIDADE", "✅ BOM PREÇO"
