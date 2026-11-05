import os
from dataclasses import dataclass, field
from typing import List

try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

@dataclass
class Config:
    telegram_token: str = ""
    telegram_chat_id: str = ""
    query: str = "Macbook"
    min_price: float = 1000.0
    max_price: float = 30000.0
    require_delivery: bool = False
    interval_minutes: int = 10
    db_path: str = "deals.db"
    dry_run: bool = False
    google_credentials_file: str = "credentials.json"
    google_sheet_name: str = "Radar de Ofertas - Hardware"
    positive_keywords: List[str] = field(default_factory=lambda: ["macbook"])
    negative_keywords: List[str] = field(default_factory=lambda: [
        "peça", "peças", "defeito", "quebrado", "sucata", "bloqueado", 
        "icloud", "compro", "apenas caixa", "capinha", "carregador", 
        "tela trincada", "acessório", "acessorio", "bag", "case"
    ])

    @classmethod
    def load_from_env(cls) -> "Config":
        token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
        chat_id = os.getenv("TELEGRAM_CHAT_ID", "").strip()
        query = os.getenv("SEARCH_QUERY", "Macbook").strip()
        min_p = float(os.getenv("MIN_PRICE", "1000.0"))
        max_p = float(os.getenv("MAX_PRICE", "30000.0"))
        req_deliv = os.getenv("REQUIRE_DELIVERY", "false").lower() in ("true", "1", "yes")
        interval = int(os.getenv("INTERVAL_MINUTES", "10"))
        db = os.getenv("DB_PATH", "deals.db")
        dry = os.getenv("DRY_RUN", "false").lower() in ("true", "1", "yes") or not token
        g_cred = os.getenv("GOOGLE_CREDENTIALS_FILE", "credentials.json")
        g_sheet = os.getenv("GOOGLE_SHEET_NAME", "Radar de Ofertas - Hardware")

        positives = [p for p in query.lower().split() if len(p) > 2]
        if not positives:
            positives = ["macbook"]

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
            google_credentials_file=g_cred,
            google_sheet_name=g_sheet,
            positive_keywords=positives
        )
