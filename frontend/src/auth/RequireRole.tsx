import { Navigate, useLocation } from 'react-router-dom'
import type { ReactNode } from 'react'
import { useAuth } from './AuthProvider'
import { homeFor, type Role } from './tokens'

/** Sends signed-out visitors to sign in, and other roles to their own home. */
export function RequireRole({ role, children }: { role: Role; children: ReactNode }) {
  const { session } = useAuth()
  const location = useLocation()
  if (!session) {
    const next = encodeURIComponent(location.pathname + location.search)
    return <Navigate to={`/sign-in?next=${next}`} replace />
  }
  if (session.role !== role) return <Navigate to={homeFor(session.role)} replace />
  return <>{children}</>
}
