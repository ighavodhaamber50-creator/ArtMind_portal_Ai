import { useState } from 'react'
import { Link, Navigate } from 'react-router-dom'
import { useAuth } from '../context/useAuth.js'

export default function Register() {
  const { user, register } = useAuth()
  const [form, setForm] = useState({ username: '', email: '', password: '', confirm: '' })
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)

  if (user) return <Navigate to="/" replace />

  const update = (event) => setForm({ ...form, [event.target.name]: event.target.value })

  async function handleSubmit(event) {
    event.preventDefault()
    setError('')
    if (form.password !== form.confirm) {
      setError('The two passwords do not match.')
      return
    }
    setBusy(true)
    try {
      await register(form.username.trim(), form.email.trim(), form.password)
    } catch (err) {
      setError(err.message)
      setBusy(false)
    }
  }

  return (
    <div className="container py-5" style={{ maxWidth: 440 }}>
      <h1 className="h3 mb-4">Create your account</h1>
      {error && <div className="alert alert-danger" role="alert">{error}</div>}
      <form onSubmit={handleSubmit}>
        <div className="mb-3">
          <label className="form-label" htmlFor="username">Username</label>
          <input id="username" name="username" className="form-control" value={form.username}
                 onChange={update} required autoComplete="username" />
        </div>
        <div className="mb-3">
          <label className="form-label" htmlFor="email">Email (optional)</label>
          <input id="email" name="email" type="email" className="form-control" value={form.email}
                 onChange={update} autoComplete="email" />
        </div>
        <div className="mb-3">
          <label className="form-label" htmlFor="password">Password</label>
          <input id="password" name="password" type="password" className="form-control"
                 value={form.password} onChange={update} required autoComplete="new-password" />
          <div className="form-text">At least 8 characters, and not a common or all-numeric password.</div>
        </div>
        <div className="mb-3">
          <label className="form-label" htmlFor="confirm">Confirm password</label>
          <input id="confirm" name="confirm" type="password" className="form-control"
                 value={form.confirm} onChange={update} required autoComplete="new-password" />
        </div>
        <button className="btn btn-dark w-100" disabled={busy}>{busy ? 'Creating account...' : 'Register'}</button>
      </form>
      <p className="mt-3 text-secondary">
        Already have an account? <Link to="/login">Log in</Link>
      </p>
    </div>
  )
}