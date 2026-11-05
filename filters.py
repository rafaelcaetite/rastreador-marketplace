import re
import unicodedata
from typing import Tuple
from models import AdItem
from config import Config

def normalize_text(text: str) -> str:
    """Normaliza texto para minúsculas e sem acentos para comparação precisa."""
    if not text:
        return ""
    nfkd = unicodedata.normalize("NFKD", text.lower())
    return "".join(c for c in nfkd if not unicodedata.combining(c))

class AdFilter:
    def __init__(self, config: Config):
        self.config = config
        self.normalized_positives = [normalize_text(k) for k in config.positive_keywords]
        self.normalized_negatives = [normalize_text(k) for k in config.negative_keywords]

    def is_valid(self, ad: AdItem) -> Tuple[bool, str]:
        # 1. Filtro de Preço
        if ad.price < self.config.min_price or ad.price > self.config.max_price:
            return False, f"Preço fora da faixa (R$ {ad.price:,.2f} não está entre R$ {self.config.min_price} e R$ {self.config.max_price})"

        # 2. Filtro de Entrega
        if self.config.require_delivery and not ad.has_delivery:
            return False, "Sem entrega / OLX Pay disponível"

        normalized_title = normalize_text(ad.title)

        # 3. Filtro Negativo (Anti-ruído/peças/defeitos) com limite de palavra (\b) para evitar 'impecável' bater em 'peça'
        for neg in self.normalized_negatives:
            pattern = r"\b" + re.escape(neg) + r"\b"
            if re.search(pattern, normalized_title):
                return False, f"Palavra-chave negativa detectada: '{neg}'"

        # 4. Filtro Positivo (Garante que é o item exato)
        for pos in self.normalized_positives:
            pattern = r"\b" + re.escape(pos) + r"\b"
            if not re.search(pattern, normalized_title):
                return False, f"Falta palavra-chave obrigatória: '{pos}'"

        return True, "OK"
