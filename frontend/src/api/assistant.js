import { api } from './client.js'

// history is the last few turns, so the assistant can follow the conversation
export const sendMessage = (message, history = []) =>
  api('/api/ai/chat/', { method: 'POST', body: { message, history } })