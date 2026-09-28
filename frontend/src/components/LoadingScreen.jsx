const STEPS = [
  "Fetching earnings call transcript",
  "Segmenting call into sections",
  "Analyzing with Claude",
  "Computing sentiment wave",
  "Saving results",
]

function LoadingScreen({ ticker, quarter, activeStep, onCancel }) {
  return (
    <div className="flex-1 flex flex-col items-center justify-center gap-6">
      <div className="font-mono text-3xl font-bold text-amber tracking-widest">{ticker}</div>
      <div className="font-mono text-xs text-muted">{quarter}</div>

      <div className="h-0.5 bg-navy-3 rounded overflow-hidden" style={{ width: 280 }}>
        <div
          className="h-full bg-gradient-to-r from-amber to-amber-soft rounded transition-all duration-500"
          style={{ width: `${((activeStep + 1) / STEPS.length) * 100}%` }}
        />
      </div>

      <div className="flex flex-col gap-2.5" style={{ minWidth: 280 }}>
        {STEPS.map((label, i) => (
          <div
            key={label}
            className={`flex items-center gap-2.5 font-mono text-xs transition-colors ${
              i < activeStep ? "text-green" : i === activeStep ? "text-ink" : "text-dim"
            }`}
          >
            <span className="w-3.5 text-center text-[11px]">
              {i < activeStep ? "✓" : i === activeStep ? "→" : "·"}
            </span>
            {label}
          </div>
        ))}
      </div>

      <button onClick={onCancel} className="font-mono text-[11px] text-muted hover:text-ink">
        ← cancel
      </button>
    </div>
  )
}

export default LoadingScreen
