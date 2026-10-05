import { useEffect, useRef, useState } from 'react'
import { App as McpAppClient } from '@modelcontextprotocol/ext-apps'
import type { App as McpApp } from '@modelcontextprotocol/ext-apps'
import A2ADemo from './A2ADemo'
import './App.css'

type PricePoint = { date: string; Close?: number | null }
type MarketHistory = { ticker: string; count: number; prices: PricePoint[] }
type ToolResult = {
  isError?: boolean
  structuredContent?: unknown
  content?: Array<{ type: string; text?: string }>
}

function parseHistory(result: ToolResult): MarketHistory | null {
  let value: unknown = result.structuredContent
  if (!value) {
    const text = result.content?.find((item) => item.type === 'text')?.text
    if (!text) return null
    try { value = JSON.parse(text) } catch { return null }
  }
  if (!value || typeof value !== 'object') return null
  const record = value as Record<string, unknown>
  const data = (record.result ?? record) as Record<string, unknown>
  if (typeof data.ticker !== 'string' || !Array.isArray(data.prices)) return null
  return {
    ticker: data.ticker,
    count: typeof data.count === 'number' ? data.count : data.prices.length,
    prices: data.prices.filter((point): point is PricePoint =>
      Boolean(point) && typeof point === 'object' && typeof (point as PricePoint).date === 'string'),
  }
}

function PriceChart({ prices }: { prices: PricePoint[] }) {
  const data = prices.flatMap((point, index) => typeof point.Close === 'number' && Number.isFinite(point.Close)
    ? [{ index, value: point.Close }] : [])
  if (data.length < 2) return <div className="chart-empty">Not enough closing prices to plot a chart.</div>
  const width = 900
  const height = 300
  const inset = 24
  const values = data.map((point) => point.value)
  const low = Math.min(...values)
  const high = Math.max(...values)
  const spread = high - low || 1
  const line = data.map(({ index, value }) => {
    const x = inset + index / Math.max(prices.length - 1, 1) * (width - inset * 2)
    const y = height - inset - (value - low) / spread * (height - inset * 2)
    return `${x},${y}`
  }).join(' ')
  return <div className="chart-wrap">
    <div className="chart-scale"><span>{high.toFixed(2)}</span><span>{low.toFixed(2)}</span></div>
    <svg className="price-chart" viewBox={`0 0 ${width} ${height}`} role="img" aria-label="Precio de cierre">
      {[0.25, 0.5, 0.75].map((ratio) => <line key={ratio} x1={inset} x2={width - inset}
        y1={inset + ratio * (height - inset * 2)} y2={inset + ratio * (height - inset * 2)} className="chart-grid" />)}
      <polyline points={line} className="chart-line" />
    </svg>
    <div className="chart-dates"><span>{prices[0]?.date.slice(0, 10)}</span><span>{prices.at(-1)?.date.slice(0, 10)}</span></div>
  </div>
}

function PriceExplorer() {
  const mcpApp = useRef<McpApp | null>(null)
  const [connected, setConnected] = useState(false)
  const [ticker, setTicker] = useState('NVDA')
  const [period, setPeriod] = useState('1mo')
  const [history, setHistory] = useState<MarketHistory | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let active = true
    const app = new McpAppClient(
      { name: 'MarketInsider Market Chart', version: '1.0.0' }, {},
    )
    app.ontoolresult = (result) => {
      const data = parseHistory(result)
      if (active && data) { setTicker(data.ticker); setHistory(data) }
    }
    app.ontoolinput = (input) => {
      const args = input.arguments as { ticker?: string; period?: string } | undefined
      if (args?.ticker) setTicker(args.ticker)
      if (args?.period) setPeriod(args.period)
    }
    mcpApp.current = app
    app.connect().then(() => active && setConnected(true)).catch(() => {
      if (active) setError('Open this screen from an MCP Apps-compatible host.')
    })
    return () => { active = false; void app.close() }
  }, [])

  const closes = history?.prices.flatMap((point) => typeof point.Close === 'number' ? [point.Close] : []) ?? []
  const latest = closes.at(-1)
  const change = closes.length > 1 ? closes.at(-1)! - closes[0]! : null

  async function loadPrices(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (!mcpApp.current || !connected) return
    setLoading(true)
    setError(null)
    try {
      const result = await mcpApp.current.callServerTool({ name: 'get_price_history', arguments: {
        ticker: ticker.trim().toUpperCase(), period, interval: '1d',
      } })
      if (result.isError) throw new Error('Could not load price history for this ticker.')
      const data = parseHistory(result)
      if (!data) throw new Error('The server returned an unexpected response format.')
      setHistory(data)
      setTicker(data.ticker)
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : 'Could not query the MCP server.')
    } finally { setLoading(false) }
  }

  return <main className="dashboard">
    <header className="topbar">
      <div className="brand-mark">Q</div>
      <div><p className="eyebrow">MARKET INTELLIGENCE · MARKET DATA</p><h1>Price explorer</h1></div>
      <span className={`connection ${connected ? 'is-connected' : ''}`}><span className="connection-dot" />
        {connected ? 'MCP connected' : 'Connecting to host'}</span>
    </header>
    <form className="controls" onSubmit={loadPrices}>
      <label><span>Ticker</span><input value={ticker} onChange={(event) => setTicker(event.target.value)} maxLength={20} /></label>
      <label><span>Period</span><select value={period} onChange={(event) => setPeriod(event.target.value)}>
        <option value="5d">5 days</option><option value="1mo">1 month</option><option value="3mo">3 months</option>
        <option value="6mo">6 months</option><option value="1y">1 year</option>
      </select></label>
      <button type="submit" disabled={!connected || loading || !ticker.trim()}>
        {loading ? 'Loading…' : 'View prices'}{!loading && <span aria-hidden="true">↗</span>}
      </button>
    </form>
    {error && <p className="error-message" role="alert">{error}</p>}
    {history ? <section className="market-card" aria-label={`Price history for ${history.ticker}`}>
      <div className="card-heading"><div><p className="eyebrow">CLOSING PRICES · {period.toUpperCase()}</p><h2>{history.ticker}</h2></div>
        <div className="quote"><strong>{latest === undefined ? '—' : latest.toFixed(2)}</strong>
          <span className={change !== null && change >= 0 ? 'positive' : 'negative'}>
            {change === null ? 'No change' : `${change >= 0 ? '+' : ''}${change.toFixed(2)} over the period`}</span>
        </div></div>
      <PriceChart prices={history.prices} />
      <footer className="card-footer"><span>{history.count} daily bars</span><span>Source: Yahoo Finance · yfinance</span></footer>
    </section> : <section className="empty-state"><div className="empty-icon">⌁</div>
      <h2>Explore a ticker's price movement</h2>
      <p>Choose a symbol and period to retrieve historical prices from the MCP server.</p>
    </section>}
    <p className="disclaimer">Historical data for educational purposes only. This is not investment advice.</p>
  </main>
}

function App() {
  return window.location.pathname === '/a2a' ? <A2ADemo /> : <PriceExplorer />
}

export default App
