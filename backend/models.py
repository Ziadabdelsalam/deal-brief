from pydantic import BaseModel, Field, field_validator
from typing import Optional
from datetime import datetime
from enum import Enum


class DealStatus(str, Enum):
    PENDING = "pending"
    EXTRACTING = "extracting"
    VALIDATING = "validating"
    COMPLETED = "completed"
    FAILED = "failed"


class ExtractedDeal(BaseModel):
    """Schema for LLM-extracted deal information."""
    company_name: str = Field(..., min_length=1)
    founders: list[str] = Field(default_factory=list)
    sector: str = Field(default="")
    geography: str = Field(default="")
    stage: str = Field(default="")
    round_size: str = Field(default="")
    metrics: dict[str, str] = Field(default_factory=dict)
    investment_brief: list[str] = Field(..., min_length=1, max_length=15)
    tags: list[str] = Field(default_factory=list)

    @field_validator("investment_brief")
    @classmethod
    def validate_investment_brief(cls, v: list[str]) -> list[str]:
        if len(v) < 1:
            raise ValueError("investment_brief must have at least 1 bullet point")
        return v


class DealCreate(BaseModel):
    """Request body for creating a new deal."""
    raw_text: str = Field(..., min_length=1)


class DealResponse(BaseModel):
    """Response model for deal endpoints."""
    id: str
    content_hash: str
    raw_text: str
    status: DealStatus
    last_error: Optional[str] = None
    company_name: Optional[str] = None
    founders: Optional[list[str]] = None
    sector: Optional[str] = None
    geography: Optional[str] = None
    stage: Optional[str] = None
    round_size: Optional[str] = None
    metrics: Optional[dict[str, str]] = None
    investment_brief: Optional[list[str]] = None
    tags: Optional[list[str]] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class DealListResponse(BaseModel):
    """Response model for listing deals."""
    deals: list[DealResponse]


class WebSocketMessage(BaseModel):
    """WebSocket message format."""
    type: str
    deal_id: str
    status: DealStatus
    data: Optional[dict] = None
    error: Optional[str] = None
