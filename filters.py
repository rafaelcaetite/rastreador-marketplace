import re
import unicodedata
from typing import Tuple
from models import AdItem
from config import Config

import re
import unicodedata
from typing import Tuple, List
from models import AdItem
from config import Config

def normalize_text(text: str) -> str:
    """Normaliza texto para minúsculas, sem acentos e padroniza variações como 'Mac Book'."""
    if not text:
        return ""
    nfkd = unicodedata.normalize("NFKD", text.lower())
    clean = "".join(c for c in nfkd if not unicodedata.combining(c))
    # Unifica variações comuns de espaçamento
    clean = re.sub(r"\bmac\s+book\b", "macbook", clean)
    clean = re.sub(r"\bmac\s+air\b", "macbook air", clean)
    clean = re.sub(r"\bmac\s+pro\b", "macbook pro", clean)
    return clean

class AdFilter:
    # Padrões que identificam com precisão anúncios onde o item vendido é apenas um acessório, peça ou defeito
    STANDALONE_ACCESSORY_PATTERNS: List[str] = [
        # Título que começa diretamente pelo acessório (ex: 'Capa Macbook', 'Carregador Macbook Pro', 'Kit cases...')
        r"^(capa|capas|capinha|capinhas|case|cases|carregador|carregadores|fonte|pelicula|peliculas|adesivo|adesivos|skin|skins|hub|adaptador|mochila|suporte|pasta|sleeve|teclado|mouse|cooler|bolsa|bag|kit)\b",
        # Expressões do tipo 'para macbook' ou 'p/ macbook'
        r"\b(para|p/|compativel com)\s+(macbook|notebook|apple)\b",
        # Apenas acessórios ou caixa vazia
        r"\b(apenas|so)\s+(a\s+)?(caixa|carregador|fonte|capa|case|acessorios)\b",
        r"\bcaixa\s+vazia\b",
        # Peças, sucata, bloqueio e defeitos
        r"\b(para|retirada\s+de)\s+pecas\b",
        r"\bpecas\s+avulsas\b",
        r"\b(sucata|bloqueado|bloqueada|icloud|tela\s+trincada)\b",
        r"\b(com|tem)\s+defeito\b",
        r"\bdefeito\s+na\s+tela\b",
        r"\bprecisa\s+de\s+reparo\b",
        r"\bnao\s+liga\b",
        r"\bcompro\b"
    ]

    def __init__(self, config: Config):
        self.config = config
        self.normalized_positives = [normalize_text(k) for k in config.positive_keywords]

    def is_valid(self, ad: AdItem) -> Tuple[bool, str]:
        # 1. Filtro de Preço
        if ad.price < self.config.min_price or ad.price > self.config.max_price:
            return False, f"Preço fora da faixa (R$ {ad.price:,.2f} não está entre R$ {self.config.min_price} e R$ {self.config.max_price})"

        # 2. Filtro de Entrega (mantém exclusão de retirada local quando require_delivery=True)
        if self.config.require_delivery and not ad.has_delivery:
            return False, "Sem entrega / OLX Pay disponível (apenas retirada local)"

        normalized_title = normalize_text(ad.title)

        # 3. Filtro de Acessórios Avulsos, Peças e Defeitos
        for pattern in self.STANDALONE_ACCESSORY_PATTERNS:
            if re.search(pattern, normalized_title):
                return False, f"Identificado como acessório avulso, peça ou defeito ({pattern})"

        # 4. Filtro Positivo Flexível (Garante que o aparelho é o procurado)
        for pos in self.normalized_positives:
            pattern = r"\b" + re.escape(pos) + r"\b"
            if not re.search(pattern, normalized_title):
                return False, f"Falta palavra-chave obrigatória: '{pos}'"

        return True, "OK"
