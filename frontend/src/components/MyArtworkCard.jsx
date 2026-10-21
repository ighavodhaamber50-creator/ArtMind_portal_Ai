import ColorSwatches from './ColorSwatches.jsx'

// One of the user's own paintings, with its download buttons.
export default function MyArtworkCard({ artwork, onDelete }) {
  return (
    <article className="placard-card" data-category={artwork.category_slug}>
      <a
        className="canvas-frame is-contain"
        href={artwork.image}
        target="_blank"
        rel="noreferrer"
        aria-label={`Open ${artwork.title} full size`}
      >
        <img src={artwork.image} alt={`${artwork.title} by ${artwork.artist}`} loading="lazy" />
      </a>

      <div className="placard">
        <h3 className="placard-title">{artwork.title}</h3>
        <p className="placard-artist">{artwork.artist}</p>
        <p className="placard-meta">
          <span>{artwork.category_name}</span>
          <span>{artwork.medium_label}</span>
          <span>{artwork.style_label}</span>
        </p>
        {artwork.description && <p className="placard-note clamp-3">{artwork.description}</p>}
        <ColorSwatches colors={artwork.dominant_colors} />

        <div className="placard-foot">
          <div className="d-flex flex-wrap gap-2">
            <a className="btn btn-outline-dark btn-sm" href={`/api/my-artworks/${artwork.id}/download/pdf/`} download>
              <i className="bi bi-filetype-pdf me-1" />PDF
            </a>
            <a className="btn btn-outline-dark btn-sm" href={`/api/my-artworks/${artwork.id}/download/docx/`} download>
              <i className="bi bi-file-earmark-word me-1" />Word
            </a>
          </div>
          <button type="button" className="btn btn-link btn-sm text-danger" onClick={() => onDelete(artwork)}>
            Delete
          </button>
        </div>
      </div>
    </article>
  )
}