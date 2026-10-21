import { Link, useLocation } from 'react-router-dom'
import { useAuth } from '../context/useAuth.js'
import ColorSwatches from './ColorSwatches.jsx'
import FavoriteButton from './FavoriteButton.jsx'

// A framed canvas with a gallery placard. `note` is the recommender's reason, when there is one.
export default function ArtworkCard({ artwork, note, onFavoriteChange }) {
  const { user } = useAuth()
  const location = useLocation()

  // Remember the gallery view (filters, page) so "Return to Gallery" can restore it
  const linkState = {
    back: location.pathname === '/gallery' ? `${location.pathname}${location.search}` : '/gallery',
  }
  const to = `/artworks/${artwork.id}`

  return (
    <article className="placard-card" data-category={artwork.category_slug}>
      <Link to={to} state={linkState} className="canvas-frame" aria-label={`View ${artwork.title}`}>
        <img src={artwork.image} alt={`${artwork.title} by ${artwork.artist}`} loading="lazy" />
      </Link>

      <div className="placard">
        <div className="d-flex justify-content-between align-items-start gap-2">
          <h3 className="placard-title">
            <Link to={to} state={linkState}>{artwork.title}</Link>
          </h3>
          {/* The key resets the heart when someone logs in or out */}
          <FavoriteButton
            key={user?.id ?? 'guest'}
            artworkId={artwork.id}
            initial={artwork.is_favorite}
            onToggle={onFavoriteChange}
          />
        </div>
        <p className="placard-artist">{artwork.artist}</p>
        <p className="placard-meta">
          <span>{artwork.category}</span>
          <span>{artwork.medium_label}</span>
          <span>{artwork.style_label}</span>
        </p>
        {note && <p className="placard-note">{note}</p>}
        <div className="placard-foot">
          <ColorSwatches colors={artwork.dominant_colors} />
          <Link className="btn btn-outline-dark btn-sm" to={to} state={linkState}>View details</Link>
        </div>
      </div>
    </article>
  )
}