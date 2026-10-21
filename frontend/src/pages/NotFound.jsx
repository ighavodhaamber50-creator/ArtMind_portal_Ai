import { Link } from 'react-router-dom'

export default function NotFound() {
  return (
    <div className="container section">
      <div className="notfound" data-category="flower">
        <strong className="notfound-code">404</strong>
        <h1 className="h2">This wall is empty</h1>
        <p>
          We could not find the page you were looking for. It may have moved, or the address may
          have a typo.
        </p>
        <div className="d-flex flex-wrap gap-2">
          <Link className="btn btn-dark" to="/">Back to Home</Link>
          <Link className="btn btn-outline-dark" to="/gallery">Browse the gallery</Link>
        </div>
      </div>
    </div>
  )
}