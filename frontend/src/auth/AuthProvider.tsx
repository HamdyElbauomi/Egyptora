import { useQuery, useQueryClient, type QueryClient } from '@tanstack/react-query'
import { createContext, useCallback, useContext, useMemo, useSyncExternalStore, type ReactNode } from 'react'
import { api, unwrap, type Schemas } from '@/api/client'
import { onSessionChange, readSession, writeSession, type Role, type Session } from './tokens'

interface AuthValue {
  session: Session | null
  user: Schemas['UserOut'] | undefined
  signIn: (email: string, password: string) => Promise<Role>
  signUp: (name: string, email: string, password: string) => Promise<Role>
  signOut: () => void
  /** for flows that return tokens themselves, like company sign-up */
  adoptTokens: (tokens: Schemas['TokensOut']) => Role
}

const AuthContext = createContext<AuthValue | null>(null)

/** Catalog data (interests, cities) is the same for everyone; everything else belongs to the old account. */
const SHARED_KEYS = new Set(['interests', 'cities', 'shared'])

function forgetAccountData(client: QueryClient) {
  client.removeQueries({ predicate: (q) => !SHARED_KEYS.has(String(q.queryKey[0])) })
}

function save(tokens: Schemas['TokensOut']): Role {
  const role = tokens.role as Role
  writeSession({ access: tokens.access_token, refresh: tokens.refresh_token, role })
  return role
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const session = useSyncExternalStore(onSessionChange, readSession, readSession)
  const queryClient = useQueryClient()

  const me = useQuery({
    queryKey: ['me', session?.access ? 'in' : 'out'],
    queryFn: async () => unwrap(await api.GET('/api/v1/me')),
    enabled: Boolean(session),
    staleTime: 5 * 60_000,
  })

  const signIn = useCallback(async (email: string, password: string) => {
    forgetAccountData(queryClient)
    return save(unwrap(await api.POST('/api/v1/auth/login', { body: { email, password } })))
  }, [queryClient])

  const signUp = useCallback(async (name: string, email: string, password: string) => {
    forgetAccountData(queryClient)
    return save(unwrap(await api.POST('/api/v1/auth/register', { body: { name, email, password, language: 'en' } })))
  }, [queryClient])

  const adoptTokens = useCallback(
    (tokens: Schemas['TokensOut']) => {
      forgetAccountData(queryClient)
      return save(tokens)
    },
    [queryClient],
  )

  const signOut = useCallback(() => {
    void api.POST('/api/v1/auth/logout').catch(() => undefined)
    writeSession(null)
    forgetAccountData(queryClient)
  }, [queryClient])

  const value = useMemo(
    () => ({ session, user: session ? me.data : undefined, signIn, signUp, signOut, adoptTokens }),
    [session, me.data, signIn, signUp, signOut, adoptTokens],
  )
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

// the hook lives next to its provider on purpose
// oxlint-disable-next-line react/only-export-components
export function useAuth(): AuthValue {
  const value = useContext(AuthContext)
  if (!value) throw new Error('useAuth must be used inside <AuthProvider>')
  return value
}
