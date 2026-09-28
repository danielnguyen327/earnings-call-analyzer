import { useEffect, useState } from "react"
import { clearHistory, listAnalyses } from "../api"

const SENTIMENT_BADGE = {
  positive: "border-green-border text-green",
  cautious: "border-amber-border text-amber",
  negative: "border-red-border text-red",
}

const scoreColor = (v) => (v >= 0.7 ? "text-green" : v >= 0.55 ? "text-amber" : "text-red")

function HistoryScreen({ onSelect, onNewSearch }) {
  const [analyses, setAnalyses] = useState([])
  const [loading, setLoading] = useState(true)
  const [clearing, setClearing] = useState(false)

  useEffect(() => {
    listAnalyses().then(setAnalyses).finally(() => setLoading(false))
  }, [])

  function handleClear() {
    if (!window.confirm("Clear all analyzed history? This can't be undone.")) return
    setClearing(true)
    clearHistory()
      .then(() => setAnalyses([]))
      .finally(() => setClearing(false))
  }

  return (
    <div className="flex-1 px-6 py-5 overflow-y-auto">
      <div className="flex items-center justify-between mb-4">
        <div className="font-mono text-[10px] text-muted tracking-wide">ALL ANALYZED EARNINGS CALLS</div>
        {analyses.length > 0 && (
          <button
            onClick={handleClear}
            disabled={clearing}
            className="font-mono text-[10px] px-2.5 py-1 rounded border border-red-border text-red hover:bg-red-soft transition-colors disabled:opacity-50"
          >
            {clearing ? "Clearing..." : "Clear history"}
          </button>
        )}
      </div>

      {loading && <p className="text-sm text-muted">Loading...</p>}
      {!loading && analyses.length === 0 && <p className="text-sm text-muted">No analyses yet.</p>}

      <div className="flex flex-col">
        {analyses.map((a) => (
          <button
            key={a.id}
            onClick={() => onSelect(a.ticker, a.quarter)}
            className="flex items-center gap-3.5 py-3 pl-1.5 border-b border-border-soft last:border-0 rounded hover:bg-navy-2 transition-colors text-left group"
          >
            <div className="font-mono text-[15px] font-bold text-ink group-hover:text-amber" style={{ minWidth: 56 }}>
              {a.ticker}
            </div>
            <div className="flex-1">
              <div className="text-[13px] text-ink font-mono">{a.quarter}</div>
            </div>
            <div className={`font-mono text-sm font-semibold text-right ${scoreColor(a.sentiment_score)}`} style={{ minWidth: 36 }}>
              {a.sentiment_score.toFixed(2)}
            </div>
            <span
              className={`font-mono text-[10px] font-semibold px-2 py-1 rounded border uppercase ${
                SENTIMENT_BADGE[a.overall_sentiment?.toLowerCase()] ?? "border-border-soft text-muted"
              }`}
            >
              {a.overall_sentiment}
            </span>
          </button>
        ))}
      </div>

      <button
        onClick={onNewSearch}
        className="mt-5 font-mono text-[11px] px-4 py-2 rounded border border-amber-border text-amber hover:bg-amber-soft transition-colors"
      >
        + Analyze new ticker
      </button>
    </div>
  )
}

export default HistoryScreen
