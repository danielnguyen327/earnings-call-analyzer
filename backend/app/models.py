from sqlalchemy import (
    Column, Integer, String, Float,
    DateTime, JSON, Text, Index
)
from sqlalchemy.sql import func
from .database import Base


class EarningsCall(Base):
    """Raw transcript data fetched from Alpha Vantage."""
    __tablename__ = "earnings_calls"

    id             = Column(Integer, primary_key=True, index=True)
    ticker         = Column(String(10), nullable=False, index=True)
    company_name   = Column(String(200))
    quarter        = Column(String(10), nullable=False)  # e.g. "2026Q1"
    transcript_raw = Column(Text)
    fetched_at     = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        Index("ix_earnings_ticker_quarter", "ticker", "quarter", unique=True),
    )


class Analysis(Base):
    """Gemini AI analysis result for an earnings call."""
    __tablename__ = "analyses"

    id                    = Column(Integer, primary_key=True, index=True)
    ticker                = Column(String(10), nullable=False, index=True)
    quarter               = Column(String(10), nullable=False)
    overall_sentiment     = Column(String(20))   # positive/cautious/negative
    sentiment_score       = Column(Float)         # 0.0 to 1.0
    management_confidence = Column(Float)         # 0.0 to 1.0
    key_themes            = Column(JSON)          # ["theme1", "theme2", ...]
    forward_guidance      = Column(Text)
    guidance_tone         = Column(String(20))    # optimistic/neutral/cautious
    risk_factors          = Column(JSON)          # ["risk1", "risk2", ...]
    summary               = Column(Text)
    segment_sentiments    = Column(JSON)          # [0.7, 0.8, 0.6] — 3 values
    created_at            = Column(DateTime(timezone=True), server_default=func.now())
    updated_at            = Column(DateTime(timezone=True), onupdate=func.now())

    __table_args__ = (
        Index("ix_analyses_ticker_quarter", "ticker", "quarter", unique=True),
    )