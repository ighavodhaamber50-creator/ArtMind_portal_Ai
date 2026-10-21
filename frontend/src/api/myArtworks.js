import { api } from './client.js'

export const getMyArtworks = () => api('/api/my-artworks/')

// A picture plus text fields has to travel as a multipart form
export function addMyArtwork(fields, file) {
  const formData = new FormData()
  Object.entries(fields).forEach(([key, value]) => formData.append(key, value))
  formData.append('image', file)
  return api('/api/my-artworks/', { method: 'POST', formData })
}

export const deleteMyArtwork = (id) => api(`/api/mexport const SURFACES = [
  ['canvas', 'Canvas'], ['paper', 'Paper'], ['wood', 'Wood panel'], ['board', 'Board'],
]y-artworks/${id}/`, { method: 'DELETE' })

