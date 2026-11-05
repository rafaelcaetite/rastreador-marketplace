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
    image_url: Optional[str] = None
    created_at: Optional[str] = None
