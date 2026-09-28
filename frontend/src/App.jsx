import { useState } from "react"
import NavBar from "./components/NavBar"
import SearchScreen from "./components/SearchScreen"
import LoadingScreen from "./components/LoadingScreen"
import DashboardScreen from "./components/DashboardScreen"
import HistoryScreen from "./components/HistoryScreen"
import { fetchCall, analyzeCall, getCall, getAnalysis } from "./api"

const PAUSE = (ms) => new Promise((r) => setTimeout(r, ms))

function App() {
  const [view, setView] = useState("search")
  const [ticker, setTicker] = useState("")
  const [quarter, setQuarter] = useState("")
  const [step, setStep] = useState(0)
  const [result, setResult] = useState(null)
  const [error, setError] = useState(null)

  async function runAnalysis(t, q) {
    setTicker(t)
    setQuarter(q)
    setError(null)
    setView("loading")
    setStep(0)
    try {
      const call = await fetchCall(t, q)
      setStep(1)
      await PAUSE(350)
      setStep(2)
      const analysis = await analyzeCall(t, q)
      setStep(3)
      await PAUSE(350)
      setStep(4)
      await PAUSE(350)
      setResult({ call, analysis })
      setView("dashboard")
    } catch (err) {
      setError(err.message)
      setView("search")
    }
  }

  async function openFromHistory(t, q) {
    setError(null)
    setTicker(t)
    setQuarter(q)
    setView("loading")
    setStep(2)
    try {
      const [call, analysis] = await Promise.all([getCall(t, q), getAnalysis(t, q)])
      setStep(4)
      await PAUSE(300)
      setResult({ call, analysis })
      setView("dashboard")
    } catch (err) {
      setError(err.message)
      setView("search")
    }
  }

  return (
    <div className="min-h-screen flex flex-col bg-navy font-sans">
      <NavBar view={view} onNavigate={setView} />

      {view === "search" && <SearchScreen onSubmit={runAnalysis} error={error} />}

      {view === "loading" && (
        <LoadingScreen ticker={ticker} quarter={quarter} activeStep={step} onCancel={() => setView("search")} />
      )}

      {view === "dashboard" && result && (
        <DashboardScreen call={result.call} analysis={result.analysis} onNewSearch={() => setView("search")} />
      )}

      {view === "history" && <HistoryScreen onSelect={openFromHistory} onNewSearch={() => setView("search")} />}
    </div>
  )
}

export default App
