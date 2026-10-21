import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { getArtworks, getCategories, getRecommendations } from '../api/gallery.js'
import ArtworkCard from '../components/ArtworkCard.jsx'
import HeroWall from '../components/HeroWall.jsx'
import Loader from '../components/Loader.jsx'
import { useAuth } from '../context/useAuth.js'

const ASSISTANT_QUESTIONS = [
  'What is impressionism?',
  'Recommend some landscape paintings',
  'What is the difference between watercolor and oil painting?',
]
const SAMPLE_PALETTE = [
  ['#3342e8', 3], ['#1f9d6b', 2], ['#f5c518', 2], ['#e8447d', 1], ['#7a4e2d', 2], ['#f4f4f2', 1],
]

export default function Home() {
  const { user, loading: authLoading } = useAuth()
  const userId = user?.id
  const [reloadKey, setReloadKey] = useState(0)
  const [state, setState] = useState({ status: 'loading', categories: [], artworks: [], recs: null, error: '' })

  // Load once the login check is done, and again when someone logs in or out
  useEffect(() => {
    if (authLoading) return
    let cancelled = false

    async function load() {
      try {
        const [categories, artworks, recs] = await Promise.all([
          getCategories(),
          getArtworks({ sort: 'popular', page_size: 50 }),
          getRecommendations(4),
        ])
        if (!cancelled) {
          setState({ status: 'ready', categories, artworks: artworks.results, recs, error: '' })
        }
      } catch (err) {
        if (!cancelled) setState((previous) => ({ ...previous, status: 'error', error: err.message }))
      }
    }

    load()
    return () => {
      cancelled = true
    }
  }, [authLoading, userId, reloadKey])

  function retry() {
    setState((previous) => ({ ...previous, status: 'loading' }))
    setReloadKey((key) => key + 1)
  }

  if (state.status === 'loading') return <Loader label="Hanging the wall..." />

  if (state.status === 'error') {
    return (
      <div className="container py-5" style={{ maxWidth: 560 }}>
        <div className="alert alert-danger" role="alert">{state.error}</div>
        <button className="btn btn-dark" onClick={retry}>Try again</button>
      </div>
    )
  }

  const { categories, artworks, recs } = state
  const featured = artworks.slice(3, 9)

  return (
    <>
      <HeroWall artworks={artworks.slice(0, 3)} />

      <section className="container section">
        <div className="section-head">
          <h2>Browse by category</h2>
          <p>Each category has its own color.</p>
        </div>
        <div className="tile-grid">
          {categories.map((category) => {
            const sample = artworks.find((artwork) => artwork.category_slug === category.slug)
            return (
              <Link
                key={category.id}
                to={`/gallery?category=${category.slug}`}
                className="category-tile"
                data-category={category.slug}
              >
                <span className="tile-name">{category.name}</span>
                <span className="tile-count">
                  {category.artwork_count} {category.artwork_count === 1 ? 'painting' : 'paintings'}
                </span>
                {sample && <img src={sample.image} alt="" loading="lazy" />}
              </Link>
            )
          })}
        </div>
      </section>

      {featured.length > 0 && (
        <section className="container section">
          <div className="section-head">
            <h2>Featured paintings</h2>
            <p>The most viewed works in the gallery.</p>
          </div>
          <div className="row g-4">
            {featured.map((artwork) => (
              <div className="col-sm-6 col-lg-4" key={artwork.id}>
                <ArtworkCard artwork={artwork} />
              </div>
            ))}
          </div>
        </section>
      )}

      {recs && recs.results.length > 0 && (
        <section className="container section">
          <div className="section-head">
            <h2>Recommended For You</h2>
            <p>
              {recs.personalized
                ? 'Picked from the paintings you viewed and saved.'
                : user
                  ? 'Open or save a few paintings and this row will adapt to you.'
                  : 'Popular right now. Log in and save a few paintings to personalize this row.'}
            </p>
          </div>
          <div className="row g-4">
            {recs.results.map((artwork) => (
              <div className="col-sm-6 col-lg-3" key={artwork.id}>
                <ArtworkCard artwork={artwork} note={artwork.reason} />
              </div>
            ))}
          </div>
        </section>
      )}

      <section className="container section">
        <div className="row g-4">
          <div className="col-lg-6">
            <div className="cta-block cta-assistant">
              <h2>Ask the ArtMind Assistant</h2>
              <p>Get answers about styles, techniques and artists, or ask it to find paintings for you.</p>
              <div className="chip-row">
                {ASSISTANT_QUESTIONS.map((question) => (
                  <Link key={question} className="chip" to={`/assistant?ask=${encodeURIComponent(question)}`}>
                    {question}
                  </Link>
                ))}
              </div>
              <Link className="btn btn-dark" to="/assistant">Open the Assistant</Link>
            </div>
          </div>
          <div className="col-lg-6">
            <div className="cta-block cta-analyze">
              <h2>Analyze a painting</h2>
              <p>Upload a photo of a painting to see its colors and the closest matches in the gallery.</p>
              <div className="palette-strip" aria-hidden="true">
                {SAMPLE_PALETTE.map(([color, weight]) => (
                  <span key={color} style={{ background: color, flexGrow: weight }} />
                ))}
              </div>
              <Link className="btn btn-dark" to="/analyze">Upload a painting</Link>
            </div>
          </div>
        </div>
      </section>
    </>
  )
}