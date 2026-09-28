import { useEffect, useRef, useState } from "react"
import { getRecentAnalyses, searchCompanies } from "../api"

function chipColor(sentiment) {
  if (sentiment === "positive") return "border-green-border text-green"
  if (sentiment === "negative") return "border-red-border text-red"
  return "border-amber-border text-amber"
}

function SearchScreen({ onSubmit, error }) {
  const [ticker, setTicker] = useState("")
  const [quarter, setQuarter] = useState("")
  const [localError, setLocalError] = useState(null)
  const [recent, setRecent] = useState([])
  const [suggestions, setSuggestions] = useState([])
  const [showSuggestions, setShowSuggestions] = useState(false)
  const [suggestionsDisabled, setSuggestionsDisabled] = useState(false)
  const debounceRef = useRef(null)

  useEffect(() => {
    getRecentAnalyses().then(setRecent).catch(() => setRecent([]))
  }, [])

  function handleTickerChange(value) {
    setTicker(value)
    setShowSuggestions(true)

    if (debounceRef.current) clearTimeout(debounceRef.current)

    const query = value.trim()
    if (query.length < 2 || suggestionsDisabled) {
      setSuggestions([])
      return
    }

    debounceRef.current = setTimeout(() => {
      searchCompanies(query)
        .then(setSuggestions)
        .catch((err) => {
          setSuggestions([])
          // Once we hit a rate limit, stop retrying on every keystroke —
          // it won't succeed again until the quota resets.
          if (err.message?.toLowerCase().includes("api limit reached")) {
            setSuggestionsDisabled(true)
          }
        })
    }, 400)
  }

  function selectSuggestion(symbol) {
    setTicker(symbol)
    setSuggestions([])
    setShowSuggestions(false)
  }

  function handleSubmit(e) {
    e.preventDefault()
    const t = ticker.trim().toUpperCase()
    const q = quarter.trim().toUpperCase()
    if (!t || !q) {
      setLocalError("Enter both a ticker and a quarter (e.g. AAPL, 2026Q3).")
      return
    }
    setLocalError(null)
    onSubmit(t, q)
  }

  const shownError = localError || error

  return (
    <div className="flex-1 flex flex-col items-center justify-center px-6 py-8 text-center">
      <div className="flex items-center gap-2.5 font-mono text-[10px] tracking-[0.14em] text-amber mb-5">
        <span className="w-10 h-px bg-amber-border" />
        EARNINGS CALL ANALYZER
        <span className="w-10 h-px bg-amber-border" />
      </div>
      <h1 className="text-3xl font-semibold text-ink leading-tight mb-3 max-w-lg">
        What did <span className="text-amber">management</span> actually say?
      </h1>
      <p className="text-[13px] text-muted mb-8 max-w-sm leading-relaxed">
        Enter a ticker or a company and quarter to get an AI-powered breakdown of the earnings call — sentiment, summary, themes, guidance, and risks.
      </p>

      <form onSubmit={handleSubmit} className="flex flex-col gap-2 w-full max-w-md mb-2">
        <div className="flex flex-col gap-2">
          <div className="relative flex-1">
            <input
              type="text"
              placeholder="Ticker or Company, e.g. Apple"
              value={ticker}
              onChange={(e) => handleTickerChange(e.target.value)}
              onFocus={() => setShowSuggestions(true)}
              onBlur={() => setTimeout(() => setShowSuggestions(false), 150)}
              autoComplete="off"
              className="w-full bg-navy-2 border border-border-amber rounded-md px-4 py-2.5 font-mono text-sm text-ink uppercase tracking-wide placeholder:normal-case placeholder:text-muted placeholder:tracking-normal outline-none focus:border-amber-border"
            />
            {showSuggestions && !suggestionsDisabled && suggestions.length > 0 && (
              <div className="absolute top-full left-0 right-0 mt-1 bg-navy-2 border border-border-amber rounded-md overflow-hidden z-10 text-left">
                {suggestions.map((s) => (
                  <button
                    key={s.symbol}
                    type="button"
                    onClick={() => selectSuggestion(s.symbol)}
                    className="w-full px-3 py-2 flex items-center justify-between gap-2 hover:bg-navy-3 transition-colors"
                  >
                    <span className="font-mono text-xs text-ink flex-shrink-0">{s.symbol}</span>
                    <span className="text-xs text-muted truncate">{s.name}</span>
                  </button>
                ))}
              </div>
            )}
          </div>
          {suggestionsDisabled && (
            <p className="text-[11px] text-muted text-left -mt-1">
              Company search unavailable (API limit reached) — you can still enter a ticker directly.
            </p>
          )}
          <input
            type="text"
            placeholder="Quarter, e.g. 2026Q3"
            value={quarter}
            onChange={(e) => setQuarter(e.target.value)}
            className="flex-1 bg-navy-2 border border-border-amber rounded-md px-4 py-2.5 font-mono text-sm text-ink uppercase tracking-wide placeholder:normal-case placeholder:text-muted placeholder:tracking-normal outline-none focus:border-amber-border"
          />
        </div>
        <button
          type="submit"
          className="w-full px-6 py-2.5 bg-amber text-[#1A0E00] font-semibold text-sm rounded-md hover:opacity-90 hover:shadow-md transition-all"
        >
          Analyze →
        </button>
      </form>
      {shownError && <p className="text-sm text-red mb-4">{shownError}</p>}

      {recent.length > 0 && (
        <div className="mt-6">
          <div className="font-mono text-[10px] text-muted tracking-wider mb-2.5">RECENTLY ANALYZED</div>
          <div className="flex gap-1.5 flex-wrap justify-center">
            {recent.map((r) => (
              <button
                key={r.ticker}
                onClick={() => onSubmit(r.ticker, r.quarter)}
                className={`font-mono text-[11px] px-2.5 py-1 rounded border ${chipColor(r.overall_sentiment)} hover:opacity-80 transition-opacity`}
              >
                {r.ticker} <span className="opacity-70 ml-1">{r.sentiment_score?.toFixed(2)}</span>
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

export default SearchScreen
