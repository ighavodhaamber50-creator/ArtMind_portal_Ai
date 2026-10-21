import { useState } from 'react'
import { Link, Navigate, useLocation } from 'react-router-dom'
import { useAuth } from '../context/useAuth.js'

export default function Login() {
  const { user, login } = useAuth()
  const location = useLocation()
  const [form, setForm] = useState({ username: '', password: '' })
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)

  const redirectTo = location.state?.from || '/'
  if (user) return <Navigate to={redirectTo} replace />

  const update = (event) => setForm({ ...form, [event.target.name]: event.target.value })

  async function handleSubmit(event) {
    event.preventDefault()
    setError('')
    setBusy(true)
    try {
      await login(form.username.trim(), form.password) // the redirect above happens once we are logged in
    } catch (err) {
      setError(err.message)
      setBusy(false)
    }
  }

  return (
    <div className="container py-5" style={{ maxWidth: 440 }}>
      <h1 className="h3 mb-4">Log in</h1>
      {error && <div className="alert alert-danger" role="alert">{error}</div>}
      <form onSubmit={handleSubmit}>
        <div className="mb-3">
          <label className="form-label" htmlFor="username">Username</label>
          <input id="username" name="username" className="form-control" value={form.username}
                 onChange={update} required autoComplete="username" />
        </div>
        <div className="mb-3">
          <label className="form-label" htmlFor="password">Password</label>
          <input id="password" name="password" type="password" className="form-control"
                 value={form.password} onChange={update} required autoComplete="current-password" />
        </div>
        <button className="btn btn-dark w-100" disabled={busy}>{busy ? 'Logging in...' : 'Log in'}</button>
      </form>
      <p className="mt-3 text-secondary">
        New here? <Link to="/register">Create an account</Link>
      </p>
    </div>
  )
}