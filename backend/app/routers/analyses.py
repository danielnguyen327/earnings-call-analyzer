from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Analysis
from app.schemas import AnalysisOut
from app.services.analysis_service import AnalysisService

router = APIRouter(tags=["analysis"])

@router.get("/analyses/recent")
def recent_analyses(limit: int = 5, db: Session = Depends(get_db)):
    """Most recently analyzed quarter for each distinct ticker, newest first."""
    subq = (
        db.query(
            Analysis.ticker.label("ticker"),
            func.max(Analysis.created_at).label("latest"),
        )
        .group_by(Analysis.ticker)
        .subquery()
    )
    rows = (
        db.query(Analysis)
        .join(subq, (Analysis.ticker == subq.c.ticker) & (Analysis.created_at == subq.c.latest))
        .order_by(subq.c.latest.desc())
        .limit(limit)
        .all()
    )
    return [
        {
            "ticker": r.ticker,
            "quarter": r.quarter,
            "overall_sentiment": r.overall_sentiment,
            "sentiment_score": r.sentiment_score,
        }
        for r in rows
    ]

@router.get("/analyses/{ticker}/{quarter}", response_model=AnalysisOut)
def get_analysis(ticker: str, quarter: str, db: Session = Depends(get_db)):
    service = AnalysisService(db)
    analysis = service.get_existing(ticker, quarter)
    if analysis is None:
        raise HTTPException(status_code=404, detail=f"No analysis for {ticker.upper()} {quarter}")
    return analysis

@router.get("/analyses", response_model=list[AnalysisOut])
def list_analyses(ticker: str | None = None, db: Session = Depends(get_db)):
    """Lists analyses for one ticker (most recent quarter first), or all
    analyses across every ticker (most recently analyzed first) when no
    ticker is given.
    """
    query = db.query(Analysis)
    if ticker:
        return query.filter(Analysis.ticker == ticker.upper()).order_by(Analysis.quarter.desc()).all()
    return query.order_by(Analysis.created_at.desc()).all()

@router.delete("/analyses")
def clear_analyses(ticker: str | None = None, db: Session = Depends(get_db)):
    """Deletes all analyses, or just one ticker's if given. Does not touch
    the underlying cached transcripts in earnings_calls.
    """
    query = db.query(Analysis)
    if ticker:
        query = query.filter(Analysis.ticker == ticker.upper())
    deleted = query.delete(synchronize_session=False)
    db.commit()
    return {"deleted": deleted}