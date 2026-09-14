import httpx
from .config import settings


class TranscriptClient:
    BASE_URL = "https://www.alphavantage.co/query"

    async def fetch_transcript(self, ticker: str, quarter: str) -> dict:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.get(self.BASE_URL, params={
                "function": "EARNINGS_CALL_TRANSCRIPT",
                "symbol": ticker.upper(),
                "quarter": quarter,
                "apikey": settings.alpha_vantage_api_key
            })
            response.raise_for_status()
            data = response.json()

            if "Information" in data:
                raise ValueError(f"API limit reached: {data['Information']}")
            if "Error Message" in data:
                raise ValueError(f"Invalid ticker: {data['Error Message']}")
            if "transcript" not in data:
                raise ValueError(f"No transcript found for {ticker} {quarter}")

            return {
                "ticker": ticker.upper(),
                "quarter": quarter,
                "company_name": data.get("symbol", ticker.upper()),
                "transcript": data["transcript"]
            }

    async def fetch_latest(self, ticker: str) -> dict:
        candidates = [
            "2024Q3", "2024Q2", "2024Q1",
            "2023Q4", "2023Q3", "2023Q2"
        ]
        last_error = None
        for quarter in candidates:
            try:
                return await self.fetch_transcript(ticker, quarter)
            except ValueError as e:
                last_error = e
                continue

        raise ValueError(
            f"No transcript found for {ticker}. "
            f"Last error: {last_error}. Tried quarters: {candidates}"
        )
