/** Keeps the signed-in session in localStorage. Every access is guarded: storage can be blocked. */

export type Role = 'traveler' | 'company' | 'admin'

export interface Session {
  access: string
  refresh: string
  role: Role
}

const KEY = 'egyptora.session'
let memory: Session | null = null
const listeners = new Set<() => void>()

export function readSession(): Session | null {
  if (memory) return memory
  try {
    const raw = localStorage.getItem(KEY)
    memory = raw ? (JSON.parse(raw) as Session) : null
  } catch {
    memory = null
  }
  return memory
}

export function writeSession(session: Session | null): void {
  memory = session
  try {
    if (session) localStorage.setItem(KEY, JSON.stringify(session))
    else localStorage.removeItem(KEY)
  } catch {
    // storage blocked: the session lives in memory until the tab closes
  }
  listeners.forEach((fn) => fn())
}

export function onSessionChange(fn: () => void): () => void {
  listeners.add(fn)
  return () => listeners.delete(fn)
}

/** Where each role lands after signing in. */
export function homeFor(role: Role): string {
  if (role === 'company') return '/company'
  if (role === 'admin') return '/admin'
  return '/trips'
}
