import { Component } from 'react'
import { Link } from 'react-router-dom'

// Catches crashes while a page is being drawn, so visitors never see a blank screen.
export default class ErrorBoundary extends Component {
  state = { failed: false }

  static getDerivedStateFromError() {
    return { failed: true }
  }

  componentDidCatch(error) {
    console.error('A page crashed:', error)
  }

  render() {
    if (!this.state.failed) return this.props.children

    return (
      <div className="container py-5 empty-state">
        <h1 className="h3">This page ran into a problem</h1>
        <p>Nothing you did caused it. Reloading usually fixes it.</p>
        <div className="d-flex gap-2 justify-content-center">
          <button className="btn btn-dark" onClick={() => window.location.reload()}>Reload the page</button>
          <Link className="btn btn-outline-dark" to="/">Back to Home</Link>
        </div>
      </div>
    )
  }
}