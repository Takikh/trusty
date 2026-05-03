/**
 * SecureID Verification — API Utility
 *
 * Central HTTP client for all backend communication.
 * Reads the base URL from VITE_API_BASE_URL (set in .env).
 * Provides graceful network error handling.
 */

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://10.5.2.116:8000/api'
const API_KEY = import.meta.env.VITE_API_KEY || 'vaas_admin_key_123'

// ── Connection-error event bus ──────────────────────────────
// Components can subscribe to receive "cannot connect" notifications.
let connectionErrorCallback = null

export function onConnectionError(callback) {
  connectionErrorCallback = callback
}

export function offConnectionError() {
  connectionErrorCallback = null
}

// ── Core request wrapper ────────────────────────────────────

/**
 * Make an authenticated API request.
 * Catches network errors and fires the connection-error callback.
 *
 * @param {string}  endpoint  - Relative path after the base URL (e.g. "/v1/verification/upload/")
 * @param {object}  options   - fetch() options (method, body, headers, etc.)
 * @returns {Promise<Response>}
 */
async function request(endpoint, options = {}) {
  const url = `${API_BASE_URL}${endpoint}`

  const headers = { 
    ...options.headers,
    'X-Api-Key': API_KEY
  }

  // Default to JSON content type unless body is FormData
  if (!(options.body instanceof FormData) && !headers['Content-Type']) {
    headers['Content-Type'] = 'application/json'
  }

  try {
    const response = await fetch(url, {
      ...options,
      headers,
    })
    return response
  } catch (error) {
    // Network failure (server down, CORS block, firewall, etc.)
    console.error(`[API] Network error reaching ${url}:`, error)

    if (connectionErrorCallback) {
      connectionErrorCallback({
        message: 'Cannot connect to server. Please check your network and try again.',
        url,
        error,
      })
    }

    throw error
  }
}

// ── Health check ────────────────────────────────────────────

export async function healthCheck() {
  const response = await request('/health/')
  return response.json()
}

// ── Verification: Document Upload ───────────────────────────

/**
 * Upload a PDF document for verification.
 *
 * @param {string} doctorId  - External doctor identifier (email)
 * @param {File}   file      - The PDF file to upload
 * @returns {Promise<{session_uuid: string, job_id: string, status: string}>}
 */
export async function uploadDocument(doctorId, file) {
  const formData = new FormData()
  formData.append('doctor_id', doctorId)
  formData.append('file', file)

  const response = await request('/v1/verification/upload/', {
    method: 'POST',
    body: formData,
  })

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}))
    throw new Error(errorData.detail || `Upload failed (${response.status})`)
  }

  return response.json()
}

// ── Verification: Poll decision ─────────────────────────────

/**
 * Poll the verification job status.
 *
 * @param {string} jobId - UUID of the verification job
 * @returns {Promise<{session_uuid: string, job_status: string, decision: string}>}
 */
export async function getJobDecision(jobId) {
  const response = await request(`/v1/verification/jobs/${jobId}/decision/`)

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}))
    throw new Error(errorData.detail || `Decision fetch failed (${response.status})`)
  }

  return response.json()
}

// ── Interviews: Create session ──────────────────────────────

/**
 * Create an interview session.
 *
 * @param {string} doctorId - External doctor identifier (email)
 * @returns {Promise<{session_uuid: string, status: string}>}
 */
export async function createInterviewSession(doctorId) {
  const response = await request('/v1/interviews/sessions/', {
    method: 'POST',
    body: JSON.stringify({ doctor_id: doctorId }),
  })

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}))
    throw new Error(errorData.detail || `Interview creation failed (${response.status})`)
  }

  return response.json()
}

// ── Completion: Notify backend ──────────────────────────────

/**
 * Notify the backend that the verification pipeline is complete for a doctor.
 * This triggers the is_verified_by_service update in the shared Supabase DB.
 *
 * @param {string} email - The doctor's email
 * @returns {Promise<Response>}
 */
export async function notifyPipelineComplete(email) {
  try {
    const response = await request('/v1/verification/complete/', {
      method: 'POST',
      body: JSON.stringify({ email }),
    })
    return response
  } catch (error) {
    // Non-critical — the backend can also detect completion via polling
    console.warn('[API] Failed to notify pipeline completion:', error)
    return null
  }
}

// ── Client Platform URL ─────────────────────────────────────

export const CLIENT_PLATFORM_URL = import.meta.env.VITE_CLIENT_PLATFORM_URL || 'http://10.5.2.35:5173'

/**
 * Generate the WebSocket URL for an interview session.
 * Replaces http/https with ws/wss from the API_BASE_URL.
 *
 * @param {string} sessionUuid - The UUID of the interview session
 * @returns {string}
 */
export function getInterviewWSUrl(sessionUuid) {
  const wsBase = API_BASE_URL.replace('http', 'ws').replace('/api', '')
  return `${wsBase}/ws/interview/${sessionUuid}/`
}

export default {
  healthCheck,
  uploadDocument,
  getJobDecision,
  createInterviewSession,
  notifyPipelineComplete,
  onConnectionError,
  offConnectionError,
  CLIENT_PLATFORM_URL,
  API_BASE_URL,
}
