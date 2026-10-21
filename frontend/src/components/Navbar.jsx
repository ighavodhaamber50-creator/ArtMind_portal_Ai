import { useState } from 'react'
import { Link, NavLink, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/useAuth.js'

export default function Navbar() {
  const { user, loading, isAdmin, logout } = useAuth()
  const [menuOpen, setMenuOpen] = useState(false)
  const navigate = useNavigate()

  const close = () => setMenuOpen(false)
  // Every page owns a colour (see .tone-* in the CSS); the active link fills with it
  const linkClass = (tone) => ({ isActive }) => `nav-link tone-${tone}${isActive ? ' active' : ''}`

  async function handleLogout() {
    close()
    await logout()
    navigate('/')
  }

  return (
    <header className="site-header sticky-top">
      <div className="pigment-bar" aria-hidden="true">
        <span /><span /><span /><span /><span /><span />
      </div>
      <nav className="navbar navbar-expand-xl site-nav">
        <div className="container">
          <Link className="navbar-brand" to="/" onClick={close}>
            <span className="brand-mark" aria-hidden="true">
              <i /><i /><i />
            </span>
            ArtMind AI Portal
          </Link>

          <button
            className="navbar-toggler"
            type="button"
            aria-label="Toggle navigation"
            aria-expanded={menuOpen}
            onClick={() => setMenuOpen((open) => !open)}
          >
            <span className="navbar-toggler-icon" />
          </button>

          <div className={`collapse navbar-collapse${menuOpen ? ' show' : ''}`}>
            <ul className="navbar-nav me-auto mb-2 mb-xl-0 ms-xl-3 gap-xl-1">
              <li className="nav-item"><NavLink end to="/" className={linkClass('home')} onClick={close}>Home</NavLink></li>
              <li className="nav-item"><NavLink to="/gallery" className={linkClass('gallery')} onClick={close}>Gallery</NavLink></li>
              <li className="nav-item"><NavLink to="/assistant" className={linkClass('assistant')} onClick={close}>Assistant</NavLink></li>
              <li className="nav-item"><NavLink to="/analyze" className={linkClass('analyze')} onClick={close}>Analyze Artwork</NavLink></li>
              {user && (
                <>
                  <li className="nav-item"><NavLink to="/collection" className={linkClass('dashboard')} onClick={close}>My Collection</NavLink></li>
                  <li className="nav-item"><NavLink to="/my-artworks" className={linkClass('mine')} onClick={close}>My Artworks</NavLink></li>
                </>
              )}
              {isAdmin && (
                <li className="nav-item"><NavLink to="/analytics" className={linkClass('analytics')} onClick={close}>Analytics</NavLink></li>
              )}
            </ul>

            {!loading && (
              <div className="d-flex flex-column flex-xl-row align-items-xl-center gap-2">
                {user ? (
                  <>
                    <span className="navbar-text me-xl-2 d-xl-none d-xxl-inline">Signed in as {user.username}</span>
                    <button className="btn btn-outline-dark btn-sm" onClick={handleLogout}>Log out</button>
                  </>
                ) : (
                  <>
                    <Link className="btn btn-outline-dark btn-sm" to="/login" onClick={close}>Log in</Link>
                    <Link className="btn btn-brand btn-sm" to="/register" onClick={close}>Register</Link>
                  </>
                )}
              </div>
            )}
          </div>
        </div>
      </nav>
    </header>
  )
}