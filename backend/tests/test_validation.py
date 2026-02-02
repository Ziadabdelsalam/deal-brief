import pytest
from unittest.mock import AsyncMock, patch, MagicMock
import json

from models import ExtractedDeal, DealStatus
from llm_service import validate_and_parse, process_deal_extraction


class TestValidateAndParse:
    """Tests for JSON validation against ExtractedDeal schema."""

    @pytest.mark.asyncio
    async def test_valid_json_parses_successfully(self):
        valid_json = json.dumps({
            "company_name": "Acme Corp",
            "founders": ["John Doe", "Jane Smith"],
            "sector": "Fintech",
            "geography": "US",
            "stage": "Series A",
            "round_size": "$10M",
            "metrics": {"ARR": "$2M", "growth": "200%"},
            "investment_brief": [
                "Strong founding team",
                "Large TAM",
                "Product-market fit",
            ],
            "tags": ["fintech", "Series A"],
        })

        result = await validate_and_parse(valid_json)

        assert isinstance(result, ExtractedDeal)
        assert result.company_name == "Acme Corp"
        assert len(result.founders) == 2
        assert len(result.investment_brief) == 3

    @pytest.mark.asyncio
    async def test_missing_required_field_raises_error(self):
        invalid_json = json.dumps({
            "founders": ["John Doe"],
            "sector": "Fintech",
            "investment_brief": ["Point 1"],
        })

        with pytest.raises(Exception):
            await validate_and_parse(invalid_json)

    @pytest.mark.asyncio
    async def test_empty_investment_brief_raises_error(self):
        invalid_json = json.dumps({
            "company_name": "Acme Corp",
            "investment_brief": [],
        })

        with pytest.raises(Exception):
            await validate_and_parse(invalid_json)

    @pytest.mark.asyncio
    async def test_malformed_json_raises_error(self):
        malformed = "{ invalid json }"

        with pytest.raises(json.JSONDecodeError):
            await validate_and_parse(malformed)


class TestProcessDealExtraction:
    """Tests for the extraction pipeline with retry logic."""

    @pytest.mark.asyncio
    async def test_invalid_json_triggers_retry(self):
        """Test that malformed LLM response triggers repair prompt."""
        invalid_response = "{ not valid json }"
        valid_response = json.dumps({
            "company_name": "Test Co",
            "investment_brief": ["Point 1", "Point 2"],
        })

        mock_deal = MagicMock()
        mock_deal.raw_text = "Test deal text"

        call_count = 0

        async def mock_extract(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return invalid_response
            return valid_response

        async def mock_repair(*args, **kwargs):
            return valid_response

        with patch("llm_service.get_deal_by_id", AsyncMock(return_value=mock_deal)), \
             patch("llm_service.update_deal_status", AsyncMock()), \
             patch("llm_service.update_deal_extracted", AsyncMock()) as mock_update, \
             patch("llm_service.extract_deal_data", mock_extract), \
             patch("llm_service.repair_json", mock_repair):

            await process_deal_extraction("test-id")

            mock_update.assert_called_once()
            args = mock_update.call_args[0]
            assert args[0] == "test-id"
            assert isinstance(args[1], ExtractedDeal)

    @pytest.mark.asyncio
    async def test_validation_errors_stored_on_failure(self):
        """Test that persistent failures store last_error."""
        invalid_response = "{ always invalid }"

        mock_deal = MagicMock()
        mock_deal.raw_text = "Test deal text"

        with patch("llm_service.get_deal_by_id", AsyncMock(return_value=mock_deal)), \
             patch("llm_service.update_deal_status", AsyncMock()) as mock_status, \
             patch("llm_service.update_deal_extracted", AsyncMock()), \
             patch("llm_service.extract_deal_data", AsyncMock(return_value=invalid_response)), \
             patch("llm_service.repair_json", AsyncMock(return_value=invalid_response)):

            await process_deal_extraction("test-id")

            # Check that final call was to mark as failed with error
            final_call = mock_status.call_args_list[-1]
            assert final_call[0][1] == DealStatus.FAILED
            assert final_call[0][2] is not None  # last_error should be set

    @pytest.mark.asyncio
    async def test_successful_extraction_marks_completed(self):
        """Test that successful extraction marks deal as completed."""
        valid_response = json.dumps({
            "company_name": "Success Corp",
            "investment_brief": ["Great opportunity"],
        })

        mock_deal = MagicMock()
        mock_deal.raw_text = "Test deal text"

        with patch("llm_service.get_deal_by_id", AsyncMock(return_value=mock_deal)), \
             patch("llm_service.update_deal_status", AsyncMock()) as mock_status, \
             patch("llm_service.update_deal_extracted", AsyncMock()) as mock_update, \
             patch("llm_service.extract_deal_data", AsyncMock(return_value=valid_response)):

            await process_deal_extraction("test-id")

            # Should have updated status to extracting, then validating
            status_calls = [c[0][1] for c in mock_status.call_args_list]
            assert DealStatus.EXTRACTING in status_calls
            assert DealStatus.VALIDATING in status_calls

            # Should have called update_deal_extracted (which sets completed)
            mock_update.assert_called_once()
