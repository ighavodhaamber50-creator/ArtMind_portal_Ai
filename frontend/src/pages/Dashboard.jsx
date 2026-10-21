import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { getDashboard } from '../api/dashboard.js'
import ArtworkCard from '../components/ArtworkCard.jsx'
import Loader from '../components/Loader.jsx'
import MiniArtwork from '../components/MiniArtwork.jsx'

function Section({ title, hint, children }) {
  return (
    <section className="container section">
      <div className="section-head">
        <h2>{title}</h2>
        {hint && <p>{hint}</p>}
      </div>
      {children}
    </section>
  )
}

function CardGrid({ artworks, onChange, notes = false }) {
  return (
    <div className="row g-4">
      {artworks.map((artwork) => (
        <div className="col-sm-6 col-lg-4" key={artwork.id}>
          <ArtworkCard
            artwork={artwork}
            note={notes ? artwork.reason : undefined}
            onFavoriteChange={onChange}
          />
        </div>
      ))}
    </div>
  )
}

export default function Dashboard() {
  const [state, setState] = useState({ status: 'loading', data: null, error: '' })
  const [reloadKey, setReloadKey] = useState(0)

  // Loads once, and again (quietly, keeping the old data on screen) whenever a heart is pressed
  useEffect(() => {
    let cancelled = false
    getDashboard()
      .then((data) => {
        if (!cancelled) setState({ status: 'ready', data, error: '' })
      })
      .catch((err) => {
        if (!cancelled) setState((previous) => ({ status: 'error', data: previous.data, error: err.message }))
      })
    return () => {
      cancelled = true
    }
  }, [reloadKey])

  const refresh = () => setReloadKey((key) => key + 1)

  function retry() {
    setState((previous) => ({ ...previous, status: 'loading' }))
    refresh()
  }

  const { data } = state

  if (!data) {
    if (state.status === 'error') {
      return (
        <div className="container py-5 empty-state">
          <div className="alert alert-danger" role="alert">{state.error}</div>
          <button className="btn btn-dark" onClick={retry}>Try again</button>
        </div>
      )
    }
    return <Loader label="Gathering your gallery..." />
  }

  const topCategory = data.favorite_categories[0]?.name

  return (
    <>
      <header className="gallery-head" data-category="religious">
        <div className="container">
          <h1>My Collection</h1>
          <p>Hello, {data.user.username}. Everything you have saved and viewed, with paintings picked for you.</p>
        </div>
      </header>

      {state.status === 'error' && (
        <div className="container pt-4">
          <div className="alert alert-warning mb-0" role="alert">
            Some information may be out of date: {state.error}
          </div>
        </div>
      )}

      <section className="container section" style={{ paddingTop: '2.5rem' }}>
        <div className="row g-3">
          <div className="col-md-4">
            <div className="stat-tile stat-a" data-category="flower">
              <strong>{data.stats.favorites}</strong>
              <span>{data.stats.favorites === 1 ? 'painting saved' : 'paintings saved'}</span>
            </div>
          </div>
          <div className="col-md-4">
            <div className="stat-tile stat-b" data-category="figurative">
              <strong>{data.stats.recently_viewed}</strong>
              <span>{data.stats.recently_viewed === 1 ? 'painting viewed' : 'paintings viewed'}</span>
            </div>
          </div>
          <div className="col-md-4">
            <div className="stat-tile stat-c" data-category="religious">
              <strong>{topCategory || 'Not yet'}</strong>
              <span>your top category</span>
            </div>
          </div>
        </div>
      </section>

      <Section title="Recently viewed" hint="Paintings you opened lately, newest first.">
        {data.recently_viewed.length > 0 ? (
          <div className="mini-row">
            {data.recently_viewed.map((artwork) => <MiniArtwork key={artwork.id} artwork={artwork} />)}
          </div>
        ) : (
          <p className="text-secondary">
            Open a painting and it will appear here. <Link to="/gallery">Browse the gallery</Link>
          </p>
        )}
      </Section>

      <Section title="Favorites" hint="Paintings you have saved.">
        {data.favorites.length > 0 ? (
          <CardGrid artworks={data.favorites} onChange={refresh} />
        ) : (
          <p className="text-secondary">
            Nothing saved yet. Press the heart on any painting to keep it here.{' '}
            <Link to="/gallery">Browse the gallery</Link>
          </p>
        )}
      </Section>

      <Section title="Your favorite categories" hint="Weighted by what you saved and what you opened.">
        {data.favorite_categories.length > 0 ? (
          <div className="bar-list">
            {data.favorite_categories.map((category) => (
              <div className="bar-row" key={category.name} data-category={category.name.toLowerCase()}>
                <span>{category.name}</span>
                <div className="bar-track">
                  <div className="bar-fill" style={{ width: `${Math.max(category.percent, 3)}%` }} />
                </div>
                <span>{category.percent}%</span>
              </div>
            ))}
          </div>
        ) : (
          <p className="text-secondary">
            Open or save a few paintings and your favorite categories will show up here.
          </p>
        )}
      </Section>

      {data.recommendations.length > 0 && (
        <Section
          title="Recommended for you"
          hint={data.personalized
            ? 'Matched to your favorite categories, styles and colors.'
            : 'Popular right now. Open or save a few paintings to personalize this.'}
        >
          <CardGrid artworks={data.recommendations} onChange={refresh} notes />
        </Section>
      )}

      <Section
        title="Curated for you"
        hint="Built from the colors, styles and categories you keep coming back to."
      >
        {data.collections.length > 0 ? (
          data.collections.map((collection) => (
            <div className="collection" key={collection.title}>
              <div className="collection-head" data-category={collection.artworks[0]?.category_slug}>
                <h3>{collection.title}</h3>
                <p>{collection.description}</p>
              </div>
              <CardGrid artworks={collection.artworks} onChange={refresh} />
            </div>
          ))
        ) : (
          <p className="text-secondary">
            Collections appear once you have viewed or saved a few paintings.
          </p>
        )}
      </Section>
    </>
  )
}