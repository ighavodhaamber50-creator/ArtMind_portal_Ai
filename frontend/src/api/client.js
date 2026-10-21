// One place for every request to the Django API.
// It adds the CSRF token on POST/DELETE and turns errors into friendly messages.

export class ApiError extends Error {
  constructor(message, status, data) {
    super(message)
    this.status = status
    this.data = data
  }
}

function getCookie(name) {
  const match = document.cookie.split('; ').find((row) => row.startsWith(`${name}=`))
  return match ? decodeURIComponent(match.split('=')[1]) : null
}

function friendlyMessage(status, data) {
  if (status === 429) return 'You are doing that too quickly. Please wait a moment and try again.'
  if (status >= 500) return 'Something went wrong on our side. Please try again in a moment.'

  if (data && typeof data === 'object') {
    if (typeof data.detail === 'string') {
      if (status === 403 && data.detail.includes('credentials')) return 'Please log in to continue.'
      return data.detail
    }
    // Field errors look like { password: ["too short", "too common"] }
    const messages = Object.values(data).flat().filter((m) => typeof m === 'string')
    if (messages.length) return messages.join(' ')
  }

  if (status === 403) return 'Your session may have expired. Please refresh the page and try again.'
  if (status === 404) return 'We could not find that.'
  return 'Something went wrong. Please try again.'
}

export async function api(path, { method = 'GET', body, formData } = {}) {
  const options = { method, headers: {}, credentials: 'same-origin' }

  if (method !== 'GET' && method !== 'HEAD') {
    const token = getCookie('csrftoken')
    if (token) options.headers['X-CSRFToken'] = token
  }

  if (formData) {
    options.body = formData // the browser sets the multipart header itself
  } else if (body !== undefined) {
    options.headers['Content-Type'] = 'application/json'
    options.body = JSON.stringify(body)
  }

  let response
  try {
    response = await fetch(path, options)
  } catch {
    throw new ApiError('Cannot reach the server. Please check your connection and try again.', 0, null)
  }

  let data = null
  if ((response.headers.get('content-type') || '').includes('application/json')) {
    data = await response.json().catch(() => null)
  }

  if (!response.ok) {
    throw new ApiError(friendlyMessage(response.status, data), response.status, data)
  }
  return data // null for "204 No Content" responses
}