import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app
from app.services.claude_client import AnalysisResult


@pytest.fixture
def client():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(bind=engine)

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()


SAMPLE_TURNS = [
    {"speaker": "IR", "title": "Director of Investor Relations", "content": "Welcome."},
    {"speaker": "CEO", "title": "CEO", "content": "Good quarter."},
    {"speaker": "Analyst A", "title": "Analyst", "content": "Question?"},
    {"speaker": "CEO", "title": "CEO", "content": "Answer."},
    {"speaker": "IR", "title": "Director of Investor Relations", "content": "Bye."},
]

SAMPLE_ANALYSIS_RESULT = AnalysisResult(
    overall_sentiment="positive",
    sentiment_score=0.8,
    management_confidence=0.7,
    key_themes=["growth"],
    forward_guidance="Guidance text.",
    guidance_tone="optimistic",
    risk_factors=["risk"],
    summary="Summary text.",
    segment_sentiments=[0.8, 0.7, 0.9],
)


def test_fetch_then_get_call(client, monkeypatch):
    async def fake_fetch_transcript(self, ticker, quarter):
        return {
            "ticker": ticker.upper(),
            "quarter": quarter,
            "company_name": ticker.upper(),
            "transcript": SAMPLE_TURNS,
        }

    monkeypatch.setattr(
        "app.services.transcript_service.TranscriptClient.fetch_transcript",
        fake_fetch_transcript,
    )

    resp = client.post("/calls/AAPL/2024Q3/fetch")
    assert resp.status_code == 200
    assert resp.json()["ticker"] == "AAPL"

    resp2 = client.get("/calls/AAPL/2024Q3")
    assert resp2.status_code == 200
    assert resp2.json()["quarter"] == "2024Q3"


def test_get_call_not_found(client):
    resp = client.get("/calls/AAPL/2099Q1")
    assert resp.status_code == 404


def test_analyze_then_get_and_list(client, monkeypatch):
    async def fake_fetch_transcript(self, ticker, quarter):
        return {
            "ticker": ticker.upper(),
            "quarter": quarter,
            "company_name": ticker.upper(),
            "transcript": SAMPLE_TURNS,
        }

    monkeypatch.setattr(
        "app.services.transcript_service.TranscriptClient.fetch_transcript",
        fake_fetch_transcript,
    )
    monkeypatch.setattr(
        "app.services.analysis_service.ClaudeAnalysisClient.analyze",
        lambda self, company_name, quarter, segments_text: SAMPLE_ANALYSIS_RESULT,
    )

    client.post("/calls/AAPL/2024Q3/fetch")
    resp = client.post("/calls/AAPL/2024Q3/analyze")
    assert resp.status_code == 200
    assert resp.json()["overall_sentiment"] == "positive"

    resp2 = client.get("/analyses/AAPL/2024Q3")
    assert resp2.status_code == 200

    resp3 = client.get("/analyses", params={"ticker": "AAPL"})
    assert resp3.status_code == 200
    assert len(resp3.json()) == 1


def test_analyze_without_transcript_returns_404(client):
    resp = client.post("/calls/AAPL/2024Q3/analyze")
    assert resp.status_code == 404


def test_fetch_invalid_ticker_returns_400(client, monkeypatch):
    async def fake_fetch_transcript(self, ticker, quarter):
        raise ValueError("Invalid ticker: bad symbol")

    monkeypatch.setattr(
        "app.services.transcript_service.TranscriptClient.fetch_transcript",
        fake_fetch_transcript,
    )

    resp = client.post("/calls/BADTICKER/2024Q3/fetch")
    assert resp.status_code == 400


def test_fetch_api_limit_returns_429(client, monkeypatch):
    async def fake_fetch_transcript(self, ticker, quarter):
        raise ValueError("API limit reached: too many requests")

    monkeypatch.setattr(
        "app.services.transcript_service.TranscriptClient.fetch_transcript",
        fake_fetch_transcript,
    )

    resp = client.post("/calls/AAPL/2024Q3/fetch")
    assert resp.status_code == 429