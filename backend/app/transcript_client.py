import re

import httpx
from .config import settings

EQUIBLES_URL = "https://api.equibles.com/v1"
TURNS_PER_PAGE = 200


class ProviderUnavailableError(Exception):
    pass


def _parse_quarter(quarter: str) -> tuple[int, int]:
    match = re.fullmatch(r"(\d{4})Q([1-4])", quarter.strip().upper())
    if not match:
        raise ValueError(f"Invalid quarter '{quarter}', expected a format like 2026Q1")
    return int(match[1]), int(match[2])


def _to_turn(turn: dict) -> dict:
    role = turn.get("speakerRole") or ""
    # Equibles labels analysts "Analyst — <firm>"; segmentation looks for a plain "Analyst" title.
    title = "Analyst" if role.startswith("Analyst") else role
    return {
        "speaker": turn.get("speakerName") or role or "Unknown",
        "title": title,
        "content": turn.get("text") or "",
    }


def _company_name(event_title: str | None, ticker: str) -> str:
    # "Nvidia Corp Q1 FY2027 Earnings Call" -> "Nvidia Corp"
    match = re.match(r"(.+?)\s+Q[1-4]\s+FY\d{4}\b", event_title or "")
    return match[1] if match else ticker


def _error_message(response: httpx.Response) -> str:
    try:
        return response.json()["error"]["message"]
    except (ValueError, KeyError, TypeError):
        return ""


class TranscriptClient:
    async def fetch_transcript(self, ticker: str, quarter: str) -> dict:
        ticker = ticker.upper()
        if not re.fullmatch(r"[A-Z0-9.\-]{1,10}", ticker):
            raise ValueError(f"Invalid ticker: {ticker}")
        fiscal_year, fiscal_quarter = _parse_quarter(quarter)
        path = f"/stocks/{ticker}/earnings-calls/{fiscal_year}/{fiscal_quarter}/speakers"
        headers = {"Authorization": f"Bearer {settings.equibles_api_key}"}

        turns: list[dict] = []
        async with httpx.AsyncClient(base_url=EQUIBLES_URL, headers=headers, timeout=30) as client:
            while True:
                page = await self._equibles_get(
                    client, path, {"limit": TURNS_PER_PAGE, "offset": len(turns)}, ticker, quarter
                )
                turns.extend(page.get("data") or [])
                if not page.get("hasMore") or not page.get("data"):
                    break

        if not turns:
            raise ValueError(f"No transcript found for {ticker} {quarter}")

        return {
            "ticker": ticker,
            "quarter": quarter,
            "company_name": _company_name(page.get("eventTitle"), ticker),
            "transcript": [_to_turn(t) for t in turns],
        }

    async def _equibles_get(
        self, client: httpx.AsyncClient, path: str, params: dict, ticker: str, quarter: str
    ) -> dict:
        try:
            response = await client.get(path, params=params)
        except httpx.TimeoutException as e:
            raise ProviderUnavailableError("The transcript provider took too long to respond, try again in a minute") from e
        except httpx.HTTPError as e:
            raise ProviderUnavailableError("Couldn't reach the transcript provider, try again in a minute") from e

        if response.status_code == 404:
            if _error_message(response).startswith("Stock"):
                raise ValueError(f"Invalid ticker: {ticker}")
            raise ValueError(f"No transcript found for {ticker} {quarter}")
        if response.status_code == 429:
            raise ValueError("API limit reached: Equibles' daily request quota is used up")
        if response.status_code == 401:
            raise ProviderUnavailableError("The transcript provider rejected the API key")
        if response.is_error:
            raise ProviderUnavailableError(f"The transcript provider returned an error ({response.status_code})")
        return response.json()
