import { useState } from 'react'
import { useLocation, useNavigate } from 'react-router-dom'
import { addFavorite, removeFavorite } from '../api/gallery.js'
import { useAuth } from '../context/useAuth.js'

export default function FavoriteButton({ artworkId, initial = false, onToggle }) {
  const { user } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()
  const [override, setOverride] = useState(null) // what the user just chose, until the list reloads
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')

  const saved = override ?? initial

  async function toggle() {
    if (!user) {
      navigate('/login', { state: { from: location.pathname } })
      return
    }
    setBusy(true)
    setError('')
    try {
      if (saved) await removeFavorite(artworkId)
      else await addFavorite(artworkId)
      setOverride(!saved)
      onToggle?.(!saved)
    } catch (err) {
      setError(err.message)
    } finally {
      setBusy(false)
    }
  }

  return (
    <span className="heart-wrap">
      <button
        type="button"
        className="heart"
        aria-pressed={saved}
        aria-label={saved ? 'Remove from favorites' : 'Add to favorites'}
        title={saved ? 'Remove from favorites' : 'Add to favorites'}
        onClick={toggle}
        disabled={busy}
      >
        <i className={`bi ${saved ? 'bi-heart-fill' : 'bi-heart'}`} />
      </button>
      {error && <small className="heart-error" role="alert">{error}</small>}
    </span>
  )
}