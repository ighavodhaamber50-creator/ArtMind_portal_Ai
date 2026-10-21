import { api } from './client.js'

export const getCsrf = () => api('/api/auth/csrf/')
export const getMe = () => api('/api/auth/me/')

export const login = (username, password) =>
  api('/api/auth/login/', { method: 'POST', body: { username, password } })

export const register = (username, email, password) =>
  api('/api/auth/register/', { method: 'POST', body: { username, email, password } })

export const logout = () => api('/api/auth/logout/', { method: 'POST' })