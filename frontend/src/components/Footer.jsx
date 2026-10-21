import { Link } from 'react-router-dom'

export default function Footer() {
  return (
    <footer className="site-footer mt-5">
      <div className="pigment-bar" aria-hidden="true">
        <span /><span /><span /><span /><span /><span />
      </div>
      <div className="container py-4 d-flex flex-column flex-md-row justify-content-between gap-3">
        <div>
          <div className="footer-brand">ArtMind AI Portal</div>
          <div className="small">Explore, search and discover paintings with the help of AI.</div>
        </div>
        <div className="d-flex flex-wrap gap-3 small align-items-start">
          <Link to="/">Home</Link>
          <Link to="/gallery">Gallery</Link>
          <Link to="/assistant">Assistant</Link>
          <Link to="/analyze">Analyze Artwork</Link>
        </div>
        <div className="small">&copy; {new Date().getFullYear()} ArtMind AI Portal</div>
      </div>
    </footer>
  )
}