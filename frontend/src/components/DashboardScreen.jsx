import { useEffect, useState } from "react"
import { listAnalyses } from "../api"

const SENTIMENT_BADGE = {
  positive: "bg-green-soft text-green border-green-border",
  cautious: "bg-amber-soft text-amber border-amber-border",
  negative: "bg-red-soft text-red border-red-border",
}

const scoreColor = (v) => (v >= 0.7 ? "text-green" : v >= 0.55 ? "text-amber" : "text-red")
const barColor = (v) => (v >= 0.7 ? "bg-green" : v >= 0.55 ? "bg-amber" : "bg-red")

function buildWave(segments) {
  const barCount = 30
  const bars = []
  for (let i = 0; i < barCount; i++) {
    const t = i / (barCount - 1)
    const sectionIdx = Math.min(2, Math.floor(t * 3))
    const base = segments?.[sectionIdx] ?? 0.5
    const wobble = Math.sin(i * 1.7) * 0.06
    bars.push(Math.min(1, Math.max(0.05, base + wobble)))
  }
  return bars
}

function DashboardScreen({ call, analysis }) {
  const [history, setHistory] = useState([])
  const [showTranscript, setShowTranscript] = useState(false)

  useEffect(() => {
    listAnalyses(call.ticker).then(setHistory).catch(() => setHistory([]))
  }, [call.ticker])

  const currentIndex = history.findIndex((h) => h.quarter === call.quarter)
  const previous = currentIndex >= 0 && currentIndex < history.length - 1 ? history[currentIndex + 1] : null
  const delta = previous ? analysis.sentiment_score - previous.sentiment_score : null
  const trend = delta === null ? null : delta > 0.02 ? "improving" : delta < -0.02 ? "declining" : "steady"
  const chronological = [...history].reverse()

  const badgeClass =
    SENTIMENT_BADGE[analysis.overall_sentiment?.toLowerCase()] ?? "bg-navy-3 text-muted border-border-soft"
  const wave = buildWave(analysis.segment_sentiments)

  return (
    <div className="flex-1 px-6 py-5 overflow-y-auto">
      <div className="flex items-start justify-between flex-wrap gap-3 mb-5">
        <div>
          <div className="font-mono text-[26px] font-bold text-amber tracking-wide leading-none">{call.ticker}</div>
          <div className="text-sm font-medium text-ink mt-1">{call.company_name}</div>
          <div className="font-mono text-[11px] text-muted mt-0.5">{call.quarter}</div>
        </div>
        <div className="flex items-center gap-2 flex-wrap">
          <span className={`font-mono text-[11px] font-semibold px-3 py-1.5 rounded border tracking-wide uppercase ${badgeClass}`}>
            {analysis.overall_sentiment}
          </span>
        </div>
      </div>

      <div className="mb-5">
        <div className="flex justify-between font-mono text-[10px] text-muted tracking-wide mb-2">
          <span>Sentiment wave — tone across the call</span>
          <span>Prepared remarks · Q&amp;A · Closing</span>
        </div>
        <div className="bg-navy-2 border border-border-soft rounded-md flex items-center px-2.5 gap-0.5" style={{ height: 60 }}>
          {wave.map((v, i) => (
            <div
              key={i}
              className={`flex-1 rounded-sm min-h-1 ${v > 0.55 ? "bg-green" : v < 0.38 ? "bg-red" : "bg-navy-4"}`}
              style={{ height: `${Math.max(4, v * 50)}px` }}
            />
          ))}
        </div>
      </div>

      <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 mb-5">
        <div className="bg-navy-2 border border-border-soft rounded-md px-3.5 py-3">
          <div className="font-mono text-[9px] text-muted tracking-wide mb-1.5">SENTIMENT SCORE</div>
          <div className={`font-mono text-[22px] font-bold leading-none ${scoreColor(analysis.sentiment_score)}`}>
            {analysis.sentiment_score.toFixed(2)}
          </div>
          {delta !== null && (
            <div className="font-mono text-[9px] text-muted mt-1">
              {delta >= 0 ? "↑" : "↓"} {Math.abs(delta).toFixed(2)} vs last quarter
            </div>
          )}
        </div>
        <div className="bg-navy-2 border border-border-soft rounded-md px-3.5 py-3">
          <div className="font-mono text-[9px] text-muted tracking-wide mb-1.5">MGMT CONFIDENCE</div>
          <div className="font-mono text-[22px] font-bold leading-none text-amber">
            {analysis.management_confidence.toFixed(2)}
          </div>
        </div>
        <div className="bg-navy-2 border border-border-soft rounded-md px-3.5 py-3">
          <div className="font-mono text-[9px] text-muted tracking-wide mb-1.5">RISK FACTORS</div>
          <div className="font-mono text-[22px] font-bold leading-none text-red">{analysis.risk_factors.length}</div>
          <div className="font-mono text-[9px] text-muted mt-1">flagged by AI</div>
        </div>
        <div className="bg-navy-2 border border-border-soft rounded-md px-3.5 py-3">
          <div className="font-mono text-[9px] text-muted tracking-wide mb-1.5">KEY THEMES</div>
          <div className="font-mono text-[22px] font-bold leading-none text-ink">{analysis.key_themes.length}</div>
          <div className="font-mono text-[9px] text-muted mt-1">identified</div>
        </div>
      </div>

      <div className="flex flex-wrap gap-1.5 mb-5">
        <span className="text-[11px] px-2.5 py-1.5 rounded bg-navy-2 border border-border-soft text-muted">
          Most cited: {analysis.key_themes[0]}
        </span>
        <span className="text-[11px] px-2.5 py-1.5 rounded bg-navy-2 border border-border-soft text-muted capitalize">
          Guidance tone: {analysis.guidance_tone}
        </span>
        {trend && (
          <span className="text-[11px] px-2.5 py-1.5 rounded bg-navy-2 border border-border-soft text-muted">
            QoQ sentiment: {trend}
          </span>
        )}
      </div>

      <div className="bg-navy-2 border border-border-soft rounded-lg px-4.5 py-4 mb-4">
        <div className="font-mono text-[10px] text-muted tracking-wide mb-2.5 flex items-center gap-2">
          <span className="w-3 h-px bg-amber" /> AI SUMMARY
        </div>
        <p className="text-[13px] text-ink leading-relaxed">{analysis.summary}</p>
      </div>

      <div className="grid sm:grid-cols-2 gap-3 mb-3">
        <div className="bg-navy-2 border border-border-soft rounded-lg px-4.5 py-4">
          <div className="font-mono text-[10px] text-muted tracking-wide mb-2.5 flex items-center gap-2">
            <span className="w-3 h-px bg-amber" /> KEY THEMES
          </div>
          <div className="flex flex-wrap gap-1.5">
            {analysis.key_themes.map((theme, i) => (
              <span
                key={theme}
                className={`font-mono text-[11px] px-2 py-1 rounded border ${
                  i < 3 ? "border-amber-border text-amber bg-amber-soft" : "border-border-amber text-muted bg-navy-3"
                }`}
              >
                {theme}
              </span>
            ))}
          </div>
        </div>
        <div className="bg-navy-2 border border-border-soft rounded-lg px-4.5 py-4">
          <div className="font-mono text-[10px] text-muted tracking-wide mb-2.5 flex items-center gap-2">
            <span className="w-3 h-px bg-amber" /> FORWARD GUIDANCE
          </div>
          <p className="text-xs text-ink leading-relaxed italic">"{analysis.forward_guidance}"</p>
          <div
            className={`font-mono text-[10px] mt-2 ${
              analysis.guidance_tone === "optimistic"
                ? "text-green"
                : analysis.guidance_tone === "cautious"
                ? "text-amber"
                : "text-muted"
            }`}
          >
            {analysis.guidance_tone === "optimistic"
              ? "↑ Optimistic tone detected"
              : analysis.guidance_tone === "cautious"
              ? "⚠ Cautious tone detected"
              : "→ Neutral tone detected"}
          </div>
        </div>
      </div>

      <div className="grid sm:grid-cols-2 gap-3 mb-3">
        <div className="bg-navy-2 border border-border-soft rounded-lg px-4.5 py-4">
          <div className="font-mono text-[10px] text-muted tracking-wide mb-2.5 flex items-center gap-2">
            <span className="w-3 h-px bg-amber" /> RISK FACTORS
          </div>
          <div className="flex flex-col gap-1.5">
            {analysis.risk_factors.map((risk) => (
              <div key={risk} className="flex items-start gap-2">
                <span className="w-1.5 h-1.5 rounded-full bg-red mt-1.5 flex-shrink-0" />
                <span className="text-xs text-muted leading-relaxed">{risk}</span>
              </div>
            ))}
          </div>
        </div>

        {chronological.length > 1 && (
          <div className="bg-navy-2 border border-border-soft rounded-lg px-4.5 py-4">
            <div className="font-mono text-[10px] text-muted tracking-wide mb-3 flex items-center gap-2">
              <span className="w-3 h-px bg-amber" /> QUARTER COMPARISON — {call.ticker}
            </div>
            <div className="flex gap-2">
              {chronological.map((h) => (
                <div key={h.quarter} className="flex-1">
                  <div className="font-mono text-[9px] text-muted mb-1">{h.quarter}</div>
                  <div className="h-1.5 bg-navy-3 rounded overflow-hidden mb-1">
                    <div className={`h-full rounded ${barColor(h.sentiment_score)}`} style={{ width: `${h.sentiment_score * 100}%` }} />
                  </div>
                  <div className={`font-mono text-[13px] font-semibold ${scoreColor(h.sentiment_score)}`}>
                    {h.sentiment_score.toFixed(2)}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      <div className="bg-navy-2 border border-border-soft rounded-lg px-4.5 py-4">
        <button
          onClick={() => setShowTranscript((s) => !s)}
          className="flex w-full items-center justify-between text-left group"
        >
          <div className="font-mono text-[10px] text-muted tracking-wide flex items-center gap-2 group-hover:text-ink transition-colors">
            <span className="w-3 h-px bg-amber" /> FULL TRANSCRIPT
          </div>
          <span className="font-mono text-[10px] text-muted group-hover:text-amber transition-colors">
            {showTranscript ? "Hide" : "Show"}
          </span>
        </button>
        {showTranscript && (
          <div className="mt-3 max-h-80 overflow-y-auto bg-navy rounded p-3">
            <pre className="whitespace-pre-wrap font-sans text-xs text-muted leading-relaxed">{call.transcript_raw}</pre>
          </div>
        )}
      </div>
    </div>
  )
}

export default DashboardScreen
