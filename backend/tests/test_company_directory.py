import asyncio

import httpx
import pytest
import respx

from app.company_directory import NASDAQ_FILES, Company, CompanyDirectory, match_companies, parse_listings
from app.transcript_client import ProviderUnavailableError

NASDAQ_URL, OTHER_URL = NASDAQ_FILES[0][0], NASDAQ_FILES[1][0]

NASDAQ_TEXT = "\n".join([
    "Symbol|Security Name|Market Category|Test Issue|Financial Status|Round Lot Size|ETF|NextShares",
    "AAPL|Apple Inc. - Common Stock|Q|N|N|100|N|N",
    "PFBC|Preferred Bank - Common Stock|Q|N|N|100|N|N",
    "ADSE|ADS-TEC ENERGY PLC - Ordinary Shares|G|N|N|100|N|N",
    "QQQ|Invesco QQQ Trust, Series 1|G|N|N|100|Y|N",
    "ZVZZT|NASDAQ TEST STOCK|G|Y|N|100|N|N",
    "RGTIW|Rigetti Computing, Inc. - Redeemable warrants, each exercisable for one share|G|N|N|100|N|N",
    "File Creation Time: 0929202603:02|||||||",
])
OTHER_TEXT = "\n".join([
    "ACT Symbol|Security Name|Exchange|CQS Symbol|ETF|Round Lot Size|Test Issue|NASDAQ Symbol",
    "BRK.B|Berkshire Hathaway Inc. New Common Stock|N|BRK.B|N|100|N|BRK=B",
    "ABR$D|Arbor Realty Trust 6.375% Series D Cumulative Redeemable Preferred Stock|N|ABRpD|N|100|N|ABR-D",
    "MLP|Maui Land & Pineapple Company, Inc. Common Stock|N|MLP|N|100|N|MLP",
    "File Creation Time: 0929202603:02||||||",
])


def run(coro):
    return asyncio.run(coro)


def test_parse_keeps_only_company_shares_with_clean_names():
    companies = (
        parse_listings(NASDAQ_TEXT, "Symbol", "Market Category", "Q")
        + parse_listings(OTHER_TEXT, "ACT Symbol", "Exchange", "N")
    )

    # ETF, test listing, warrant, and preferred share are dropped.
    assert {c.symbol: c.name for c in companies} == {
        "AAPL": "Apple Inc.",
        "PFBC": "Preferred Bank",
        "ADSE": "ADS-TEC ENERGY PLC",
        "BRK.B": "Berkshire Hathaway Inc.",
        "MLP": "Maui Land & Pineapple Company, Inc.",
    }
    assert {c.symbol for c in companies if c.top_tier} == {"AAPL", "PFBC", "BRK.B", "MLP"}


COMPANIES = [
    Company("MBOT", "Microbot Medical Inc.", False),
    Company("MSFT", "Microsoft Corporation", True),
    Company("AAPL", "Apple Inc.", True),
    Company("MLP", "Maui Land & Pineapple Company, Inc.", True),
    Company("BAC", "Bank of America Corporation", True),
]


@pytest.mark.parametrize("query, expected", [
    ("aapl", ["AAPL"]),            # exact ticker
    ("apple", ["AAPL"]),           # "Pineapple" doesn't count: matches must start a word
    ("micro", ["MSFT", "MBOT"]),   # same-length names: the top-tier listing ranks first
    ("of america", ["BAC"]),       # can match later words in the name
    ("  ", []),
])
def test_match_companies(query, expected):
    assert [r["symbol"] for r in match_companies(COMPANIES, query)] == expected


def test_match_companies_returns_symbol_and_name_up_to_the_limit():
    many = [Company(f"T{i:03}", f"Test Company {i}", True) for i in range(20)]

    results = match_companies(many, "test")

    assert len(results) == 8
    assert results[0] == {"symbol": "T000", "name": "Test Company 0"}


@respx.mock
def test_directory_downloads_once_and_reuses_the_list():
    nasdaq = respx.get(NASDAQ_URL).mock(return_value=httpx.Response(200, text=NASDAQ_TEXT))
    other = respx.get(OTHER_URL).mock(return_value=httpx.Response(200, text=OTHER_TEXT))
    directory = CompanyDirectory()

    async def two_searches():
        return await directory.search("apple"), await directory.search("berkshire")

    apple, berkshire = run(two_searches())

    assert apple[0] == {"symbol": "AAPL", "name": "Apple Inc."}
    assert berkshire == [{"symbol": "BRK.B", "name": "Berkshire Hathaway Inc."}]
    assert nasdaq.call_count == 1 and other.call_count == 1


@respx.mock
def test_directory_is_unavailable_if_first_download_fails():
    respx.get(NASDAQ_URL).mock(side_effect=httpx.ConnectError("down"))

    with pytest.raises(ProviderUnavailableError, match="unavailable"):
        run(CompanyDirectory().search("apple"))


@respx.mock
def test_directory_keeps_old_list_if_refresh_fails(monkeypatch):
    monkeypatch.setattr("app.company_directory.REFRESH_AFTER_S", 0)  # every search tries to refresh
    nasdaq = respx.get(NASDAQ_URL)
    nasdaq.side_effect = [httpx.Response(200, text=NASDAQ_TEXT), httpx.ConnectError("down")]
    respx.get(OTHER_URL).mock(return_value=httpx.Response(200, text=OTHER_TEXT))
    directory = CompanyDirectory()

    async def two_searches():
        return await directory.search("apple"), await directory.search("apple")

    first, second = run(two_searches())

    assert first == second == [{"symbol": "AAPL", "name": "Apple Inc."}]
    assert nasdaq.call_count == 2


def test_empty_search_does_not_download():
    with respx.mock:
        assert run(CompanyDirectory().search("   ")) == []
        assert not respx.calls
