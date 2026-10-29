import { Icon } from '@/components/ui/Icon'
import { TextField } from '@/components/ui/TextField'
import { clampDays, lengthHint, MAX_DAYS, MIN_DAYS } from '../draft'
import { usePlan } from '../PlanContext'
import { StepFrame } from '../StepFrame'

const QUICK = [
  { label: 'Long weekend', days: 3 },
  { label: 'One week', days: 7 },
  { label: 'Two weeks', days: 14 },
]

function today(): string {
  const d = new Date()
  return new Date(d.getTime() - d.getTimezoneOffset() * 60_000).toISOString().slice(0, 10)
}

export function LengthStep() {
  const { draft, update } = usePlan()
  const setDays = (days: number) => update({ days: clampDays(days) })

  return (
    <StepFrame
      step="length"
      title="How many days do you have?"
      subtitle="Count full days on the ground. We’ll plan travel between cities for you."
      hint="Travel days between cities are included"
    >
      <div className="flex w-full max-w-[430px] items-center justify-between rounded-[22px] border-[1.5px] border-line bg-card px-6 py-8 sm:px-10">
        <button
          type="button"
          aria-label="One day less"
          onClick={() => setDays(draft.days - 1)}
          disabled={draft.days <= MIN_DAYS}
          className="grid size-16 place-items-center rounded-full border-[1.5px] border-line-strong bg-canvas text-ink hover:border-line-muted disabled:opacity-40"
        >
          <Icon name="minus" size={24} />
        </button>
        <div className="text-center" aria-live="polite">
          <span className="block font-display text-[96px] leading-[0.9] text-terracotta">{draft.days}</span>
          <span className="mt-1 block text-lg font-semibold text-ink-2">{draft.days === 1 ? 'day' : 'days'}</span>
        </div>
        <button
          type="button"
          aria-label="One more day"
          onClick={() => setDays(draft.days + 1)}
          disabled={draft.days >= MAX_DAYS}
          className="grid size-16 place-items-center rounded-full bg-terracotta text-white hover:bg-terracotta-strong disabled:opacity-40"
        >
          <Icon name="plus" size={24} />
        </button>
      </div>

      <div className="mt-8 flex flex-wrap items-center gap-2.5">
        <span className="mr-1 text-[15px] font-semibold text-ink-3">Quick pick</span>
        {QUICK.map((q) => (
          <button
            key={q.days}
            type="button"
            aria-pressed={draft.days === q.days}
            onClick={() => setDays(q.days)}
            className={`rounded-full border-[1.5px] px-4 py-2 text-[15px] font-medium ${
              draft.days === q.days ? 'border-terracotta bg-selected text-terracotta-strong' : 'border-line-strong bg-card text-ink'
            }`}
          >
            {q.label} · {q.days}
          </button>
        ))}
      </div>

      <p className="mt-8 inline-flex items-center gap-3 rounded-2xl bg-nile-soft px-5 py-4 text-base text-nile-strong">
        <Icon name="spark" size={18} />
        {lengthHint(draft.days)}
      </p>

      <TextField
        className="mt-8 w-full sm:w-[320px]"
        label="Start date (optional)"
        type="date"
        min={today()}
        value={draft.startDate ?? ''}
        onChange={(e) => update({ startDate: e.target.value || null })}
      />
    </StepFrame>
  )
}
