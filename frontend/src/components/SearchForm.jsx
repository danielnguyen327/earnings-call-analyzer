import { useState } from "react"
import { fetchCall, analyzeCall } from "../api"

function SearchForm({ onResult }) {
  const [ticker, setTicker] = useState("")
  const [quarter, setQuarter] = useState("")
  const [status, setStatus] = useState("idle")
  const [error, setError] = useState(null)

  async function handleSubmit(e) {
    e.preventDefault()
    setError(null)

    const normalizedTicker = ticker.trim().toUpperCase()
    const normalizedQuarter = quarter.trim().toUpperCase()

    if (!normalizedTicker || !normalizedQuarter) {
      setError("Enter both a ticker and a quarter (e.g., 2026Q3).")
      return
    }

    try {
      setStatus("fetching")
      const call = await fetchCall(normalizedTicker, normalizedQuarter)

      setStatus("analyzing")
      const analysis = await analyzeCall(normalizedTicker, normalizedQuarter)

      setStatus("idle")
      onResult({ call, analysis })
    } catch (err) {
      setError(err.message)
      setStatus("idle")
    }
  }

  const isBusy = status === "fetching" || status === "analyzing"

  return (
    <form onSubmit={handleSubmit} className="search-form">
      <input
        type="text"
        placeholder="Ticker (e.g. AAPL)"
        value={ticker}
        onChange={(e) => setTicker(e.target.value)}
        disabled={isBusy}
      />
      <input
        type="text"
        placeholder="Quarter (e.g. 2026Q3)"
        value={quarter}
        onChange={(e) => setQuarter(e.target.value)}
        disabled={isBusy}
      />
      <button type="submit" disabled={isBusy}>
        {status === "fetching" && "Fetching transcript..."}
        {status === "analyzing" && "Analyzing with Claude..."}
        {!isBusy && "Fetch and Analyze"}
      </button>
      {error && <p className="error">{error}</p>}
    </form>   
  )
}

export default SearchForm
