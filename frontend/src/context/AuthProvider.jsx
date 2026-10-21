import { useEffect, useState } from 'react'
import * as authApi from '../api/auth.js'
import { AuthContext } from './authContext.js'

export default function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    let cancelled = false

    async function start() {
      try {
        await authApi.getCsrf() // makes the browser store the CSRF cookie
        const data = await authApi.getMe()
        if (!cancelled) setUser(data.is_authenticated ? data.user : null)
      } catch {
        if (!cancelled) setUser(null)
      } finally {
        if (!cancelled) setLoading(false)
      }
    }

    start()
    return () => {
      cancelled = true
    }
  }, [])

  const value = {
    user,
    loading,
    isAdmin: Boolean(user?.is_staff),
    async login(username, password) {
      setUser(await authApi.login(username, password))
    },
    async register(username, email, password) {
      setUser(await authApi.register(username, email, password))
    },
    async logout() {
      await authApi.logout()
      setUser(null)
    },
  }

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}