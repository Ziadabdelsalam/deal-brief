import hashlib
import uuid
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware

from models import DealCreate, DealResponse, DealListResponse, DealStatus
from database import (
    init_db,
    create_deal,
    get_deal_by_hash,
    get_deal_by_id,
    list_deals,
    update_deal_status,
)

MAX_INPUT_SIZE = 10 * 1024  # 10KB


def compute_content_hash(text: str) -> str:
    """Compute SHA-256 hash of normalized text for deduplication."""
    normalized = " ".join(text.lower().split())
    return hashlib.sha256(normalized.encode()).hexdigest()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize database on startup."""
    await init_db()
    yield


app = FastAPI(
    title="Deal Brief API",
    description="LLM-powered deal text extraction pipeline",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


@app.post("/api/deals", response_model=DealResponse, status_code=201)
async def create_deal_endpoint(
    deal: DealCreate, background_tasks: BackgroundTasks
) -> DealResponse:
    """Submit new deal text for extraction."""
    # Check input size limit
    if len(deal.raw_text.encode("utf-8")) > MAX_INPUT_SIZE:
        raise HTTPException(
            status_code=413,
            detail=f"Input too large. Maximum size is {MAX_INPUT_SIZE // 1024}KB (~2,500 words)",
        )

    # Compute hash for deduplication
    content_hash = compute_content_hash(deal.raw_text)

    # Check for duplicate
    existing = await get_deal_by_hash(content_hash)
    if existing:
        raise HTTPException(
            status_code=409,
            detail={"message": "Duplicate deal detected", "existing_id": existing.id},
        )

    # Create new deal
    deal_id = str(uuid.uuid4())
    new_deal = await create_deal(deal_id, content_hash, deal.raw_text)

    # Queue extraction task (will be implemented in Step 3)
    # background_tasks.add_task(process_deal_extraction, deal_id)

    return new_deal


@app.get("/api/deals", response_model=DealListResponse)
async def list_deals_endpoint() -> DealListResponse:
    """List latest 10 deals."""
    deals = await list_deals(limit=10)
    return DealListResponse(deals=deals)


@app.get("/api/deals/{deal_id}", response_model=DealResponse)
async def get_deal_endpoint(deal_id: str) -> DealResponse:
    """Get deal by ID."""
    deal = await get_deal_by_id(deal_id)
    if not deal:
        raise HTTPException(status_code=404, detail="Deal not found")
    return deal
