import re
import unicodedata
from typing import Dict, Any

class HardwareSpecExtractor:
    """Extrai e padroniza especificações de hardware (MacBooks) a partir do título e descrição."""

    def __init__(self):
        # Linhas de produtos
        self.line_patterns = [
            (r"\b(macbook\s*air)\b", "MacBook Air"),
            (r"\b(macbook\s*pro)\b", "MacBook Pro"),
            (r"\b(macbook)\b", "MacBook")
        ]

        # Processadores Apple Silicon e Intel
        self.chip_patterns = [
            (r"\b(m4\s*max)\b", "Apple M4 Max"),
            (r"\b(m4\s*pro)\b", "Apple M4 Pro"),
            (r"\b(m4)\b", "Apple M4"),
            (r"\b(m3\s*max)\b", "Apple M3 Max"),
            (r"\b(m3\s*pro)\b", "Apple M3 Pro"),
            (r"\b(m3)\b", "Apple M3"),
            (r"\b(m2\s*max)\b", "Apple M2 Max"),
            (r"\b(m2\s*pro)\b", "Apple M2 Pro"),
            (r"\b(m2)\b", "Apple M2"),
            (r"\b(m1\s*max)\b", "Apple M1 Max"),
            (r"\b(m1\s*pro)\b", "Apple M1 Pro"),
            (r"\b(m1)\b", "Apple M1"),
            (r"\b(core\s*i9|i9)\b", "Intel Core i9"),
            (r"\b(core\s*i7|i7)\b", "Intel Core i7"),
            (r"\b(core\s*i5|i5)\b", "Intel Core i5"),
            (r"\b(intel)\b", "Intel Core")
        ]

        # Memória RAM
        self.ram_patterns = [
            (r"\b(64\s*(?:gb|g|ram))\b", "64GB"),
            (r"\b(32\s*(?:gb|g|ram))\b", "32GB"),
            (r"\b(24\s*(?:gb|g|ram))\b", "24GB"),
            (r"\b(18\s*(?:gb|g|ram))\b", "18GB"),
            (r"\b(16\s*(?:gb|g|ram))\b", "16GB"),
            (r"\b(8\s*(?:gb|g|ram))\b", "8GB"),
        ]

        # Armazenamento SSD
        self.storage_patterns = [
            (r"\b(2\s*(?:tb|tera))\b", "2TB"),
            (r"\b(1\s*(?:tb|tera))\b", "1TB"),
            (r"\b(512\s*(?:gb|ssd|g))\b", "512GB"),
            (r"\b(256\s*(?:gb|ssd|g))\b", "256GB"),
            (r"\b(128\s*(?:gb|ssd|g))\b", "128GB"),
        ]

        # Tamanho da tela
        self.screen_patterns = [
            (r"\b(16[\.,]?\d*[\"']?|16\s*pol)\b", '16"'),
            (r"\b(15[\.,]?\d*[\"']?|15\s*pol)\b", '15"'),
            (r"\b(14[\.,]?\d*[\"']?|14\s*pol)\b", '14"'),
            (r"\b(13[\.,]6[\"']?|13\.6\s*pol)\b", '13.6"'),
            (r"\b(13[\.,]3[\"']?|13\.3\s*pol)\b", '13.3"'),
            (r"\b(13[\"']?|13\s*pol)\b", '13"'),
        ]

    def _normalize(self, text: str) -> str:
        if not text:
            return ""
        nfkd = unicodedata.normalize("NFKD", text.lower())
        return "".join(c for c in nfkd if not unicodedata.combining(c))

    def extract(self, title: str, description: str = "") -> Dict[str, Any]:
        combined = f"{title} {description}".strip()
        norm = self._normalize(combined)

        # 1. Linha do modelo
        line = "MacBook"
        for pattern, label in self.line_patterns:
            if re.search(pattern, norm):
                line = label
                break

        # 2. Processador / Chip
        chip = "Não especificado"
        for pattern, label in self.chip_patterns:
            if re.search(pattern, norm):
                chip = label
                break

        # 3. Memória RAM
        ram = "Não especificado"
        for pattern, label in self.ram_patterns:
            if re.search(pattern, norm):
                ram = label
                break

        # 4. Armazenamento SSD
        storage = "Não especificado"
        for pattern, label in self.storage_patterns:
            if re.search(pattern, norm):
                storage = label
                break

        # 5. Tamanho da tela
        screen = None
        for pattern, label in self.screen_patterns:
            if re.search(pattern, norm):
                screen = label
                break

        # SKU Agrupador (Chave Canônica)
        sku_key = f"{line} | {chip} | {ram} | {storage}"

        return {
            "model_line": line,
            "processor": chip,
            "ram": ram,
            "storage": storage,
            "screen_size": screen,
            "sku_key": sku_key
        }
