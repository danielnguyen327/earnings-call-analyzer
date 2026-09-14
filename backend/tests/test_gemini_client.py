from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from app.services.gemini_client import GeminiAnalysisClient, GeminiAnalysisError

VALID_JSON = (
    '{"overall_sentiment": "positive", "sentiment_score": 0.8, '
    '"management_confidence": 0.7, "key_themes": ["growth"], '
    '"forward_guidance": "Guidance text.", "guidance_tone": "optimistic", '
    '"risk_factors": ["risk"], "summary": "Summary text.", '
    '"segment_sentiments": [0.8, 0.7, 0.9]}'
)


def _response(text):
    return SimpleNamespace(text=text)


def _segments():
    return {"prepared_remarks": "a", "qa": "b", "closing": "c"}


def test_analyze_succeeds_on_first_try():
    client = GeminiAnalysisClient()
    client.client.models.generate_content = MagicMock(return_value=_response(VALID_JSON))

    result = client.analyze("TestCorp", "2024Q3", _segments())

    assert result.overall_sentiment == "positive"
    assert client.client.models.generate_content.call_count == 1


def test_analyze_retries_once_on_malformed_json_then_succeeds():
    client = GeminiAnalysisClient()
    client.client.models.generate_content = MagicMock(
        side_effect=[_response("not json"), _response(VALID_JSON)]
    )

    result = client.analyze("TestCorp", "2024Q3", _segments())

    assert result.overall_sentiment == "positive"
    assert client.client.models.generate_content.call_count == 2


def test_analyze_raises_after_exhausting_retries():
    client = GeminiAnalysisClient()
    client.client.models.generate_content = MagicMock(return_value=_response("still not json"))

    with pytest.raises(GeminiAnalysisError):
        client.analyze("TestCorp", "2024Q3", _segments())

    assert client.client.models.generate_content.call_count == 2