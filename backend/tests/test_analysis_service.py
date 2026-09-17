import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app.models import EarningsCall
from app.services.analysis_service import AnalysisService
from app.services.claude_client import AnalysisResult


@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


class FakeClaudeClient:
    def __init__(self, result: AnalysisResult):
        self.result = result
        self.calls = []

    def analyze(self, company_name, quarter, segments_text):
        self.calls.append((company_name, quarter, segments_text))
        return self.result


SAMPLE_SEGMENTS = {
    "prepared_remarks": [{"speaker": "CEO", "title": "CEO", "content": "Good quarter."}],
    "qa": [{"speaker": "Analyst", "title": "Analyst", "content": "Question?"}],
    "closing": [{"speaker": "IR", "title": "Director of Investor Relations", "content": "Bye."}],
}

SAMPLE_RESULT = AnalysisResult(
    overall_sentiment="positive",
    sentiment_score=0.8,
    management_confidence=0.7,
    key_themes=["growth", "margins"],
    forward_guidance="Guidance is optimistic.",
    guidance_tone="optimistic",
    risk_factors=["competition"],
    summary="Solid quarter overall.",
    segment_sentiments=[0.9, 0.7, 0.8],
)


def _seed_call(db_session, ticker="AAPL", quarter="2024Q3"):
    call = EarningsCall(
        ticker=ticker,
        company_name="Apple Inc.",
        quarter=quarter,
        transcript_raw="full text",
        segments=SAMPLE_SEGMENTS,
    )
    db_session.add(call)
    db_session.commit()
    return call


def test_analyze_creates_row(db_session):
    _seed_call(db_session)
    client = FakeClaudeClient(SAMPLE_RESULT)
    service = AnalysisService(db_session, client=client)

    analysis = service.analyze("aapl", "2024Q3")

    assert analysis.ticker == "AAPL"
    assert analysis.overall_sentiment == "positive"
    assert analysis.segment_sentiments == [0.9, 0.7, 0.8]
    assert len(client.calls) == 1
    assert client.calls[0][0] == "Apple Inc."


def test_analyze_skips_when_already_analyzed(db_session):
    _seed_call(db_session)
    client = FakeClaudeClient(SAMPLE_RESULT)
    service = AnalysisService(db_session, client=client)

    first = service.analyze("AAPL", "2024Q3")
    second = service.analyze("AAPL", "2024Q3")

    assert first.id == second.id
    assert len(client.calls) == 1


def test_analyze_raises_when_transcript_missing(db_session):
    client = FakeClaudeClient(SAMPLE_RESULT)
    service = AnalysisService(db_session, client=client)

    with pytest.raises(ValueError, match="No transcript found"):
        service.analyze("AAPL", "2024Q3")