import os
import pytest
from models import AdItem
from database import DatabaseManager

@pytest.fixture
def temp_db(tmp_path):
    db_file = tmp_path / "test_deals.db"
    mgr = DatabaseManager(db_path=str(db_file))
    yield mgr

def test_database_initialization_and_deduplication(temp_db):
    ad = AdItem(
        id="olx-998877",
        title="MacBook Air M2 256GB Cinza Espacial",
        price=4500.0,
        url="https://olx.com.br/item/998877",
        location="Rio de Janeiro - RJ",
        has_delivery=True
    )

    # Initial check: not seen
    assert temp_db.is_ad_seen(ad.id) is False
    assert temp_db.get_total_seen() == 0

    # Mark as seen
    temp_db.mark_ad_seen(ad)

    # Subsequent check: seen
    assert temp_db.is_ad_seen(ad.id) is True
    assert temp_db.get_total_seen() == 1

    # Re-inserting the same ad should not raise error (idempotent)
    temp_db.mark_ad_seen(ad)
    assert temp_db.get_total_seen() == 1
