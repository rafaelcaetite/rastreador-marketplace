import os
from dataclasses import dataclass, field
from typing import List
from dotenv import load_dotenv

load_dotenv()

@dataclass
class Config:
    telegram_token: str = ""
    telegram_chat_id: str = ""
    query: str = "Macbook Air M2"
    min_price: float = 3000.0
    max_price: float = 5000.0
    require_delivery: bool = True
    interval_minutes: int = 10
    db_path: str = "deals.db"
    dry_run: bool = False
    positive_keywords: List[str] = field(default_factory=lambda: ["macbook", "m2"])
    negative_keywords: List[str] = field(default_factory=lambda: [
        "peça", "peças", "defeito", "quebrado", "sucata", "bloqueado", 
        "icloud", "compro", "apenas caixa", "capinha", "carregador", 
        "tela trincada", "acessório", "acessorio", "bag", "case"
    ])

    @classmethod
    def load_from_env(cls) -> "Config":
        token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
        chat_id = os.getenv("TELEGRAM_CHAT_ID", "").strip()
        query = os.getenv("SEARCH_QUERY", "Macbook Air M2").strip()
        min_p = float(os.getenv("MIN_PRICE", "3000.0"))
        max_p = float(os.getenv("MAX_PRICE", "5000.0"))
        req_deliv = os.getenv("REQUIRE_DELIVERY", "true").lower() in ("true", "1", "yes")
        interval = int(os.getenv("INTERVAL_MINUTES", "10"))
        db = os.getenv("DB_PATH", "deals.db")
        dry = os.getenv("DRY_RUN", "false").lower() in ("true", "1", "yes") or not token

        return cls(
            telegram_token=token,
            telegram_chat_id=chat_id,
            query=query,
            min_price=min_p,
            max_price=max_p,
            require_delivery=req_deliv,
            interval_minutes=interval,
            db_path=db,
            dry_run=dry,
        )
