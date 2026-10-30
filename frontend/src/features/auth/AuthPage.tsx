import { useState, type FormEvent } from 'react'
import { Link, Navigate, useNavigate, useSearchParams } from 'react-router-dom'
import { useAuth } from '@/auth/AuthProvider'
import { homeFor, type Role } from '@/auth/tokens'
import { Button } from '@/components/ui/Button'
import { Icon } from '@/components/ui/Icon'
import { Logo } from '@/components/ui/Logo'
import { TextField } from '@/components/ui/TextField'
import pattern from '@/assets/pattern-mashrabiya.svg'

const DEMO: { label: string; email: string }[] = [
  { label: 'Traveler', email: 'traveler1@egyptora.dev' },
  { label: 'Company', email: 'sunrise@egyptora.dev' },
  { label: 'Admin', email: 'admin@egyptora.dev' },
]

/** Only same-site paths are accepted as `next`, so the link can't send people elsewhere. */
function safeNext(next: string | null): string | null {
  return next && next.startsWith('/') && !next.startsWith('//') ? next : null
}

export function AuthPage({ mode }: { mode: 'sign-in' | 'sign-up' }) {
  const { session, signIn, signUp } = useAuth()
  const navigate = useNavigate()
  const [params] = useSearchParams()
  const next = safeNext(params.get('next'))
  const fromPlan = next === '/plan/build'

  const [name, setName] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)

  if (session && !busy) return <Navigate to={next ?? homeFor(session.role)} replace />

  const isUp = mode === 'sign-up'
  const switchTo = `${isUp ? '/sign-in' : '/sign-up'}${next ? `?next=${encodeURIComponent(next)}` : ''}`

  const submit = async (e: FormEvent) => {
    e.preventDefault()
    setError(null)
    setBusy(true)
    try {
      const role: Role = isUp ? await signUp(name.trim(), email.trim(), password) : await signIn(email.trim(), password)
      navigate(next ?? homeFor(role), { replace: true })
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Something went wrong. Please try again.')
      setBusy(false)
    }
  }

  return (
    <div className="flex min-h-dvh">
      <div className="flex flex-1 flex-col px-4 py-6 sm:px-10 lg:px-20">
        <Logo />
        <main className="flex flex-1 items-center py-10">
          <div className="w-full max-w-[440px]">
            {fromPlan && (
              <p className="mb-6 flex gap-3 rounded-2xl bg-nile-soft px-4 py-3.5 text-[15px] text-nile-strong">
                <Icon name="check" size={18} className="mt-0.5" />
                Your answers are saved. {isUp ? 'Create an account' : 'Sign in'} and we’ll build your trip.
              </p>
            )}
            <h1 className="font-display text-[40px] leading-[1.1] tracking-[-0.01em]">
              {isUp ? 'Create your account' : 'Welcome back'}
            </h1>
            <p className="mt-3 text-[17px] text-ink-2">
              {isUp ? 'Save your trips and change them any time.' : 'Sign in to see your trips.'}
            </p>

            <form onSubmit={submit} className="mt-8 flex flex-col gap-5" noValidate={false}>
              {isUp && (
                <TextField label="Your name" autoComplete="name" required minLength={2} value={name} onChange={(e) => setName(e.target.value)} />
              )}
              <TextField label="Email" type="email" autoComplete="email" required value={email} onChange={(e) => setEmail(e.target.value)} />
              <TextField
                label="Password"
                type="password"
                autoComplete={isUp ? 'new-password' : 'current-password'}
                required
                minLength={isUp ? 8 : undefined}
                hint={isUp ? 'At least 8 characters' : undefined}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
              />
              {error && (
                <p role="alert" className="flex gap-2 rounded-xl bg-terracotta-soft px-4 py-3 text-[15px] text-terracotta-strong">
                  <Icon name="alert" size={18} className="mt-0.5" />
                  {error}
                </p>
              )}
              <Button type="submit" size="lg" loading={busy} className="mt-1 w-full">
                {isUp ? 'Create account' : 'Sign in'}
              </Button>
            </form>

            <p className="mt-6 text-[15px] text-ink-2">
              {isUp ? 'Already have an account?' : 'New to Egyptora?'}{' '}
              <Link to={switchTo} className="font-bold text-terracotta hover:text-terracotta-strong">
                {isUp ? 'Sign in' : 'Create an account'}
              </Link>
            </p>
            {!isUp && (
              <p className="mt-2 text-[15px] text-ink-2">
                Run a travel company?{' '}
                <Link to="/partner/sign-up" className="font-bold text-terracotta hover:text-terracotta-strong">
                  List your hotel offers
                </Link>
              </p>
            )}

            {import.meta.env.DEV && !isUp && (
              <div className="mt-8 rounded-2xl border border-dashed border-line-strong p-4">
                <p className="text-xs font-bold tracking-[0.08em] text-ink-3">DEMO ACCOUNTS (DEV ONLY)</p>
                <div className="mt-3 flex flex-wrap gap-2">
                  {DEMO.map((d) => (
                    <Button
                      key={d.email}
                      size="sm"
                      variant="outline"
                      onClick={() => {
                        setEmail(d.email)
                        setPassword('egyptora123')
                      }}
                    >
                      {d.label}
                    </Button>
                  ))}
                </div>
              </div>
            )}
          </div>
        </main>
      </div>
      <aside
        className="relative m-4 hidden w-[44%] max-w-[600px] overflow-hidden rounded-[32px] bg-terracotta lg:block"
        style={{ backgroundImage: `url("${pattern}")`, backgroundSize: 'cover', backgroundPosition: 'center' }}
        aria-hidden
      >
        <div className="absolute -top-16 -right-16 size-[220px] rounded-full bg-gold" />
        <div className="absolute right-10 bottom-10 left-10 rounded-3xl bg-card p-7 shadow-[0_20px_50px_rgba(31,26,23,0.22)]">
          <p className="font-display text-[26px] leading-snug">“Make day 3 slower and find a hotel by the Nile.”</p>
          <p className="mt-3 text-[15px] text-ink-2">Change your trip by asking. Egyptora shows exactly what changed.</p>
        </div>
      </aside>
    </div>
  )
}
