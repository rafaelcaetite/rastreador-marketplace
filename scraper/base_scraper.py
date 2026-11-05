from abc import ABC, abstractmethod
from typing import List
from models import AdItem

class BaseScraper(ABC):
    """Interface abstrata padronizada para coletores de ofertas."""

    @abstractmethod
    async def search(self, query: str) -> List[AdItem]:
        """Busca anúncios na plataforma e retorna lista normalizada de AdItem."""
        pass
