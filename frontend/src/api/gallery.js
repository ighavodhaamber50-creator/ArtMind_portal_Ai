import { api } from './client.js'

// In development React runs effects twice. Requests that log activity (a search, a painting
// view) would be counted twice, so an identical request within 2 seconds reuses the first one.
const recent = new Map()
function once(key, makeRequest, windowMs = 2000) {
  const hit = recent.get(key)
  if (hit && Date.now() - hit.time < windowMs) return hit.promise

  const promise = makeRequest()
  recent.set(key, { time: Date.now(), promise })
  promise.catch(() => {
    if (recent.get(key)?.promise === promise) recent.delete(key)
  })
  return promise
}

export const getCategories = () => api('/api/categories/')

export function getArtworks(params = {}) {
  const query = new URLSearchParams(params).toString()
  return api(`/api/artworks/${query ? `?${query}` : ''}`)
}

export const getArtwork = (id) => once(`artwork:${id}`, () => api(`/api/artworks/${id}/`))
export const getSummary = (id) => api(`/api/artworks/${id}/summary/`)
export const getRecommendations = (limit = 8) => api(`/api/recommendations/?limit=${limit}`)

export const searchArtworks = (text) =>
  once(`search:${text}`, () => api('/api/search/', { method: 'POST', body: { query: text } }))

export const addFavorite = (artworkId) =>
  api('/api/favorites/', { method: 'POST', body: { artwork_id: artworkId } })
export const removeFavorite = (artworkId) =>
  api(`/api/favorites/${artworkId}/`, { method: 'DELETE' })