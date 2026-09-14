import asyncio

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app.models import EarningsCall
from app.services.transcript_service import TranscriptService


def run(coro):
    return asyncio.run(coro)


@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


class FakeTranscriptClient:
    def __init__(self, responses=None, latest_response=None):
        self.responses = responses or {}
        self.latest_response = latest_response
        self.fetch_transcript_calls = []
        self.fetch_latest_calls = []

    async def fetch_transcript(self, ticker, quarter):
        self.fetch_transcript_calls.append((ticker, quarter))
        return self.responses[(ticker.upper(), quarter)]

    async def fetch_latest(self, ticker):
        self.fetch_latest_calls.append(ticker)
        return self.latest_response


SAMPLE_TURNS = [
    {"speaker": "IR", "title": "Director of Investor Relations", "content": "Welcome."},
    {"speaker": "CEO", "title": "CEO", "content": "Good quarter."},
    {"speaker": "Analyst A", "title": "Analyst", "content": "Question?"},
    {"speaker": "CEO", "title": "CEO", "content": "Answer."},
    {"speaker": "IR", "title": "Director of Investor Relations", "content": "Thanks, bye."},
]


def sample_data(ticker="AAPL", quarter="2024Q3"):
    return {
        "ticker": ticker,
        "quarter": quarter,
        "company_name": ticker,
        "transcript": SAMPLE_TURNS,
    }


def test_fetch_and_store_creates_row(db_session):
    client = FakeTranscriptClient(responses={("AAPL", "2024Q3"): sample_data()})
    service = TranscriptService(db_session, client=client)

    call = run(service.fetch_and_store("aapl", "2024Q3"))

    assert call.ticker == "AAPL"
    assert call.quarter == "2024Q3"
    assert call.segments["qa"][0]["speaker"] == "Analyst A"
    assert "Good quarter." in call.transcript_raw
    assert client.fetch_transcript_calls == [("aapl", "2024Q3")]


def test_fetch_and_store_skips_api_call_when_already_fetched(db_session):
    client = FakeTranscriptClient(responses={("AAPL", "2024Q3"): sample_data()})
    service = TranscriptService(db_session, client=client)

    first = run(service.fetch_and_store("AAPL", "2024Q3"))
    second = run(service.fetch_and_store("AAPL", "2024Q3"))

    assert first.id == second.id
    assert len(client.fetch_transcript_calls) == 1


def test_fetch_latest_and_store_creates_row(db_session):
    client = FakeTranscriptClient(latest_response=sample_data(quarter="2024Q2"))
    service = TranscriptService(db_session, client=client)

    call = run(service.fetch_latest_and_store("AAPL"))

    assert call.quarter == "2024Q2"
    assert client.fetch_latest_calls == ["AAPL"]


def test_fetch_latest_and_store_skips_duplicate_row(db_session):
    client = FakeTranscriptClient(latest_response=sample_data(quarter="2024Q2"))
    service = TranscriptService(db_session, client=client)

    first = run(service.fetch_latest_and_store("AAPL"))
    second = run(service.fetch_latest_and_store("AAPL"))

    assert first.id == second.id
    assert len(client.fetch_latest_calls) == 2  # API is still called each time
    assert db_session.query(EarningsCall).count() == 1  # but no duplicate row