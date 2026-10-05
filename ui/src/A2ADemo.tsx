import { useRef, useState } from 'react'
import type { FormEvent, KeyboardEvent } from 'react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import './A2A.css'

type ChatMessage = { id: string; role: 'user' | 'assistant'; text: string }
type Delegation = { id: string; agent: string; status: 'working' | 'done' | 'error' }

const agents = [
  { id: 'coordinator', name: 'Market Coordinator', role: 'Coordinates research', icon: '✳', color: 'violet' },
  { id: 'fundamentals', name: 'Company Fundamentals', role: 'Company profile and business', icon: '◈', color: 'blue' },
  { id: 'prices', name: 'Price Analyst', role: 'Price history and performance', icon: '↗', color: 'green' },
  { id: 'news', name: 'Market News', role: 'Recent headlines', icon: '◷', color: 'orange' },
]
const codeMode = { id: 'code-mode', name: 'Market Data · CodeMode', role: 'Sandboxed MCP execution', icon: '⌘', color: 'green' }
const displayNames: Record<string, string> = {
  delegate_to_fundamentals_agent: 'fundamentals',
  delegate_to_price_analyst: 'prices',
  delegate_to_market_news: 'news',
}
const priceExplorerUrl = new URL('/launch', window.location.href)
priceExplorerUrl.port = '8081'
priceExplorerUrl.searchParams.set('tool', 'open_price_chart')
priceExplorerUrl.searchParams.set('args', JSON.stringify({ ticker: 'AAPL', period: '1mo', interval: '1d' }))

function readSseEvent(raw: string): Record<string, unknown> | null {
  const line = raw.split('\n').find((part) => part.startsWith('data:'))
  if (!line) return null
  try { return JSON.parse(line.slice(5).trim()) as Record<string, unknown> } catch { return null }
}

export default function A2ADemo() {
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [delegations, setDelegations] = useState<Delegation[]>([])
  const [input, setInput] = useState('')
  const [running, setRunning] = useState(false)
  const [error, setError] = useState('')
  const [activeAgent, setActiveAgent] = useState('coordinator')
  const threadId = useRef(crypto.randomUUID())

  async function sendMessage(event?: FormEvent<HTMLFormElement>) {
    event?.preventDefault()
    const text = input.trim()
    if (!text || running) return
    const userMessage: ChatMessage = { id: crypto.randomUUID(), role: 'user', text }
    const nextMessages = [...messages, userMessage]
    setMessages(nextMessages)
    setInput('')
    setError('')
    setDelegations([])
    setRunning(true)
    setActiveAgent('coordinator')
    const assistantId = crypto.randomUUID()
    let answer = ''
    try {
      const response = await fetch('/ag-ui', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', Accept: 'text/event-stream' },
        body: JSON.stringify({
          threadId: threadId.current,
          runId: crypto.randomUUID(),
          messages: nextMessages.map((message) => ({ id: message.id, role: message.role, content: message.text })),
          tools: [], context: [], state: {}, forwardedProps: {},
        }),
      })
      if (!response.ok) {
        const data = await response.json().catch(() => ({})) as { error?: string }
        throw new Error(data.error ?? `The agent returned ${response.status}.`)
      }
      if (!response.body) throw new Error('The server did not start the AG-UI stream.')
      const reader = response.body.getReader()
      const decoder = new TextDecoder()
      let buffer = ''
      while (true) {
        const { value, done } = await reader.read()
        if (done) break
        buffer += decoder.decode(value, { stream: true })
        const frames = buffer.split('\n\n')
        buffer = frames.pop() ?? ''
        for (const frame of frames) {
          const event = readSseEvent(frame)
          if (!event) continue
          const type = String(event.type ?? '')
          if (type === 'TOOL_CALL_START') {
            const toolName = String(event.toolCallName ?? '')
            const agent = displayNames[toolName] ?? (toolName.toLowerCase().endsWith('execute') ? codeMode.id : undefined)
            if (agent) {
              const id = String(event.toolCallId ?? crypto.randomUUID())
              setActiveAgent(agent)
              setDelegations((items) => [...items, { id, agent, status: 'working' }])
            }
          } else if (type === 'TOOL_CALL_END') {
            const id = String(event.toolCallId ?? '')
            setDelegations((items) => items.map((item) => item.id === id ? { ...item, status: 'done' } : item))
          } else if (type === 'TEXT_MESSAGE_CONTENT') {
            answer += String(event.delta ?? '')
            setMessages((items) => {
              const found = items.some((item) => item.id === assistantId)
              return found
                ? items.map((item) => item.id === assistantId ? { ...item, text: answer } : item)
                : [...items, { id: assistantId, role: 'assistant', text: answer }]
            })
          } else if (type === 'RUN_ERROR') {
            throw new Error(String(event.message ?? 'The agent could not complete the request.'))
          }
        }
      }
      if (!answer) setMessages((items) => [...items, { id: assistantId, role: 'assistant', text: 'No text response was received.' }])
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : 'Could not connect to the agent.')
      setDelegations((items) => items.map((item) => item.status === 'working' ? { ...item, status: 'error' } : item))
    } finally {
      setRunning(false)
      setActiveAgent('coordinator')
    }
  }

  function handleKeyDown(event: KeyboardEvent<HTMLTextAreaElement>) {
    if (event.key === 'Enter' && !event.shiftKey) { event.preventDefault(); void sendMessage() }
  }

  return <main className="a2a-shell">
    <header className="a2a-topbar">
      <a href="/" className="a2a-brand"><span className="a2a-logo">M</span><span>MARKETINSIDER <small>AGENT STUDIO</small></span></a>
      <div className="protocol-pills"><span><i /> AG-UI <small>streaming</small></span><span><i /> A2A <small>delegation</small></span></div>
      <a className="back-link" href={priceExplorerUrl.href} target="_blank" rel="noreferrer">Price explorer <span>↗</span></a>
    </header>
    <div className="a2a-layout">
      <aside className="agent-sidebar">
        <div className="sidebar-title"><span>YOUR TEAM</span><span className="team-count">04</span></div>
        <p className="sidebar-caption">The coordinator delegates based on your question.</p>
        <div className="agent-list">{agents.map((agent) => <div key={agent.id}
          className={`agent-card ${activeAgent === agent.id && running ? 'agent-active' : ''}`}>
          <span className={`agent-icon ${agent.color}`}>{agent.icon}</span><span className="agent-copy"><strong>{agent.name}</strong><small>{agent.role}</small></span>
          <span className={`agent-state ${activeAgent === agent.id && running ? 'state-working' : ''}`}>{activeAgent === agent.id && running ? 'working' : 'ready'}</span>
        </div>)}</div>
        <div className="delegation-panel"><div className="delegation-heading"><span>DELEGATION TRACE</span><span className="live-dot" /></div>
          {delegations.length === 0 ? <p className="trace-empty">Specialist calls will appear here during the conversation.</p> :
            delegations.map((item) => {
              const agent = item.agent === codeMode.id ? codeMode : agents.find((entry) => entry.id === item.agent)!
              return <div className="trace-item" key={item.id}><span className={`trace-icon ${agent.color}`}>{agent.icon}</span><span className="trace-copy"><strong>{agent.name}</strong><small>{item.status === 'working' ? 'Querying the MCP…' : item.status === 'done' ? 'Response received' : 'Did not complete'}</small></span><span className={`trace-status ${item.status}`}>{item.status === 'working' ? '•••' : item.status === 'done' ? '✓' : '!'}</span></div>
            })}
        </div>
        <div className="a2a-architecture"><span className="architecture-label">UNDER THE HOOD</span><p><b>Coordinator</b> <span>→</span> <b>A2A specialists</b><br /><b>Coordinator</b> <span>→</span> <b>CodeMode</b> <span>→</span> <b>FastMCP</b></p><small>AG-UI streams updates to this chat.</small></div>
      </aside>
      <section className="chat-panel">
        <div className="chat-heading"><div><p className="a2a-eyebrow">MULTI-AGENT RESEARCH</p><h1>Market research team</h1></div><span className={`chat-status ${running ? 'chat-running' : ''}`}><i />{running ? 'Working' : 'Ready'}</span></div>
        <div className="chat-content">
          {messages.length === 0 ? <div className="chat-welcome"><div className="welcome-orbit"><span>Q</span><i>✳</i></div><p className="a2a-eyebrow">COORDINATED MARKET INTELLIGENCE</p><h2>What would you like<br />the team to research?</h2><p>Ask about a company, recent price action, or news. The coordinator will bring in the right specialists.</p><div className="suggestion-list">
            {['Use CodeMode to compare NVDA’s five-day and one-month price movement', 'What does Microsoft do, and what is in the news?', 'Analyze AAPL fundamentals, prices, and recent news'].map((item) => <button key={item} onClick={() => setInput(item)}>{item}<span>↗</span></button>)}
          </div></div> : <div className="message-list">{messages.map((message) => <article key={message.id} className={`chat-message ${message.role}`}>
            {message.role === 'assistant' && <span className="message-avatar">✳</span>}<div><span className="message-author">{message.role === 'user' ? 'You' : 'Market Coordinator'}</span>
              {message.role === 'assistant'
                ? <div className="assistant-markdown"><ReactMarkdown remarkPlugins={[remarkGfm]}>{message.text}</ReactMarkdown></div>
                : <p>{message.text}</p>}
            </div>
          </article>)}{running && !messages.some((message) => message.role === 'assistant' && message.text) && <div className="thinking-line"><span className="message-avatar">✳</span><span>Coordinating the research team <i>•••</i></span></div>}</div>}
        </div>
        {error && <div className="a2a-error" role="alert">{error}</div>}
        <form className="composer" onSubmit={(event) => void sendMessage(event)}><textarea value={input} onChange={(event) => setInput(event.target.value)} onKeyDown={handleKeyDown} placeholder="Ask the market research team…" rows={2} disabled={running} /><div className="composer-bottom"><span>Enter to send · Shift + Enter for a new line</span><button type="submit" disabled={running || !input.trim()}>{running ? 'Working…' : 'Send'} <span>↑</span></button></div></form>
        <p className="chat-footnote">Educational market information only. Not investment advice.</p>
      </section>
    </div>
  </main>
}
