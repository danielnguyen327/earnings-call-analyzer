function NavBar({ view, onNavigate }) {
  return (
    <nav className="flex items-center justify-between px-6 py-3.5 border-b border-border-amber">
      <img src="/callscope-logo.svg" alt="CallScope" className="h-8" />
      <div className="flex items-center gap-2">
        {view !== "history" && (
          <button
            onClick={() => onNavigate("history")}
            className="font-mono text-[11px] px-3 py-1.5 rounded border border-border-soft text-muted hover:text-ink hover:border-border-amber transition-colors"
          >
            History
          </button>
        )}
        {view !== "search" && (
          <button
            onClick={() => onNavigate("search")}
            className="font-mono text-[11px] px-3 py-1.5 rounded border border-border-soft text-muted hover:text-ink hover:border-border-amber transition-colors"
          >
            New search
          </button>
        )}
      </div>
    </nav>
  )
}

export default NavBar
