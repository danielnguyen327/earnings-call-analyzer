from sqlalchemy.orm import Session

from app.models import EarningsCall
from app.segmentation import segment_transcript, flatten_turns
from app.transcript_client import TranscriptClient

class TranscriptService:
    def __init__(self, db: Session, client: TranscriptClient | None = None):
        self.db = db
        self.client = client or TranscriptClient()

    def get_existing(self, ticker: str, quarter: str) -> EarningsCall | None:
        return (
            self.db.query(EarningsCall)
            .filter(EarningsCall.ticker == ticker.upper(), EarningsCall.quarter == quarter)
            .first()
        )
    def _store(self, data: dict) -> EarningsCall:
        turns = data["transcript"]
        call = EarningsCall(
            ticker = data["ticker"],
            company_name = data["company_name"],
            quarter = data["quarter"],
            transcript_raw = flatten_turns(turns),
            segments = segment_transcript(turns),
        )
        self.db.add(call)
        self.db.commit()
        self.db.refresh(call)
        return call

    async def fetch_and_store(self, ticker: str, quarter: str) -> EarningsCall:
        """Fetch a transcript for a specific ticker+quarter and store it.
        Returns the existing row without calling the API if already fetched."""
        existing = self.get_existing(ticker, quarter)
        if existing is not None:
            return existing

        data = await self.client.fetch_transcript(ticker, quarter)
        return self._store(data)

    async def fetch_latest_and_store(self, ticker: str) -> EarningsCall:
        """Fetch the most recent available transcript for a ticker.
        Note: we don't know which quarter it'll be until the API responds,
        so this always makes at least one API call — but never stores a
        duplicate row if that quarter was already fetched.
        """
        data = await self.client.fetch_latest(ticker)
        existing = self.get_existing(data["ticker"], data["quarter"])
        if existing is not None:
            return existing
        return self._store(data)
    