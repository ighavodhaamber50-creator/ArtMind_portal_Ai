import { useEffect, useState } from 'react'
import { Link, useLocation, useNavigate, useParams } from 'react-router-dom'
import { addFavorite, getArtwork, getSummary, removeFavorite } from '../api/gallery.js'
import ArtworkCard from '../components/ArtworkCard.jsx'
import Loader from '../components/Loader.jsx'
import { useAuth } from '../context/useAuth.js'
import { swatchOf } from '../lib/colors.js'

function FavoriteAction({ artwork }) {
  const { user } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()
  const [saved, setSaved] = useState(artwork.is_favorite)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')

  async function toggle() {
    if (!user) {
      navigate('/login', { state: { from: location.pathname } }) // and come straight back after login
      return
    }
    setBusy(true)
    setError('')
    try {
      if (saved) await removeFavorite(artwork.id)
      else await addFavorite(artwork.id)
      setSaved(!saved)
    } catch (err) {
      setError(err.message)
    } finally {
      setBusy(false)
    }
  }

  return (
    <div>
      <button
        type="button"
        className={`btn ${saved ? 'btn-outline-dark' : 'btn-brand'}`}
        onClick={toggle}
        disabled={busy}
      >
        <i className={`bi ${saved ? 'bi-heart-fill' : 'bi-heart'} me-2`} />
        {saved ? 'Remove from Favorites' : 'Add to Favorites'}
      </button>
      {error && <div className="alert alert-danger py-2 mt-3 mb-0" role="alert">{error}</div>}
    </div>
  )
}

export default function ArtworkDetail() {
  const { id } = useParams()
  const { user, loading: authLoading } = useAuth()
  const userId = user?.id
  const location = useLocation()
  const back = location.state?.back || '/gallery'

  const [result, setResult] = useState({ key: '', status: 'loading' })
  const [summary, setSummary] = useState({ key: '', status: 'loading' })
  const [reloadKey, setReloadKey] = useState(0)
  const requestKey = `${id}|${userId ?? 'guest'}|${reloadKey}`

  useEffect(() => {
    window.scrollTo({ top: 0 })
  }, [id])

  useEffect(() => {
    if (authLoading) return
    let cancelled = false
    getArtwork(id)
      .then((artwork) => {
        if (!cancelled) setResult({ key: requestKey, status: 'ready', artwork })
      })
      .catch((err) => {
        if (!cancelled) {
          setResult({ key: requestKey, status: 'error', error: err.message, notFound: err.status === 404 })
        }
      })
    return () => {
      cancelled = true
    }
  }, [authLoading, id, requestKey])

  // The summary can take a moment to write, so it loads separately from the page
  useEffect(() => {
    let cancelled = false
    getSummary(id)
      .then((data) => {
        if (!cancelled) setSummary({ key: id, status: 'ready', ...data })
      })
      .catch(() => {
        if (!cancelled) setSummary({ key: id, status: 'error' })
      })
    return () => {
      cancelled = true
    }
  }, [id])

  if (authLoading || result.key !== requestKey) return <Loader label="Opening the frame..." />

  if (result.status === 'error') {
    return (
      <div className="container py-5 empty-state">
        <h1 className="h3">{result.notFound ? 'We could not find that painting' : 'Something went wrong'}</h1>
        <p>{result.notFound ? 'It may have been removed from the gallery.' : result.error}</p>
        <div className="d-flex gap-2 justify-content-center">
          <Link className="btn btn-dark" to="/gallery">Return to Gallery</Link>
          {!result.notFound && (
            <button className="btn btn-outline-dark" onClick={() => setReloadKey((key) => key + 1)}>
              Try again
            </button>
          )}
        </div>
      </div>
    )
  }

  const { artwork } = result
  const info = artwork.artist_info

  let summaryBody
  if (summary.key !== id) {
    summaryBody = <p className="text-secondary mb-0">Writing a summary...</p>
  } else if (summary.status === 'error') {
    summaryBody = <p className="text-secondary mb-0">A summary is not available right now.</p>
  } else {
    summaryBody = (
      <>
        <span className={`engine-badge${summary.is_ai ? '' : ' is-fallback'}`}>
          {summary.is_ai ? 'Written by AI' : "Built from the painting's details"}
        </span>
        <p>{summary.summary}</p>
      </>
    )
  }

  return (
    <>
      <div className="detail" data-category={artwork.category_slug}>
        <div className="detail-wall">
          <div className="detail-frame">
            <img src={artwork.image} alt={`${artwork.title} by ${artwork.artist}`} />
          </div>
        </div>

        <div className="detail-info">
          <h1>{artwork.title}</h1>
          <p className="artist-line">{artwork.artist}</p>

          <dl className="facts">
            <dt>Category</dt>
            <dd><span className="category-pill">{artwork.category}</span></dd>
            <dt>Style</dt>
            <dd>{artwork.style_label}</dd>
            <dt>Medium</dt>
            <dd>{artwork.medium_label}</dd>
            <dt>Surface</dt>
            <dd>{artwork.surface_label}</dd>
            <dt>Colors</dt>
            <dd>
              <ul className="named-swatches">
                {artwork.dominant_colors.map((color) => (
                  <li key={color}><i style={{ background: swatchOf(color) }} />{color}</li>
                ))}
              </ul>
            </dd>
          </dl>

          <p>{artwork.description}</p>

          <section className="summary-box" aria-label="Summary">
            {summaryBody}
          </section>

          <div className="d-flex flex-wrap gap-2 align-items-start">
            <FavoriteAction key={artwork.id} artwork={artwork} />
            <Link className="btn btn-outline-dark" to={back}>Return to Gallery</Link>
          </div>

          {info && (
            <section className="artist-box">
              <h2 className="h4">About {info.name}</h2>
              {info.nationality && <p className="artist-line mb-1">{info.nationality}</p>}
              {info.bio && <p className="mb-0">{info.bio}</p>}
            </section>
          )}
        </div>
      </div>

      {artwork.similar_artworks.length > 0 && (
        <section className="container section">
          <div className="section-head">
            <h2>Similar paintings</h2>
            <p>Chosen for matching category, style, and colors.</p>
          </div>
          <div className="row g-4">
            {artwork.similar_artworks.map((similar) => (
              <div className="col-sm-6 col-lg-3" key={similar.id}>
                <ArtworkCard artwork={similar} />
              </div>
            ))}
          </div>
        </section>
      )}
    </>
  )
}