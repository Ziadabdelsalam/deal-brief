import aiosqlite
import json
import os
from datetime import datetime
from typing import Optional
from models import DealStatus, DealResponse, ExtractedDeal

DATABASE_PATH = os.getenv("DATABASE_PATH", "./data/deals.db")
MIGRATIONS_PATH = os.getenv("MIGRATIONS_PATH", "./migrations")


async def init_db():
    """Initialize database and run migrations."""
    os.makedirs(os.path.dirname(DATABASE_PATH), exist_ok=True)

    async with aiosqlite.connect(DATABASE_PATH) as db:
        migration_file = os.path.join(MIGRATIONS_PATH, "001_initial.sql")
        if os.path.exists(migration_file):
            with open(migration_file) as f:
                await db.executescript(f.read())
            await db.commit()


async def get_db():
    """Get database connection."""
    db = await aiosqlite.connect(DATABASE_PATH)
    db.row_factory = aiosqlite.Row
    return db


def row_to_deal_response(row: aiosqlite.Row) -> DealResponse:
    """Convert database row to DealResponse."""
    return DealResponse(
        id=row["id"],
        content_hash=row["content_hash"],
        raw_text=row["raw_text"],
        status=DealStatus(row["status"]),
        last_error=row["last_error"],
        company_name=row["company_name"],
        founders=json.loads(row["founders"]) if row["founders"] else None,
        sector=row["sector"],
        geography=row["geography"],
        stage=row["stage"],
        round_size=row["round_size"],
        metrics=json.loads(row["metrics"]) if row["metrics"] else None,
        investment_brief=json.loads(row["investment_brief"]) if row["investment_brief"] else None,
        tags=json.loads(row["tags"]) if row["tags"] else None,
        created_at=datetime.fromisoformat(row["created_at"]),
        updated_at=datetime.fromisoformat(row["updated_at"]),
    )


async def create_deal(deal_id: str, content_hash: str, raw_text: str) -> DealResponse:
    """Create a new deal in pending status."""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        now = datetime.utcnow().isoformat()
        await db.execute(
            """
            INSERT INTO deals (id, content_hash, raw_text, status, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (deal_id, content_hash, raw_text, DealStatus.PENDING.value, now, now),
        )
        await db.commit()

        cursor = await db.execute("SELECT * FROM deals WHERE id = ?", (deal_id,))
        row = await cursor.fetchone()
        return row_to_deal_response(row)


async def get_deal_by_hash(content_hash: str) -> Optional[DealResponse]:
    """Get deal by content hash for dedupe check."""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT * FROM deals WHERE content_hash = ?", (content_hash,)
        )
        row = await cursor.fetchone()
        if row:
            return row_to_deal_response(row)
        return None


async def get_deal_by_id(deal_id: str) -> Optional[DealResponse]:
    """Get deal by ID."""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute("SELECT * FROM deals WHERE id = ?", (deal_id,))
        row = await cursor.fetchone()
        if row:
            return row_to_deal_response(row)
        return None


async def list_deals(limit: int = 10) -> list[DealResponse]:
    """List latest deals."""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT * FROM deals ORDER BY created_at DESC LIMIT ?", (limit,)
        )
        rows = await cursor.fetchall()
        return [row_to_deal_response(row) for row in rows]


async def update_deal_status(
    deal_id: str, status: DealStatus, last_error: Optional[str] = None
) -> Optional[DealResponse]:
    """Update deal status."""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        now = datetime.utcnow().isoformat()
        await db.execute(
            """
            UPDATE deals SET status = ?, last_error = ?, updated_at = ?
            WHERE id = ?
            """,
            (status.value, last_error, now, deal_id),
        )
        await db.commit()
        return await get_deal_by_id(deal_id)


async def update_deal_extracted(
    deal_id: str, extracted: ExtractedDeal
) -> Optional[DealResponse]:
    """Update deal with extracted data."""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        now = datetime.utcnow().isoformat()
        await db.execute(
            """
            UPDATE deals SET
                status = ?,
                company_name = ?,
                founders = ?,
                sector = ?,
                geography = ?,
                stage = ?,
                round_size = ?,
                metrics = ?,
                investment_brief = ?,
                tags = ?,
                updated_at = ?
            WHERE id = ?
            """,
            (
                DealStatus.COMPLETED.value,
                extracted.company_name,
                json.dumps(extracted.founders),
                extracted.sector,
                extracted.geography,
                extracted.stage,
                extracted.round_size,
                json.dumps(extracted.metrics),
                json.dumps(extracted.investment_brief),
                json.dumps(extracted.tags),
                now,
                deal_id,
            ),
        )
        await db.commit()
        return await get_deal_by_id(deal_id)
