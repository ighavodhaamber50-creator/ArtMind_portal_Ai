import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { wallOf } from '../lib/colors.js'
import ColorSwatches from './ColorSwatches.jsx'

const DEFAULT_WALL = wallOf('blue')

export default function HeroWall({ artworks }) {
  const navigate = useNavigate()
  const [query, setQuery] = useState('')
  const [wall, setWall] = useState(DEFAULT_WALL)

  function search(event) {
    event.preventDefault()
    const text = query.trim()
    navigate(text ? `/gallery?q=${encodeURIComponent(text)}` : '/gallery')
  }

  // The wall takes on the first dominant colour of the painting you point at
  const tint = (artwork) => setWall(wallOf(artwork.dominant_colors[0]))
  const reset = () => setWall(DEFAULT_WALL)

  return (
    <section className="hero-wall" style={{ '--wall': wall }}>
      <div className="container">
        <div className="row align-items-center g-5">
          <div className="col-lg-6">
            <h1>Search paintings the way you talk about them.</h1>
            <p className="lead">
              Ask for &ldquo;blue watercolor landscapes&rdquo; and ArtMind finds them. Save favorites,
              get recommendations, or upload a painting to read its palette.
            </p>

            <form className="hero-search" onSubmit={search} role="search">
              <input
                type="search"
                aria-label="Search paintings"
                placeholder="Try: oil paintings with nature themes"
                value={query}
                onChange={(event) => setQuery(event.target.value)}
                maxLength={300}
              />
              <button className="btn btn-dark" type="submit">Search paintings</button>
            </form>

            <div className="d-flex flex-wrap gap-2 mt-4">
              <Link className="btn btn-outline-light" to="/gallery">Browse the gallery</Link>
            </div>
          </div>

          <div className="col-lg-6">
            {artworks.length > 0 && (
              <div className="hang" onMouseLeave={reset}>
                {artworks.map((artwork, index) => (
                  <Link
                    key={artwork.id}
                    to={`/artworks/${artwork.id}`}
                    className={`hung hung-${index + 1}`}
                    onMouseEnter={() => tint(artwork)}
                    onFocus={() => tint(artwork)}
                    onBlur={reset}
                  >
                    <img src={artwork.image} alt={`${artwork.title} by ${artwork.artist}`} />
                    <span className="hung-label">
                      <strong>{artwork.title}</strong>
                      <span>{artwork.artist}</span>
                      <ColorSwatches colors={artwork.dominant_colors} size={10} />
                    </span>
                  </Link>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </section>
  )
}