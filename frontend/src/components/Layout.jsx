import { useEffect } from 'react'
import { Outlet, useLocation } from 'react-router-dom'
import ErrorBoundary from './ErrorBoundary.jsx'
import Footer from './Footer.jsx'
import Navbar from './Navbar.jsx'
import OfflineBanner from './OfflineBanner.jsx'

const TITLES = {
  '/': 'Home',
  '/gallery': 'Gallery',
  '/assistant': 'Assistant',
  '/analyze': 'Analyze Artwork',
  '/collection': 'My Collection',
  '/analytics': 'Analytics',
  '/login': 'Log in',
  '/register': 'Register',
 '/my-artworks': 'My Artworks',
}

function titleFor(pathname) {
  if (TITLES[pathname]) return TITLES[pathname]
  if (pathname.startsWith('/artworks/')) return 'Painting'
  return 'Page not found'
}

export default function Layout() {
  const { pathname } = useLocation()

  // On every page change: set the tab title and start at the top of the new page
  useEffect(() => {
    document.title = `${titleFor(pathname)} | ArtMind AI Portal`
    window.scrollTo({ top: 0 })
  }, [pathname])

  return (
    <div className="d-flex flex-column min-vh-100">
      <a className="skip-link" href="#main">Skip to content</a>
      <OfflineBanner />
      <Navbar />
      <main id="main" tabIndex={-1} className="flex-grow-1">
        {/* The key clears a crashed page as soon as you navigate somewhere else */}
        <ErrorBoundary key={pathname}>
          <Outlet />
        </ErrorBoundary>
      </main>
      <Footer />
    </div>
  )
}