import { useCallback, useEffect, useRef, useState } from 'react'
import { Navigate, useNavigate } from 'react-router-dom'
import { useGenerateTrip } from '@/api/queries'
import { useAuth } from '@/auth/AuthProvider'
import { Button, ButtonLink } from '@/components/ui/Button'
import { ErrorState } from '@/components/ui/ErrorState'
import { Icon } from '@/components/ui/Icon'
import { Logo } from '@/components/ui/Logo'
import { firstOpenStep, saveDraft, toGenerateBody } from './draft'
import { usePlan } from './PlanContext'

const STAGES = ['Matching places to your interests', 'Fitting your days and travel time', 'Choosing hotels within budget']

/** Builds the trip from the saved answers, then opens it. Signing in comes first if needed. */
export function BuildPage() {
  const { draft } = usePlan()
  const { session } = useAuth()
  const navigate = useNavigate()
  const generate = useGenerateTrip()
  const started = useRef(false)
  const [stage, setStage] = useState(0)
  const open = firstOpenStep(draft)
  const canBuild = session?.role === 'traveler' && !open

  const { mutate } = generate
  const build = useCallback(
    () =>
      mutate(toGenerateBody(draft), {
        onSuccess: (trip) => {
          saveDraft(null)
          navigate(`/trips/${trip.id}`, { replace: true, state: { fresh: true } })
        },
      }),
    [mutate, draft, navigate],
  )

  useEffect(() => {
    if (!canBuild || started.current) return
    started.current = true
    build()
  }, [canBuild, build])

  useEffect(() => {
    const timer = setInterval(() => setStage((s) => Math.min(s + 1, STAGES.length - 1)), 900)
    return () => clearInterval(timer)
  }, [])

  if (!session) return <Navigate to="/sign-up?next=/plan/build" replace />
  if (open) return <Navigate to={`/plan/${open}`} replace />

  return (
    <div className="flex min-h-dvh flex-col px-4 py-6 sm:px-10">
      <Logo size="md" />
      <main className="flex flex-1 items-center justify-center">
        {session.role !== 'traveler' ? (
          <ErrorState
            title="Trips are for traveler accounts"
            action={<ButtonLink to={session.role === 'company' ? '/company' : '/admin'}>Go to your dashboard</ButtonLink>}
          >
            You’re signed in as a {session.role}. Sign in with a traveler account to build a trip.
          </ErrorState>
        ) : generate.isError ? (
          <ErrorState
            title="We couldn’t build this trip"
            action={
              <div className="flex flex-wrap justify-center gap-3">
                <ButtonLink to="/plan/destinations" variant="outline" leadingIcon="arrowL">
                  Change answers
                </ButtonLink>
                <Button onClick={build} leadingIcon="spark">
                  Try again
                </Button>
              </div>
            }
          >
            {generate.error.message}
          </ErrorState>
        ) : (
          <div className="flex max-w-md flex-col items-center text-center" aria-live="polite">
            <span className="relative grid size-20 place-items-center rounded-[26px] bg-terracotta text-white">
              <span className="absolute inset-0 animate-ping rounded-[26px] bg-terracotta/30" />
              <Icon name="spark" size={34} />
            </span>
            <h1 className="mt-8 font-display text-[34px] leading-tight">Building your trip…</h1>
            <ul className="mt-6 space-y-2.5 text-left text-base">
              {STAGES.map((text, i) => (
                <li key={text} className={`flex items-center gap-3 ${i <= stage ? 'text-ink' : 'text-ink-4'}`}>
                  <span
                    className={`grid size-6 place-items-center rounded-full ${
                      i < stage ? 'bg-nile text-white' : i === stage ? 'bg-terracotta-soft text-terracotta' : 'bg-muted'
                    }`}
                  >
                    {i < stage ? <Icon name="check" size={14} /> : <span className="size-1.5 rounded-full bg-current" />}
                  </span>
                  {text}
                </li>
              ))}
            </ul>
          </div>
        )}
      </main>
    </div>
  )
}
