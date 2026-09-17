import asyncio
import httpx
import pytest
import respx

from app.transcript_client import TranscriptClient, _recent_quarters

BASE_URL = "https://www.alphavantage.co/query"

def run(coro):
   return asyncio.run(coro)

@respx.mock
def test_fetch_transcrip_success():
    respx.get(BASE_URL).mock(return_value=httpx.Response(200, json={
      "symbol": "AAPL",
      "quarter": "2024Q3",
      "transcript": [
          {"speaker": "Tim Cook", "title": "CEO", "content": "Great quarter.", "sentiment": "0.5"}
      ]
    }))

    result = run(TranscriptClient().fetch_transcript("aapl", "2024Q3"))

    assert result["ticker"] == "AAPL"
    assert result["quarter"] == "2024Q3"
    assert result["company_name"] == "AAPL"
    assert result["transcript"][0]["speaker"] == "Tim Cook"

@respx.mock
def test_fetch_transcript_api_limit_reached():
    respx.get(BASE_URL).mock(return_value=httpx.Response(200, json={
        "Information": "Thank you for using Alpha Vantage! Our standard API rate limit is 25 requests per day.",
    }))

    with pytest.raises(ValueError, match="API limit reached"):
        run(TranscriptClient().fetch_transcript("AAPL", "2024Q3"))


@respx.mock
def test_fetch_transcript_invalid_ticker():
    respx.get(BASE_URL).mock(return_value=httpx.Response(200, json={
        "Error Message": "Invalid API call.",
    }))

    with pytest.raises(ValueError, match="Invalid ticker"):
        run(TranscriptClient().fetch_transcript("NOTATICKER", "2024Q3"))


@respx.mock
def test_fetch_transcript_no_transcript_found():
    respx.get(BASE_URL).mock(return_value=httpx.Response(200, json={
        "symbol": "AAPL",
        "quarter": "1999Q1",
    }))

    with pytest.raises(ValueError, match="No transcript found"):
        run(TranscriptClient().fetch_transcript("AAPL", "1999Q1"))


@respx.mock
def test_fetch_latest_falls_back_across_quarters():
    third_quarter = _recent_quarters()[2]
    route = respx.get(BASE_URL)
    route.side_effect = [
        httpx.Response(200, json={"symbol": "AAPL"}),  # no transcript key
        httpx.Response(200, json={"symbol": "AAPL"}),  # no transcript key
        httpx.Response(200, json={
            "symbol": "AAPL",
            "transcript": [{"speaker": "CFO", "title": "CFO", "content": "Solid results."}],
        }),
    ]

    result = run(TranscriptClient().fetch_latest("AAPL"))

    assert result["quarter"] == third_quarter
    assert route.call_count == 3


@respx.mock
def test_fetch_latest_raises_when_all_quarters_fail():
    respx.get(BASE_URL).mock(return_value=httpx.Response(200, json={"symbol": "AAPL"}))

    with pytest.raises(ValueError, match="No transcript found for AAPL"):
        run(TranscriptClient().fetch_latest("AAPL"))