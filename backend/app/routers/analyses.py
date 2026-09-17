from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Analysis
from app.schemas import AnalysisOut
from app.services.analysis_service import AnalysisService

router = APIRouter(tags=["analysis"])

@router.get("/analyses/{ticker}/{quarter}", response_model=AnalysisOut)
def get_analysis(ticker: str, quarter: str, db: Session = Depends(get_db)):
    service = AnalysisService(db)
    analysis = service.get_existing(ticker, quarter)
    if analysis is None:
        raise HTTPException(status_code=404, detail=f"No analysis for {ticker.upper()} {quarter}")
    return analysis

@router.get("/analyses", response_model=list[AnalysisOut])
def list_analyses(ticker: str, db: Session = Depends(get_db)):
    return (
        db.query(Analysis)
        .filter(Analysis.ticker == ticker.upper())
        .order_by(Analysis.quarter.desc())
        .all()
    )