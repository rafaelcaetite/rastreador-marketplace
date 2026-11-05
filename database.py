import sqlite3
from typing import Optional
from models import AdItem

class DatabaseManager:
    def __init__(self, db_path: str = "deals.db"):
        self.db_path = db_path
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        return sqlite3.connect(self.db_path)

    def _init_db(self) -> None:
        with self._get_connection() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS seen_ads (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    price REAL NOT NULL,
                    url TEXT NOT NULL,
                    location TEXT,
                    has_delivery INTEGER,
                    image_url TEXT,
                    first_seen_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.commit()

    def is_ad_seen(self, ad_id: str) -> bool:
        with self._get_connection() as conn:
            cursor = conn.execute("SELECT 1 FROM seen_ads WHERE id = ?", (str(ad_id),))
            return cursor.fetchone() is not None

    def mark_ad_seen(self, ad: AdItem) -> None:
        with self._get_connection() as conn:
            conn.execute("""
                INSERT OR IGNORE INTO seen_ads (id, title, price, url, location, has_delivery, image_url)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                str(ad.id),
                ad.title,
                ad.price,
                ad.url,
                ad.location,
                1 if ad.has_delivery else 0,
                ad.image_url
            ))
            conn.commit()

    def get_total_seen(self) -> int:
        with self._get_connection() as conn:
            cursor = conn.execute("SELECT COUNT(*) FROM seen_ads")
            row = cursor.fetchone()
            return row[0] if row else 0
