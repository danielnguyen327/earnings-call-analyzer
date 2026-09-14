from sqlalchemy.orm import Session

from app.models import Analysis, EarningsCall
from app.segmentation import segment_text
from app.services.gemini_client import GeminiAnalysisClient

class AnalysisService:
    def __init__(self, db: Session, client: GeminiAnalysisCleint | None = None):
        self.db = db
        self.client = client or GeminiAnalysisClient()

    def get_existing(self, ticker: str, quarter: str) -> Analysis | None:
        return (
            self.db.query(Analysis)
            .filter(Analysis.ticker == ticker.upper(), Analysis.quarter == quarter)
            .first()
        )

    def analyze(self, ticker: str, quarter: str) -> Analysis:
        ticker = ticker.upper()
        existing = self.get_existing(ticker, quarter)
        if existing is not None:
            return existing
        
        call = (
            self.db.query(EarningsCall)
            .filter(EarningsCall.ticker == ticker, EarningsCall.quarter == quarter)
            .first()
        )
        if call is None:
            raise ValueError(f"No transcript found for {ticker} {quarter} - fetch it first")

        segments_text = segment_text(call.segments)
        result = self.client.analyze(call.company_name or ticker, quarter, segments_text)

        analysis = Analysis(
            ticker=ticker,
            quarter=quarter,
            overall_sentiment=result.overall_sentiment,
            sentiment_score=result.sentiment_score,
            management_confidence=result.management_confidence,
            key_themes=result.key_themes,
            forward_guidance=result.forward_guidance,
            guidance_tone=result.guidance_tone,
            risk_factors=result.risk_factors,
            summary=result.summary,
            segment_sentiments=result.segment_sentiments,
        )
        self.db.add(analysis)
        self.db.commit()
        self.db.refresh(analysis)
        return analysis
  