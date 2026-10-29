import { useCities } from '@/api/queries'
import { Button } from '@/components/ui/Button'
import { ErrorState } from '@/components/ui/ErrorState'
import { Icon } from '@/components/ui/Icon'
import { PageLoader } from '@/components/ui/Spinner'
import { plural } from '@/lib/format'
import { toggleId } from '../draft'
import { usePlan } from '../PlanContext'
import { StepFrame } from '../StepFrame'

export function DestinationsStep() {
  const { draft, update } = usePlan()
  const cities = useCities()
  const full = draft.cityIds.length >= draft.days

  const hint = draft.suggest
    ? 'Almost done'
    : draft.cityIds.length > draft.days
      ? `Pick at most ${plural(draft.days, 'place')} for ${plural(draft.days, 'day')}`
      : draft.cityIds.length
        ? 'Almost done'
        : 'Choose a place, or let us suggest'

  return (
    <StepFrame
      step="destinations"
      title="Where would you like to go?"
      subtitle="Pick places you already have in mind — or let us suggest the route."
      hint={hint}
    >
      <button
        type="button"
        role="switch"
        aria-checked={draft.suggest}
        onClick={() => update({ suggest: !draft.suggest })}
        className={`flex w-full items-center gap-4 rounded-[18px] border-[1.5px] p-5 text-left transition-colors ${
          draft.suggest ? 'border-terracotta bg-selected' : 'border-line bg-card hover:border-line-strong'
        }`}
      >
        <span
          className={`grid size-[52px] shrink-0 place-items-center rounded-[14px] ${
            draft.suggest ? 'bg-terracotta text-white' : 'bg-muted text-terracotta'
          }`}
        >
          <Icon name="spark" size={22} />
        </span>
        <span className="min-w-0 flex-1">
          <span className="block text-lg font-bold">Not sure — suggest for me</span>
          <span className="mt-1 block text-[15px] text-ink-2">
            We’ll pick the best route for your interests, budget and days.
          </span>
        </span>
        <span
          className={`grid size-6 shrink-0 place-items-center rounded-full border-[1.5px] ${
            draft.suggest ? 'border-terracotta bg-terracotta text-white' : 'border-line-muted'
          }`}
        >
          {draft.suggest && <Icon name="check" size={14} />}
        </span>
      </button>

      <p className="mt-8 mb-3 text-[15px] font-semibold text-ink-2">Or choose places</p>
      {cities.isPending ? (
        <PageLoader />
      ) : cities.isError ? (
        <ErrorState title="We couldn’t load the places" action={<Button onClick={() => cities.refetch()}>Try again</Button>} />
      ) : (
        <div
          className={`grid grid-cols-[repeat(auto-fill,minmax(240px,1fr))] gap-3 transition-opacity ${
            draft.suggest ? 'opacity-55' : ''
          }`}
        >
          {cities.data.map((city) => {
            const checked = !draft.suggest && draft.cityIds.includes(city.id)
            const blocked = !draft.suggest && !checked && full
            return (
              <button
                key={city.id}
                type="button"
                role="checkbox"
                aria-checked={checked}
                aria-disabled={blocked || undefined}
                title={blocked ? `A ${plural(draft.days, 'day')} trip fits up to ${plural(draft.days, 'place')}` : undefined}
                onClick={() => {
                  if (draft.suggest) {
                    // leaving "suggest" keeps earlier picks and adds this one
                    const ids = draft.cityIds.includes(city.id) ? draft.cityIds : [...draft.cityIds, city.id]
                    update({ suggest: false, cityIds: ids.slice(-draft.days) })
                  }
                  else if (!blocked) update({ cityIds: toggleId(draft.cityIds, city.id) })
                }}
                className={`flex items-center gap-3.5 rounded-2xl border-[1.5px] px-[18px] py-4 text-left transition-colors ${
                  checked ? 'border-terracotta bg-selected' : 'border-line bg-card hover:border-line-strong'
                } ${blocked ? 'cursor-not-allowed opacity-60' : ''}`}
              >
                <span
                  className={`grid size-[22px] shrink-0 place-items-center rounded-md border-[1.5px] ${
                    checked ? 'border-terracotta bg-terracotta text-white' : 'border-line-muted bg-card'
                  }`}
                >
                  {checked && <Icon name="check" size={14} />}
                </span>
                <span className="min-w-0">
                  <span className="block text-base font-bold">{city.name}</span>
                  {city.description && <span className="mt-0.5 block text-[13px] text-ink-3">{city.description}</span>}
                </span>
              </button>
            )
          })}
        </div>
      )}
      {!draft.suggest && draft.cityIds.length > 1 && (
        <p className="mt-4 text-sm text-ink-3">We’ll visit them in the order you picked them.</p>
      )}
    </StepFrame>
  )
}
