import asyncio
import httpx
import pytest
import respx

from app.transcript_client import ProviderUnavailableError, TranscriptClient

EQUIBLES_URL = "https://api.equibles.com/v1"
NVDA_SPEAKERS = f"{EQUIBLES_URL}/stocks/NVDA/earnings-calls/2027/1/speakers"

OPERATOR = {"speakerName": None, "speakerRole": "Operator", "text": "Welcome to the call."}
CFO = {"speakerName": "Colette Kress", "speakerRole": "CFO", "text": "Great quarter."}
ANALYST = {"speakerName": "Joseph Moore", "speakerRole": "Analyst — Morgan Stanley", "text": "A question."}


def run(coro):
    return asyncio.run(coro)


def speakers_page(turns, has_more=False):
    return {"eventTitle": "Nvidia Corp Q1 FY2027 Earnings Call", "hasMore": has_more, "data": turns}


def not_found(message):
    return httpx.Response(404, json={"error": {"code": "not_found", "message": message, "status": 404}})



@respx.mock
def test_fetch_transcript_maps_equibles_turns():
    respx.get(NVDA_SPEAKERS).mock(return_value=httpx.Response(200, json=speakers_page([OPERATOR, CFO, ANALYST])))

    result = run(TranscriptClient().fetch_transcript("nvda", "2027Q1"))

    assert result["ticker"] == "NVDA"
    assert result["quarter"] == "2027Q1"
    assert result["company_name"] == "Nvidia Corp"
    assert result["transcript"] == [
        {"speaker": "Operator", "title": "Operator", "content": "Welcome to the call."},
        {"speaker": "Colette Kress", "title": "CFO", "content": "Great quarter."},
        {"speaker": "Joseph Moore", "title": "Analyst", "content": "A question."},
    ]


@respx.mock
def test_fetch_transcript_follows_pages():
    route = respx.get(NVDA_SPEAKERS)
    route.side_effect = [
        httpx.Response(200, json=speakers_page([OPERATOR, CFO], has_more=True)),
        httpx.Response(200, json=speakers_page([ANALYST])),
    ]

    result = run(TranscriptClient().fetch_transcript("NVDA", "2027Q1"))

    assert len(result["transcript"]) == 3
    assert route.calls[1].request.url.params["offset"] == "2"


@respx.mock
def test_unknown_ticker_is_invalid():
    respx.get(f"{EQUIBLES_URL}/stocks/ZZZZQ/earnings-calls/2026/1/speakers").mock(
        return_value=not_found("Stock 'ZZZZQ' not found.")
    )

    with pytest.raises(ValueError, match="Invalid ticker"):
        run(TranscriptClient().fetch_transcript("ZZZZQ", "2026Q1"))


@respx.mock
def test_missing_quarter_is_no_transcript():
    respx.get(f"{EQUIBLES_URL}/stocks/NVDA/earnings-calls/2099/1/speakers").mock(
        return_value=not_found("No earnings-call event found for NVDA FY2099 Q1.")
    )

    with pytest.raises(ValueError, match="No transcript found for NVDA 2099Q1"):
        run(TranscriptClient().fetch_transcript("NVDA", "2099Q1"))


@pytest.mark.parametrize("ticker, quarter, message", [
    ("NVDA", "2027", "expected a format like"),
    ("NVDA", "Q1 2027", "expected a format like"),
    ("NVDA", "2027Q5", "expected a format like"),
    ("../admin", "2027Q1", "Invalid ticker"),
])
@respx.mock
def test_bad_input_is_rejected_before_any_request(ticker, quarter, message):
    with pytest.raises(ValueError, match=message):
        run(TranscriptClient().fetch_transcript(ticker, quarter))
    assert not respx.calls


@respx.mock
def test_equibles_quota_used_up():
    respx.get(NVDA_SPEAKERS).mock(return_value=httpx.Response(429, json={"error": {"code": "rate_limited"}}))

    with pytest.raises(ValueError, match="API limit reached"):
        run(TranscriptClient().fetch_transcript("NVDA", "2027Q1"))


@respx.mock
def test_equibles_timeout_is_unavailable():
    respx.get(NVDA_SPEAKERS).mock(side_effect=httpx.ReadTimeout("timed out"))

    with pytest.raises(ProviderUnavailableError, match="took too long"):
        run(TranscriptClient().fetch_transcript("NVDA", "2027Q1"))


@respx.mock
def test_rejected_key_is_unavailable():
    respx.get(NVDA_SPEAKERS).mock(
        return_value=httpx.Response(401, json={"error": {"code": "unauthorized", "message": "Invalid API key."}})
    )

    with pytest.raises(ProviderUnavailableError, match="rejected the API key"):
        run(TranscriptClient().fetch_transcript("NVDA", "2027Q1"))
