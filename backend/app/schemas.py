from datetime import datetime

from pydantic import BaseModel, ConfigDict

class EarningsCallOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id : int
    ticker: str
    company_name: str | None
    quarter: str
    transcript_raw: str | None
    fetched_at: datetime | None

class AnalysisOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    ticker: str
    quarter: str
    overall_sentiment: str | None
    sentiment_score: float | None
    management_confidence: float | None
    key_themes: list[str] | None
    forward_guidance: str | None
    guidance_tone: str | None
    risk_factors: list[str] | None
    summary: str | None
    segment_sentiments: list[float] | None
    created_at: datetime | None
    updated_at: datetime | None