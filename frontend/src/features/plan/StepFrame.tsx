import type { ReactNode } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useCities, useInterests } from '@/api/queries'
import { useAuth } from '@/auth/AuthProvider'
import { Button } from '@/components/ui/Button'
import { Icon } from '@/components/ui/Icon'
import { Logo } from '@/components/ui/Logo'
import { plural } from '@/lib/format'
import { BUDGETS, STEPS, stepDone, type PlanDraft, type StepKey } from './draft'
import { usePlan } from './PlanContext'

interface StepFrameProps {
  step: StepKey
  title: string
  subtitle: string
  hint: string
  children: ReactNode
}

/** One preference step: sidebar with all steps, progress bar, question, and the Back / Continue footer. */
export function StepFrame({ step, title, subtitle, hint, children }: StepFrameProps) {
  const { draft } = usePlan()
  const { session } = useAuth()
  const navigate = useNavigate()
  const index = STEPS.findIndex((s) => s.key === step)
  const last = index === STEPS.length - 1
  const done = stepDone(step, draft)

  const next = () => navigate(last ? '/plan/build' : `/plan/${STEPS[index + 1].key}`)
  const back = () => navigate(`/plan/${STEPS[index - 1].key}`)

  return (
    <div className="flex min-h-dvh">
      <Sidebar current={step} />
      <div className="flex min-w-0 flex-1 flex-col">
        <div className="h-1.5 bg-track" role="progressbar" aria-valuemin={0} aria-valuemax={4} aria-valuenow={index + 1}>
          <div className="h-full bg-terracotta transition-[width] duration-300" style={{ width: `${((index + 1) / STEPS.length) * 100}%` }} />
        </div>
        <header className="flex items-center justify-between gap-4 px-4 pt-5 sm:px-10 lg:px-20 lg:pt-7">
          <div className="lg:hidden">
            <Logo size="sm" />
          </div>
          <p className="hidden text-sm font-bold tracking-[0.08em] text-ink-3 lg:block">
            STEP {index + 1} OF {STEPS.length}
          </p>
          <Link to={session ? '/trips' : '/'} className="text-[15px] font-semibold text-ink-2 hover:text-ink">
            Save &amp; exit
          </Link>
        </header>

        <main className="flex-1 px-4 pt-6 pb-10 sm:px-10 lg:px-20 lg:pt-10">
          <p className="mb-2 text-xs font-bold tracking-[0.08em] text-ink-3 lg:hidden">
            STEP {index + 1} OF {STEPS.length}
          </p>
          <h1 className="font-display text-[32px] leading-[1.1] tracking-[-0.01em] sm:text-[44px]">{title}</h1>
          <p className="mt-3 text-base text-ink-2 sm:text-[17px]">{subtitle}</p>
          <div className="mt-8">{children}</div>
        </main>

        <footer className="sticky bottom-0 flex items-center gap-4 border-t border-line bg-raised px-4 py-4 sm:px-10 lg:h-24 lg:px-20">
          {index > 0 ? (
            <Button variant="outline" leadingIcon="arrowL" onClick={back}>
              Back
            </Button>
          ) : (
            <span className="hidden sm:block sm:w-[101px]" />
          )}
          <p className="hidden flex-1 text-center text-[15px] text-ink-2 sm:block">{hint}</p>
          <Button
            className="ml-auto sm:ml-0"
            onClick={next}
            disabled={!done}
            icon={last ? undefined : 'arrowR'}
            leadingIcon={last ? 'spark' : undefined}
          >
            {last ? 'Build my trip' : 'Continue'}
          </Button>
        </footer>
      </div>
    </div>
  )
}

function Sidebar({ current }: { current: StepKey }) {
  const { draft } = usePlan()
  const summaries = useSummaries(draft)
  const currentIndex = STEPS.findIndex((s) => s.key === current)

  return (
    <aside className="sticky top-0 hidden h-dvh w-[380px] shrink-0 flex-col bg-muted p-9 lg:flex">
      <Logo size="md" />
      <h2 className="mt-12 font-display text-[28px] leading-tight">Plan your trip</h2>
      <p className="mt-1.5 text-[15px] text-ink-2">Four quick questions. You can change everything later.</p>

      <nav aria-label="Steps" className="mt-8 flex flex-col gap-1">
        {STEPS.map((s, i) => {
          const isCurrent = s.key === current
          const isDone = !isCurrent && stepDone(s.key, draft) && i < currentIndex
          const reachable = STEPS.slice(0, i).every((p) => stepDone(p.key, draft))
          const content = (
            <>
              <span
                className={`grid size-8 shrink-0 place-items-center rounded-full text-sm font-bold ${
                  isCurrent
                    ? 'bg-terracotta text-white'
                    : isDone
                      ? 'bg-nile text-white'
                      : 'border-[1.5px] border-line-muted text-ink-3'
                }`}
              >
                {isDone ? <Icon name="check" size={16} /> : i + 1}
              </span>
              <span className="min-w-0">
                <span className="block text-base font-bold text-ink">{s.title}</span>
                {summaries[s.key] && <span className="block truncate text-[13px] text-ink-3">{summaries[s.key]}</span>}
              </span>
            </>
          )
          const cls = `flex items-center gap-3.5 rounded-xl px-3 py-3 ${isCurrent ? 'bg-raised' : ''}`
          return reachable && !isCurrent ? (
            <Link key={s.key} to={`/plan/${s.key}`} className={`${cls} hover:bg-raised/60`}>
              {content}
            </Link>
          ) : (
            <div key={s.key} className={cls} aria-current={isCurrent ? 'step' : undefined}>
              {content}
            </div>
          )
        })}
      </nav>

      <div className="mt-auto flex gap-3 rounded-2xl bg-raised p-4 text-sm text-ink-2">
        <Icon name="shield" size={18} className="mt-0.5 text-nile" />
        <p>Your first trip is a suggestion, not a booking. Nothing is paid until you choose to book.</p>
      </div>
    </aside>
  )
}

function useSummaries(draft: PlanDraft): Partial<Record<StepKey, string>> {
  const interests = useInterests().data ?? []
  const cities = useCities().data ?? []
  const names = (ids: number[], list: { id: number; name: string }[]) =>
    ids.map((id) => list.find((x) => x.id === id)?.name).filter(Boolean).join(', ')
  return {
    interests: names(draft.interestIds, interests),
    budget: draft.budgetTotal
      ? `EGP ${draft.budgetTotal.toLocaleString('en-US')}`
      : BUDGETS.find((b) => b.level === draft.budgetLevel)?.tier,
    length: plural(draft.days, 'day'),
    destinations: draft.suggest ? 'Suggest for me' : names(draft.cityIds, cities),
  }
}
