import { Link } from 'react-router-dom'
import ColorSwatches from './ColorSwatches.jsx'

export default function MiniArtwork({ artwork }) {
  return (
    <Link to={`/artworks/${artwork.id}`} className="chat-art" data-category={artwork.category_slug}>
      <img src={artwork.image} alt={`${artwork.title} by ${artwork.artist}`} loading="lazy" />
      <strong>{artwork.title}</strong>
      <span>{artwork.artist}</span>
      <ColorSwatches colors={artwork.dominant_colors} size={10} />
    </Link>
  )
}