import { useState } from "react"
import SearchForm from "./components/SearchForm"
import "./App.css"

function App() {
  const [result, setResult] = useState(null)

  return (
    <div className="App">
      <h1>Earnings Call Analyzer</h1>
      <SearchForm onResult={setResult} />
      {result && (
        <pre className="result-preview">
          {JSON.stringify(result, null, 2)}
        </pre>
      )}
    </div>
  )
}

export default App