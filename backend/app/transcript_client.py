from datetime import date

import httpx
from .config import settings


def _recent_quarters(n: int = 8) -> list[str]:
    """Returns the current quarter and the n-1 quarters before it,
    most recent first, e.g. ["2026Q3", "2026Q2", ..., "2024Q4"].
    """
    today = date.today()
    year, quarter = today.year, (today.month - 1) // 3 + 1
    quarters = []
    for _ in range(n):
        quarters.append(f"{year}Q{quarter}")
        quarter -= 1
        if quarter == 0:
            quarter, year = 4, year - 1
    return quarters


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

    async def search_companies(self, keywords: str) -> list[dict]:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.get(self.BASE_URL, params={
                "function": "SYMBOL_SEARCH",
                "keywords": keywords,
                "apikey": settings.alpha_vantage_api_key
            })
            response.raise_for_status()
            data = response.json()

            if "Information" in data:
                raise ValueError(f"API limit reached: {data['Information']}")

            results = []
            for m in data.get("bestMatches", []):
                if m.get("3. type") == "Equity" and m.get("4. region") == "United States":
                    results.append({
                        "symbol": m.get("1. symbol"),
                        "name": m.get("2. name"),
                        "match_score": float(m.get("9. matchScore", 0)),
                    })
            results.sort(key=lambda r: r["match_score"], reverse=True)
            return results

    async def fetch_latest(self, ticker: str) -> dict:
        candidates = _recent_quarters()
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
