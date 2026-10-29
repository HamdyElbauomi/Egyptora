import { useInterests } from '@/api/queries'
import { Button } from '@/components/ui/Button'
import { ErrorState } from '@/components/ui/ErrorState'
import { Icon } from '@/components/ui/Icon'
import { PageLoader } from '@/components/ui/Spinner'
import { toggleId } from '../draft'
import { interestMeta } from '../interestMeta'
import { usePlan } from '../PlanContext'
import { StepFrame } from '../StepFrame'

export function InterestsStep() {
  const { draft, update } = usePlan()
  const interests = useInterests()

  return (
    <StepFrame
      step="interests"
      title="What do you enjoy?"
      subtitle="Pick as many as you like — we’ll balance the days around them."
      hint={draft.interestIds.length ? `${draft.interestIds.length} selected` : 'Choose at least one'}
    >
      {interests.isPending ? (
        <PageLoader />
      ) : interests.isError ? (
        <ErrorState title="We couldn’t load the interests" action={<Button onClick={() => interests.refetch()}>Try again</Button>}>
          Check your connection and try again.
        </ErrorState>
      ) : (
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-[repeat(auto-fill,minmax(190px,1fr))] sm:gap-4">
          {interests.data.map((interest) => {
            const selected = draft.interestIds.includes(interest.id)
            const meta = interestMeta(interest.icon)
            return (
              <button
                key={interest.id}
                type="button"
                aria-pressed={selected}
                onClick={() => update({ interestIds: toggleId(draft.interestIds, interest.id) })}
                className={`relative flex flex-col items-start rounded-[18px] border-[1.5px] p-4 text-left sm:p-[22px] transition-colors focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-terracotta ${
                  selected ? 'border-terracotta bg-selected' : 'border-line bg-card hover:border-line-strong'
                }`}
              >
                <span
                  className={`grid size-10 place-items-center rounded-xl sm:size-12 sm:rounded-[14px] ${
                    selected ? 'bg-terracotta text-white' : 'bg-muted text-terracotta'
                  }`}
                >
                  <Icon name={meta.icon} size={24} />
                </span>
                {selected && (
                  <span className="absolute top-3 right-3 grid size-[26px] sm:top-[18px] sm:right-[18px] place-items-center rounded-full bg-terracotta text-white">
                    <Icon name="check" size={15} />
                  </span>
                )}
                <span className="mt-3.5 text-base leading-snug font-bold sm:mt-[18px] sm:text-lg text-ink">{interest.name}</span>
                <span className="mt-1.5 text-[13px] leading-normal text-ink-3 sm:mt-2.5 sm:text-sm">{meta.description}</span>
              </button>
            )
          })}
        </div>
      )}
    </StepFrame>
  )
}
