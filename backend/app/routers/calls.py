from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import AnalysisOut, EarningsCallOut
from app.services.analysis_service import AnalysisService
from app.services.transcript_service import TranscriptService

router = APIRouter(tags=["calls"])

@router.post("/calls/{ticker}/{quarter}/fetch", response_model=EarningsCallOut)
async def fetch_call(ticker: str, quarter: str, db: Session = Depends(get_db)):
    service = TranscriptService(db)
    return await service.fetch_and_store(ticker, quarter)

@router.post("/calls/{ticker}/{quarter}/analyze", response_model=AnalysisOut)
def analyze_call(ticker: str, quarter: str, db: Session = Depends(get_db)):
    service = AnalysisService(db)
    return service.analyze(ticker, quarter)

@router.get("/calls/{ticker}/{quarter}", response_model=EarningsCallOut)
def get_call(ticker: str, quarter: str, db: Session = Depends(get_db)):
    service = TranscriptService(db)
    call = service.get_existing(ticker, quarter)
    if call is None:
        raise HTTPException(status_code=404, detail=f"No stored transcript for {ticker.upper()} {quarter}")
    return call
