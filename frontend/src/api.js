const API_BASE = import.meta.env.VITE_API_BASE || "http://127.0.0.1:8000"

async function request(path, options) {
  const res = await fetch(`${API_BASE}${path}`, options)
  const data = await res.json().catch(() => null)
  if (!res.ok) {
    throw new Error(data?.detail || `Request failed with status ${res.status}`)
  }
  return data
}

export function fetchCall(ticker, quarter) {
  return request(`/calls/${ticker}/${quarter}/fetch`, { method: "POST" })
} 

export function analyzeCall(ticker, quarter) {
  return request(`/calls/${ticker}/${quarter}/analyze`, { method: "POST" })
}

export function getCall(ticker, quarter) {
  return request(`/calls/${ticker}/${quarter}`)
}

export function getAnalysis(ticker, quarter) {
  return request(`/analyses/${ticker}/${quarter}`)
}

export function listAnalyses(ticker) {
  const query = ticker ? `?ticker=${encodeURIComponent(ticker)}` : ""
  return request(`/analyses${query}`)
}

export function getRecentAnalyses(limit = 5) {
  return request(`/analyses/recent?limit=${limit}`)
}

export function searchCompanies(query) {
  return request(`/companies/search?q=${encodeURIComponent(query)}`)
}

export function clearHistory(ticker) {
  const query = ticker ? `?ticker=${encodeURIComponent(ticker)}` : ""
  return request(`/analyses${query}`, { method: "DELETE" })
}