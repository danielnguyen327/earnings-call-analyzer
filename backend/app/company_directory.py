import asyncio
import re
import time
from dataclasses import dataclass

import httpx

from .transcript_client import ProviderUnavailableError

# Nasdaq's public symbol directory, refreshed daily. Each entry: (url, symbol column,
# the column and value marking the top listing tier: Nasdaq Global Select, or NYSE).
NASDAQ_FILES = [
    ("https://www.nasdaqtrader.com/dynamic/SymDir/nasdaqlisted.txt", "Symbol", "Market Category", "Q"),
    ("https://www.nasdaqtrader.com/dynamic/SymDir/otherlisted.txt", "ACT Symbol", "Exchange", "N"),
]
REFRESH_AFTER_S = 24 * 60 * 60
MAX_RESULTS = 8

_NOT_COMMON_STOCK = re.compile(r"\b(warrants?|units?|rights?|preferred|notes?|debentures?)\b|%", re.IGNORECASE)
_SHARE_TYPES = [
    r"common\s+stock", r"capital\s+stock", r"common\s+shares?", r"ord(inary)?\s+shares?",
    r"american\s+deposit[ao]ry\s+shares?", r"(new\s+york\s+)?regist(ry|ered)\s+shares?",
    r"((common|subordinate|limited|exchangeable)\s+)*voting\s+shares?",
    r"shares?\s+of\s+beneficial\s+interest", r"ads", r"adrs?",
]
# Strips "- Class A Common Stock" and similar from the end of a name. It must follow a space
# (or come right after "." or ")"), so a company named "ADS-TEC" keeps its name.
_SHARE_TYPE_SUFFIX = re.compile(
    r"(?:(?:\s+-)?\s+|(?<=[.)]))(?:new\s+)?(?:class\s+[a-z]\s+)?(?:" + "|".join(_SHARE_TYPES) + r")\b.*$",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class Company:
    symbol: str
    name: str
    top_tier: bool


def parse_listings(text: str, symbol_column: str, tier_column: str, top_tier_value: str) -> list[Company]:
    lines = text.splitlines()
    header = lines[0].split("|")
    companies = []
    for line in lines[1:]:
        row = dict(zip(header, line.split("|")))
        symbol, name = row.get(symbol_column, ""), row.get("Security Name", "")
        if not symbol or row.get("ETF") != "N" or row.get("Test Issue") != "N" or "$" in symbol:
            continue
        # Only the part after " - " describes the security: "Preferred Bank - Common Stock" is a common stock.
        security_type = name.split(" - ", 1)[1] if " - " in name else name
        if _NOT_COMMON_STOCK.search(security_type):
            continue
        clean_name = _SHARE_TYPE_SUFFIX.sub("", name).strip(" -,") or name
        companies.append(Company(symbol, clean_name, row.get(tier_column) == top_tier_value))
    return companies


def match_companies(companies: list[Company], query: str, limit: int = MAX_RESULTS) -> list[dict]:
    q = query.strip().lower()
    if not q:
        return []
    word_start = re.compile(r"\b" + re.escape(q))

    ranked = []
    for c in companies:
        symbol, name = c.symbol.lower(), c.name.lower()
        if symbol == q:
            rank = 0
        elif symbol.startswith(q):
            rank = 1
        elif name.startswith(q):
            rank = 2
        elif word_start.search(name):
            rank = 3
        else:
            continue
        ranked.append(((rank, not c.top_tier, len(c.name), c.symbol), c))
    ranked.sort(key=lambda item: item[0])
    return [{"symbol": c.symbol, "name": c.name} for _, c in ranked[:limit]]


class CompanyDirectory:
    def __init__(self):
        self._companies: list[Company] = []
        self._loaded_at = 0.0
        self._lock = asyncio.Lock()

    async def search(self, query: str) -> list[dict]:
        if not query.strip():
            return []
        return match_companies(await self._get_companies(), query)

    async def _get_companies(self) -> list[Company]:
        async with self._lock:
            if self._companies and time.monotonic() - self._loaded_at < REFRESH_AFTER_S:
                return self._companies
            try:
                companies = []
                async with httpx.AsyncClient(timeout=30) as client:
                    for url, *columns in NASDAQ_FILES:
                        response = await client.get(url)
                        response.raise_for_status()
                        companies.extend(parse_listings(response.text, *columns))
            except httpx.HTTPError as e:
                if self._companies:
                    return self._companies  # keep serving the last list rather than failing
                raise ProviderUnavailableError("Company search is unavailable right now, try again in a minute") from e

            self._companies, self._loaded_at = companies, time.monotonic()
            return self._companies


directory = CompanyDirectory()
