import { Link } from 'react-router-dom'
import { useMyTrips, type TripCard } from '@/api/queries'
import { Button, ButtonLink } from '@/components/ui/Button'
import { Chip } from '@/components/ui/Chip'
import { ErrorState } from '@/components/ui/ErrorState'
import { Icon } from '@/components/ui/Icon'
import { PageLoader } from '@/components/ui/Spinner'
import { formatDate, formatEgp, plural } from '@/lib/format'

export function MyTripsPage() {
  const trips = useMyTrips()

  return (
    <>
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <h1 className="font-display text-[34px] leading-tight sm:text-[44px]">My trips</h1>
          <p className="mt-2 text-[17px] text-ink-2">Every plan you’ve made. Open one to see it day by day.</p>
        </div>
        <ButtonLink to="/plan/interests" leadingIcon="plus">
          Plan a new trip
        </ButtonLink>
      </div>

      <div className="mt-8">
        {trips.isPending ? (
          <PageLoader label="Loading your trips…" />
        ) : trips.isError ? (
          <ErrorState title="We couldn’t load your trips" action={<Button onClick={() => trips.refetch()}>Try again</Button>}>
            {trips.error.message}
          </ErrorState>
        ) : trips.data.length === 0 ? (
          <EmptyTrips />
        ) : (
          <ul className="grid grid-cols-[repeat(auto-fill,minmax(300px,1fr))] gap-5">
            {trips.data.map((trip) => (
              <li key={trip.id}>
                <TripCardLink trip={trip} />
              </li>
            ))}
          </ul>
        )}
      </div>
    </>
  )
}

function TripCardLink({ trip }: { trip: TripCard }) {
  const over = trip.budget_total !== null && trip.budget_total !== undefined && trip.total_cost > trip.budget_total
  return (
    <Link
      to={`/trips/${trip.id}`}
      className="group flex h-full flex-col rounded-[22px] border border-line bg-card p-6 transition-colors hover:border-line-strong focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-terracotta"
    >
      <div className="flex items-start justify-between gap-3">
        <Chip tone={trip.status === 'saved' ? 'nile' : 'muted'} className="!px-2.5 !py-0.5 !text-[13px]">
          {trip.status === 'saved' ? 'Saved' : 'Suggested'}
        </Chip>
        <Icon name="arrowR" size={20} className="text-ink-4 transition-transform group-hover:translate-x-0.5 group-hover:text-terracotta" />
      </div>
      <h2 className="mt-4 font-display text-2xl leading-tight">{trip.title}</h2>
      <p className="mt-2 text-[15px] text-ink-2">
        {trip.cities.join(' → ')} · {plural(trip.days, 'day')}
        {trip.start_date ? ` · from ${formatDate(trip.start_date, true)}` : ''}
      </p>
      <div className="mt-auto flex items-end justify-between pt-6">
        <div>
          <p className="text-[13px] text-ink-3">Estimated</p>
          <p className="text-lg font-bold">{formatEgp(trip.total_cost)}</p>
        </div>
        {over && <Chip tone="accent" icon="alert" className="!px-2.5 !py-0.5 !text-[13px]">Over budget</Chip>}
      </div>
    </Link>
  )
}

function EmptyTrips() {
  return (
    <div className="flex flex-col items-center rounded-[22px] border border-dashed border-line-strong bg-raised px-6 py-16 text-center">
      <span className="grid size-14 place-items-center rounded-2xl bg-terracotta-soft text-terracotta">
        <Icon name="spark" size={26} />
      </span>
      <h2 className="mt-5 font-display text-[28px]">No trips yet</h2>
      <p className="mt-2 max-w-sm text-[15px] text-ink-2">
        Answer four quick questions and we’ll suggest a day-by-day plan in about a minute.
      </p>
      <ButtonLink to="/plan/interests" icon="arrowR" className="mt-6">
        Start planning
      </ButtonLink>
    </div>
  )
}
