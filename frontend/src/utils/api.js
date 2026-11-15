/**
 * HDL Arena API Client
 * Supports dynamic host resolution for Android mobile browsers, tablets, and desktop browsers.
 */

export function getApiBase() {
  if (typeof window === 'undefined') return 'http://127.0.0.1:8000'
  if (window.__API_BASE__) return window.__API_BASE__
  // Default to relative URL so Vite dev proxy or same-origin deployment handles /api seamlessly
  return ''
}

export const API_BASE = getApiBase()

export function getAuthToken() {
  if (typeof window === 'undefined') return null
  const token = localStorage.getItem('hdl_auth_token')
  if (!token || token === 'undefined' || token === 'null' || token.trim() === '') {
    return null
  }
  return token.trim()
}

export function setAuthToken(token) {
  if (typeof window !== 'undefined') {
    if (token && typeof token === 'string' && token !== 'undefined' && token !== 'null' && token.trim()) {
      localStorage.setItem('hdl_auth_token', token.trim())
    } else {
      localStorage.removeItem('hdl_auth_token')
    }
  }
}

export function clearAuthToken() {
  if (typeof window !== 'undefined') {
    localStorage.removeItem('hdl_auth_token')
  }
}

/**
 * Standardized API Error object preserving HTTP status, backend error codes,
 * and actionable descriptions for user notifications and retry buttons.
 */
export class ApiError extends Error {
  constructor(message, options = {}) {
    super(message)
    this.name = 'ApiError'
    this.status = options.status || 0
    this.code = options.code || (options.status ? `HTTP_${options.status}` : 'NETWORK_ERROR')
    this.endpoint = options.endpoint || ''
    this.data = options.data || null
    this.isNetworkError = Boolean(options.isNetworkError)
    this.canRetry = options.canRetry !== undefined ? options.canRetry : (this.status >= 500 || this.status === 429 || this.isNetworkError)
  }
}

/**
 * Extracts a human-friendly actionable message from diverse error shapes.
 */
export function getErrorMessage(errOrData, defaultMsg = 'An unexpected error occurred.') {
  if (!errOrData) return defaultMsg
  if (typeof errOrData === 'string') return errOrData
  if (errOrData instanceof Error) return errOrData.message || defaultMsg
  if (typeof errOrData.error === 'string') return errOrData.error
  if (errOrData.error && typeof errOrData.error.message === 'string') return errOrData.error.message
  if (typeof errOrData.message === 'string') return errOrData.message
  return defaultMsg
}

/**
 * Universal safe JSON body parser for Fetch Response objects.
 * Prevents "Unexpected end of JSON input" on empty responses, non-JSON HTML error pages, and 204s.
 */
export async function parseResponseJson(res, endpointLabel = '') {
  let rawText = ''
  try {
    rawText = await res.text()
  } catch (err) {
    return {
      ok: false,
      status: res?.status || 0,
      error: {
        code: 'READ_ERROR',
        message: `Failed to read response body from ${endpointLabel}: ${err.message}`
      },
      message: `Failed to read response body from ${endpointLabel}: ${err.message}`
    }
  }

  const trimmed = (rawText || '').trim()

  // 1. Handle empty response body safely (prevents "Unexpected end of JSON input")
  if (trimmed.length === 0) {
    if (res.ok || res.status === 204) {
      return { ok: true, data: {} }
    }
    return {
      ok: false,
      status: res.status,
      error: {
        code: `HTTP_${res.status}`,
        message: `Server returned an empty response with HTTP status ${res.status} (${res.statusText || 'Error'}) for ${endpointLabel}.`
      },
      message: `Server returned an empty response with HTTP status ${res.status} for ${endpointLabel}.`
    }
  }

  // 2. Detect HTML error responses (e.g. 500 error page or Vite index fallback)
  if (trimmed.startsWith('<')) {
    return {
      ok: false,
      status: res.status,
      error: {
        code: 'HTML_RESPONSE',
        message: `Expected JSON but received HTML response (HTTP ${res.status}) from ${endpointLabel}. Backend route may be offline or unhandled.`
      },
      message: `Server returned HTML (HTTP ${res.status}) instead of JSON for ${endpointLabel}.`
    }
  }

  // 3. Safely parse JSON
  try {
    return JSON.parse(trimmed)
  } catch (parseErr) {
    return {
      ok: false,
      status: res.status,
      error: {
        code: 'INVALID_JSON',
        message: `Invalid JSON received from ${endpointLabel} (HTTP ${res.status}): ${trimmed.slice(0, 100)}`
      },
      message: `Invalid JSON received from ${endpointLabel}.`
    }
  }
}

/**
 * Universal apiFetch with automatic token injection, cookie inclusion,
 * intelligent fallback between relative proxy and direct backend URL,
 * and guaranteed safe response.json() execution.
 */
export async function apiFetch(endpoint, options = {}) {
  const base = getApiBase()
  const cleanEndpoint = endpoint.startsWith('/') ? endpoint : `/${endpoint}`
  const primaryUrl = endpoint.startsWith('http')
    ? endpoint
    : `${base}${cleanEndpoint}`

  const headers = {
    'Content-Type': 'application/json',
    'Accept': 'application/json',
    ...(options.headers || {})
  }

  const token = getAuthToken()
  if (token) {
    headers['Authorization'] = `Bearer ${token}`
    headers['X-Auth-Token'] = token
  }

  const fetchOptions = {
    ...options,
    credentials: options.credentials || 'same-origin',
    headers
  }

  let finalRes = null

  try {
    const res = await fetch(primaryUrl, fetchOptions)
    finalRes = res
    // If relative fetch failed with 404 or connection error and we're not on port 8000, try direct host fallback
    if (!res.ok && res.status === 404 && typeof window !== 'undefined' && window.location.port !== '8000' && !endpoint.startsWith('http')) {
      const fallbackUrl = `http://${window.location.hostname || '127.0.0.1'}:8000${cleanEndpoint}`
      try {
        const fallbackRes = await fetch(fallbackUrl, {
          ...fetchOptions,
          credentials: 'omit' // avoid CORS wildcard conflict on direct IP fallback
        })
        if (fallbackRes.ok) finalRes = fallbackRes
      } catch {
        // Fallback also failed, keep original response
      }
    }
  } catch (networkError) {
    // If primary relative URL failed due to network (e.g. proxy offline), try direct host fallback
    if (typeof window !== 'undefined' && !endpoint.startsWith('http')) {
      const fallbackUrl = `http://${window.location.hostname || '127.0.0.1'}:8000${cleanEndpoint}`
      try {
        finalRes = await fetch(fallbackUrl, {
          ...fetchOptions,
          credentials: 'omit'
        })
      } catch (fallbackError) {
        throw new ApiError(
          `Network connection failed when reaching HDL Arena backend at ${cleanEndpoint}. Ensure Flask backend is running on port 8000.`,
          { isNetworkError: true, status: 0, code: 'NETWORK_ERROR', endpoint: cleanEndpoint, canRetry: true }
        )
      }
    } else {
      throw new ApiError(
        `Network connection failed when reaching HDL Arena backend at ${cleanEndpoint}.`,
        { isNetworkError: true, status: 0, code: 'NETWORK_ERROR', endpoint: cleanEndpoint, canRetry: true }
      )
    }
  }

  // Wrap response with safe .json() parser so NO component ever throws "Unexpected end of JSON input"
  if (finalRes) {
    finalRes.json = async function safeJson() {
      return await parseResponseJson(finalRes, cleanEndpoint)
    }
  }

  return finalRes
}

/**
 * Shared high-level API fetcher that parses JSON safely and rejects on non-2xx responses.
 */
export async function apiFetchJson(endpoint, options = {}) {
  const cleanEndpoint = endpoint.startsWith('/') ? endpoint : `/${endpoint}`
  const res = await apiFetch(cleanEndpoint, options)
  const data = await parseResponseJson(res, cleanEndpoint)

  if (!res.ok || (data && data.ok === false && res.status >= 400)) {
    if (res.status === 401) {
      clearAuthToken()
    }
    const message = getErrorMessage(data, `Request to ${cleanEndpoint} failed with HTTP status ${res.status}`)
    const code = data?.error?.code || (res.status ? `HTTP_${res.status}` : 'SERVER_ERROR')
    const err = new ApiError(message, {
      status: res.status,
      code,
      endpoint: cleanEndpoint,
      data,
      canRetry: res.status >= 500 || res.status === 429
    })
    throw err
  }

  return data
}

/**
 * Authoritative VJ Coin fetcher.
 * Retrieves authenticated user's coin balance from /api/account/coins with fallback to /api/coins.
 */
export async function fetchUserCoins() {
  const data = await apiFetchJson('/api/account/coins')
  if (typeof data.coins !== 'number') {
    throw new Error('Invalid JSON response: missing numeric "coins" field from backend.')
  }
  return data
}

/**
 * Fetch design and verification hints for a problem.
 */
export async function fetchProblemHints(problemId) {
  try {
    const data = await apiFetchJson(`/api/problems/${problemId}/hints`)
    return data.hints || []
  } catch (e) {
    return []
  }
}

/**
 * Unlock a progressive paid hint for 0.5 VJ Coin.
 */
export async function unlockPaidHint(problemId, hintIndex) {
  return await apiFetchJson(`/api/questions/${problemId}/hints/${hintIndex}/unlock`, {
    method: 'POST'
  })
}

/**
 * Fetch questions list with filter params.
 */
export async function fetchQuestions(params = {}) {
  const query = new URLSearchParams()
  for (const [k, v] of Object.entries(params)) {
    if (v !== undefined && v !== null && v !== '' && v !== 'All' && v !== 'all') {
      query.set(k, v)
    }
  }
  const qStr = query.toString()
  const endpoint = qStr ? `/api/questions?${qStr}` : '/api/questions'
  return await apiFetchJson(endpoint)
}
