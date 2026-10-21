import { api } from './client.js'

// Sends the image as multipart form data (the browser sets the right headers itself)
export function analyzeImage(file) {
  const formData = new FormData()
  formData.append('image', file)
  return api('/api/ai/analyze-image/', { method: 'POST', formData })
}