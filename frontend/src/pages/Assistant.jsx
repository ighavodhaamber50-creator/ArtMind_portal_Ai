import { useEffect, useRef, useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import { sendMessage } from '../api/assistant.js'
import ColorSwatches from '../components/ColorSwatches.jsx'

const STARTERS = [
  'What is impressionism?',
  'Recommend some landscape paintings',
  'What is the difference between watercolor and oil painting?',
  'How do I save a painting to my favorites?',
]

let counter = 0
const makeId = () => ++counter

const GREETING = {
  id: makeId(),
  role: 'assistant',
  local: true, // written here, not by the server
  content:
    'Hello! I am the ArtMind Assistant. Ask me about art styles, painting techniques and ' +
    'categories, or tell me what kind of paintings you would like to see.',
  suggestions: STARTERS,
}

const withoutChips = (message) => (message.suggestions?.length ? { ...message, suggestions: [] } : message)

function toHistory(messages) {
  return messages
    .filter((message) => !message.local && !message.error)
    .slice(-6)
    .map((message) => ({ role: message.role, content: message.content }))
}

async function fetchReply(message, history) {
  try {
    const data = await sendMessage(message, history)
    return {
      id: makeId(),
      role: 'assistant',
      content: data.reply,
      artworks: data.artworks,
      suggestions: data.suggestions,
      usedAi: data.used_ai,
      note: data.note,
    }
  } catch (err) {
    return { id: makeId(), role: 'assistant', content: err.message, error: true }
  }
}

function ChatArtwork({ artwork }) {
  return (
    <Link to={`/artworks/${artwork.id}`} className="chat-art" data-category={artwork.category_slug}>
      <img src={artwork.image} alt={`${artwork.title} by ${artwork.artist}`} loading="lazy" />
      <strong>{artwork.title}</strong>
      <span>{artwork.artist}</span>
      <ColorSwatches colors={artwork.dominant_colors} size={10} />
    </Link>
  )
}

function Message({ message, onPick, disabled }) {
  const isUser = message.role === 'user'
  const showBadge = !isUser && !message.local && !message.error

  return (
    <div className={`msg ${isUser ? 'msg-user' : 'msg-assistant'}${message.error ? ' msg-error' : ''}`}>
      <div className="bubble">{message.content}</div>

      {message.artworks?.length > 0 && (
        <div className="chat-art-grid">
          {message.artworks.map((artwork) => <ChatArtwork key={artwork.id} artwork={artwork} />)}
        </div>
      )}

      {showBadge && (
        <span
          className={`engine-badge${message.usedAi ? '' : ' is-fallback'}`}
          title={message.note || 'Answered by an AI model'}
        >
          {message.usedAi ? 'Answered by AI' : 'Built-in answer'}
        </span>
      )}

      {message.suggestions?.length > 0 && (
        <div className="chip-row chat-chips">
          {message.suggestions.map((question) => (
            <button key={question} type="button" className="chip" disabled={disabled} onClick={() => onPick(question)}>
              {question}
            </button>
          ))}
        </div>
      )}
    </div>
  )
}

export default function Assistant() {
  const [searchParams, setSearchParams] = useSearchParams()
  const [messages, setMessages] = useState([GREETING])
  const [input, setInput] = useState('')
  const [busy, setBusy] = useState(false)
  const endRef = useRef(null)
  const askedRef = useRef(false)

  async function send(text) {
    const message = text.trim()
    if (!message || busy) return

    const history = toHistory(messages)
    setMessages((current) => [...current.map(withoutChips), { id: makeId(), role: 'user', content: message }])
    setInput('')
    setBusy(true)

    const reply = await fetchReply(message, history)
    setMessages((current) => [...current, reply])
    if (reply.error) setInput(message) // put the text back so it can be sent again
    setBusy(false)
  }

  // A link such as /assistant?ask=What+is+impressionism asks that question once, then cleans the URL
  useEffect(() => {
    const question = searchParams.get('ask')
    if (!question || askedRef.current) return
    askedRef.current = true
    setSearchParams({}, { replace: true })
    send(question)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [searchParams])

  // Keep the newest message in view (but not on the very first load)
  useEffect(() => {
    if (messages.length < 2) return
    const calm = window.matchMedia('(prefers-reduced-motion: reduce)').matches
    endRef.current?.scrollIntoView({ behavior: calm ? 'auto' : 'smooth', block: 'end' })
  }, [messages, busy])

  function handleSubmit(event) {
    event.preventDefault()
    send(input)
  }

  return (
    <>
      <header className="assist-head">
        <div className="container">
          <h1>ArtMind Assistant</h1>
          <p>Ask about styles, techniques and artists, or tell it what you would like to see.</p>
        </div>
      </header>

      <div className="container">
        <div className="chat">
          <div className="chat-log" role="log" aria-live="polite">
            {messages.map((message) => (
              <Message key={message.id} message={message} onPick={send} disabled={busy} />
            ))}
            {busy && (
              <div className="msg msg-assistant">
                <div className="bubble typing" role="status" aria-label="The assistant is thinking">
                  <i /><i /><i />
                </div>
              </div>
            )}
            <div ref={endRef} />
          </div>

          <form className="chat-input" onSubmit={handleSubmit}>
            <input
              type="text"
              aria-label="Message the assistant"
              placeholder="Ask about a style, or say what you want to see"
              value={input}
              maxLength={500}
              onChange={(event) => setInput(event.target.value)}
            />
            <button className="btn btn-brand" type="submit" disabled={busy || !input.trim()}>Send</button>
          </form>
        </div>
      </div>
    </>
  )
}