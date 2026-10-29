import createClient, { type Middleware } from 'openapi-fetch'
import { readSession, writeSession, type Role } from '@/auth/tokens'
import type { components, paths } from './schema'

export type Schemas = components['schemas']

export const api = createClient<paths>({ baseUrl: '' })

let refreshing: Promise<boolean> | null = null

/** Swaps the refresh token for a new pair. Concurrent 401s share one refresh call. */
function refreshSession(): Promise<boolean> {
  const session = readSession()
  if (!session) return Promise.resolve(false)
  refreshing ??= fetch('/api/v1/auth/refresh', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ refresh_token: session.refresh }),
  })
    .then(async (res) => {
      if (!res.ok) {
        writeSession(null)
        return false
      }
      const tokens = (await res.json()) as Schemas['TokensOut']
      writeSession({ access: tokens.access_token, refresh: tokens.refresh_token, role: tokens.role as Role })
      return true
    })
    .catch(() => false)
    .finally(() => {
      refreshing = null
    })
  return refreshing
}

// an unsent copy of each request, so it can be sent again after a refresh
const copies = new WeakMap<Request, Request>()

const auth: Middleware = {
  onRequest({ request }) {
    const session = readSession()
    if (session) request.headers.set('Authorization', `Bearer ${session.access}`)
    copies.set(request, request.clone())
    return request
  },
  async onResponse({ request, response }) {
    if (response.status !== 401 || request.url.includes('/auth/')) return response
    if (!readSession() || !(await refreshSession())) return response
    const again = copies.get(request)
    if (!again) return response
    again.headers.set('Authorization', `Bearer ${readSession()!.access}`)
    return fetch(again)
  },
}

api.use(auth)

/** Turns FastAPI's error body into one readable sentence. */
export function errorMessage(error: unknown, fallback = 'Something went wrong. Please try again.'): string {
  if (!error || typeof error !== 'object') return fallback
  const detail = (error as { detail?: unknown }).detail
  if (typeof detail === 'string') return detail
  if (Array.isArray(detail) && detail.length) {
    const first = detail[0] as { msg?: string; loc?: (string | number)[] }
    const field = first.loc?.filter((part) => part !== 'body').join(' ')
    const msg = (first.msg ?? '').replace(/^Value error, /, '')
    return field ? `${capitalize(String(field))}: ${msg}` : msg || fallback
  }
  return fallback
}

function capitalize(text: string): string {
  return text.charAt(0).toUpperCase() + text.slice(1)
}

/** Unwraps an openapi-fetch result: returns data or throws an Error with the API's message. */
export function unwrap<T>(result: { data?: T; error?: unknown; response: Response }): T {
  if (result.error !== undefined || result.data === undefined) {
    if (result.response.status === 204) return undefined as T
    throw new ApiError(errorMessage(result.error), result.response.status)
  }
  return result.data
}

export class ApiError extends Error {
  status: number
  constructor(message: string, status: number) {
    super(message)
    this.status = status
  }
}
