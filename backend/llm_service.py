import os
import json
from openai import AsyncOpenAI
from pydantic import ValidationError

from models import ExtractedDeal, DealStatus
from database import update_deal_status, update_deal_extracted, get_deal_by_id

client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

MAX_RETRIES = 2

EXTRACTION_PROMPT = """
Extract deal information from the following text and return valid JSON matching this schema:

{
  "company_name": "string (required)",
  "founders": ["string"],
  "sector": "string",
  "geography": "string",
  "stage": "Seed | Series A | Series B | Series C | Growth | Other",
  "round_size": "string (e.g., '$5M', '$10-15M')",
  "metrics": {"key": "value"},
  "investment_brief": ["bullet 1", "bullet 2", ... (5-10 key investment highlights)],
  "tags": ["fintech", "deep tech", "climate tech", "Seed", "Series A", ...]
}

Rules:
- company_name is required, extract from context if not explicit
- investment_brief should have 5-10 concise bullet points summarizing key investment highlights
- metrics should capture any quantitative data (revenue, growth, users, etc.)
- Return ONLY valid JSON, no markdown or explanation

Text:
{raw_text}
"""

REPAIR_PROMPT = """
Your previous response had validation errors:
{errors}

Please fix and return valid JSON matching the schema. Return ONLY the corrected JSON.
"""


async def extract_deal_data(raw_text: str) -> ExtractedDeal:
    """Extract structured data from raw deal text using LLM."""
    prompt = EXTRACTION_PROMPT.format(raw_text=raw_text)

    response = await client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_object"},
        temperature=0.1,
    )

    return response.choices[0].message.content


async def validate_and_parse(json_str: str) -> ExtractedDeal:
    """Validate JSON string against ExtractedDeal schema."""
    data = json.loads(json_str)
    return ExtractedDeal(**data)


async def repair_json(original_response: str, errors: str) -> str:
    """Ask LLM to repair invalid JSON based on validation errors."""
    prompt = REPAIR_PROMPT.format(errors=errors)

    response = await client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "user", "content": f"Original response:\n{original_response}"},
            {"role": "user", "content": prompt},
        ],
        response_format={"type": "json_object"},
        temperature=0.1,
    )

    return response.choices[0].message.content


async def process_deal_extraction(deal_id: str, ws_manager=None):
    """
    Process deal extraction with retry logic.

    Status flow: pending → extracting → validating → completed/failed
    """
    try:
        # Update status to extracting
        await update_deal_status(deal_id, DealStatus.EXTRACTING)
        if ws_manager:
            await ws_manager.broadcast_status(deal_id, DealStatus.EXTRACTING)

        # Get deal data
        deal = await get_deal_by_id(deal_id)
        if not deal:
            raise ValueError(f"Deal {deal_id} not found")

        # Extract data from LLM
        json_response = await extract_deal_data(deal.raw_text)

        # Update status to validating
        await update_deal_status(deal_id, DealStatus.VALIDATING)
        if ws_manager:
            await ws_manager.broadcast_status(deal_id, DealStatus.VALIDATING)

        # Try to validate
        last_error = None
        for attempt in range(MAX_RETRIES):
            try:
                extracted = await validate_and_parse(json_response)

                # Success - update deal with extracted data
                await update_deal_extracted(deal_id, extracted)
                if ws_manager:
                    await ws_manager.broadcast_status(deal_id, DealStatus.COMPLETED)
                return

            except (json.JSONDecodeError, ValidationError) as e:
                last_error = str(e)
                if attempt < MAX_RETRIES - 1:
                    # Try to repair
                    json_response = await repair_json(json_response, last_error)

        # All retries exhausted - mark as failed
        await update_deal_status(deal_id, DealStatus.FAILED, last_error)
        if ws_manager:
            await ws_manager.broadcast_status(deal_id, DealStatus.FAILED, last_error)

    except Exception as e:
        # Unexpected error - mark as failed
        await update_deal_status(deal_id, DealStatus.FAILED, str(e))
        if ws_manager:
            await ws_manager.broadcast_status(deal_id, DealStatus.FAILED, str(e))
