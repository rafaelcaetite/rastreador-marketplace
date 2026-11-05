import statistics
from typing import List, Dict
from models import AdItem

class PricingEngine:
    """Calcula médias de mercado por SKU e classifica as oportunidades de preço."""

    def __init__(self, historical_benchmarks: Dict[str, float] = None):
        self.historical_benchmarks = historical_benchmarks or {}

    def classify_discount(self, discount_pct: float) -> str:
        if discount_pct >= 20.0:
            return "🔥 SUPER OPORTUNIDADE"
        elif discount_pct >= 10.0:
            return "✅ BOM PREÇO"
        elif discount_pct >= -10.0:
            return "⚖️ PREÇO NA MÉDIA"
        else:
            return "⚠️ ACIMA DA MÉDIA"

    def evaluate_deals(self, ads: List[AdItem]) -> List[AdItem]:
        # 1. Agrupar preços válidos por SKU
        sku_groups: Dict[str, List[float]] = {}
        for ad in ads:
            if not ad.sku_key or ad.price <= 0:
                continue
            sku_groups.setdefault(ad.sku_key, []).append(ad.price)

        # 2. Calcular média para cada SKU
        sku_averages: Dict[str, float] = {}
        for sku, prices in sku_groups.items():
            sku_averages[sku] = statistics.mean(prices)

        # 3. Atualizar cada anúncio com a métrica calculada
        for ad in ads:
            sku = ad.sku_key or "Outros"
            avg_price = sku_averages.get(sku) or self.historical_benchmarks.get(sku) or ad.price

            ad.market_avg_price = round(avg_price, 2)
            if avg_price > 0:
                discount = ((avg_price - ad.price) / avg_price) * 100.0
                ad.discount_pct = round(discount, 2)
                ad.deal_rating = self.classify_discount(ad.discount_pct)
            else:
                ad.discount_pct = 0.0
                ad.deal_rating = "⚖️ PREÇO NA MÉDIA"

        return ads
