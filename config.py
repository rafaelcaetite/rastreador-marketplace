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
    """Configurações globais da esteira de monitoramento."""
    
    telegram_token: str = ""
    telegram_chat_id: str = ""
    query: str = "Macbook"
    min_price: float = 1000.0
    max_price: float = 30000.0
    require_delivery: bool = True
    interval_minutes: int = 10
    max_pages: int = 100
    max_days: int = 30
    db_path: str = "deals.db"
    dry_run: bool = False
    google_credentials_file: str = "credentials.json"
    google_sheet_name: str = "Rastreador de Marketplace"
    google_sheet_id: str = ""
    ml_access_token: str = ""
    shopee_cookie: str = ""
    active_sources: List[str] = field(default_factory=lambda: ["olx", "ml", "shopee"])
    positive_keywords: List[str] = field(default_factory=lambda: ["macbook"])
    negative_keywords: List[str] = field(default_factory=lambda: [
        "peça", "peças", "peca", "pecas", "defeito", "quebrado", "sucata", 
        "bloqueado", "icloud", "compro", "apenas caixa", "capinha", "capinhas", 
        "capa", "capas", "carregador", "carregadores", "fonte", "tela trincada", 
        "acessório", "acessorio", "acessórios", "acessorios", "bag", "case", 
        "cases", "kit", "película", "pelicula", "peliculas", "adesivo", 
        "adesivos", "skin", "skins", "hub", "adaptador", "mochila", "suporte", 
        "pasta", "sleeve", "teclado", "mouse", "cooler"
    ])

    @classmethod
    def load_from_env(cls) -> "Config":
        token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
        chat_id = os.getenv("TELEGRAM_CHAT_ID", "").strip()
        query = os.getenv("SEARCH_QUERY", "Macbook").strip()
        min_p = float(os.getenv("MIN_PRICE", "1000.0"))
        max_p = float(os.getenv("MAX_PRICE", "30000.0"))
        req_deliv = os.getenv("REQUIRE_DELIVERY", "true").lower() in ("true", "1", "yes")
        interval = int(os.getenv("INTERVAL_MINUTES", "10"))
        pages = int(os.getenv("MAX_PAGES", "100"))
        days = int(os.getenv("MAX_DAYS", "30"))
        db = os.getenv("DB_PATH", "deals.db")
        dry = os.getenv("DRY_RUN", "false").lower() in ("true", "1", "yes") or not token
        g_cred = os.getenv("GOOGLE_CREDENTIALS_FILE", "credentials.json")
        g_sheet = os.getenv("GOOGLE_SHEET_NAME", "Rastreador de Marketplace")
        g_id = os.getenv("GOOGLE_SHEET_ID", "").strip()
        ml_token = os.getenv("MERCADOLIVRE_ACCESS_TOKEN", "").strip()
        shopee_c = os.getenv("SHOPEE_COOKIE", "").strip()

        sources_raw = os.getenv("ACTIVE_SOURCES", "olx,ml,shopee").lower()
        sources = [s.strip() for s in sources_raw.split(",") if s.strip()]

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
            max_pages=pages,
            max_days=days,
            db_path=db,
            dry_run=dry,
            google_credentials_file=g_cred,
            google_sheet_name=g_sheet,
            google_sheet_id=g_id,
            ml_access_token=ml_token,
            shopee_cookie=shopee_c,
            active_sources=sources,
            positive_keywords=positives
        )
