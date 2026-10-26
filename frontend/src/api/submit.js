import request from './request'

export const submitInquiry = (data) => request.post('/submit/inquiry/', data)
export const submitContact = (data) => request.post('/submit/contact/', data)
export const recordVisit = (data) => request.post('/submit/visit/', data)
export const createPlaySession = (data) => request.post('/submit/playback/start/', data)
export const reportPlaybackProgress = (data) => request.post('/submit/playback/progress/', data)

export function generateRequestId() {
  return `${Date.now()}-${Math.random().toString(36).slice(2, 10)}`
}
