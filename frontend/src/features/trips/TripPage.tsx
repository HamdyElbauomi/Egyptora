import { useLocation, useParams } from 'react-router-dom'
import { useInterests, useTrip } from '@/api/queries'
import { ApiError } from '@/api/client'
import { Button, ButtonLink } from '@/components/ui/Button'
import { Chip } from '@/components/ui/Chip'
import { ErrorState } from '@/components/ui/ErrorState'
import { Icon } from '@/components/ui/Icon'
import { PageLoader } from '@/components/ui/Spinner'
import { TripView } from './TripView'

export function TripPage() {
  const id = Number(useParams().tripId)
  const fresh = Boolean((useLocation().state as { fresh?: boolean } | null)?.fresh)
  const trip = useTrip(id)
  const interests = useInterests().data ?? []

  if (trip.isPending) return <PageLoader label="Loading your trip…" />
  if (trip.isError) {
    const missing = trip.error instanceof ApiError && trip.error.status === 404
    return (
      <ErrorState
        title={missing ? 'Trip not found' : 'We couldn’t load this trip'}
        action={missing ? <ButtonLink to="/trips">Back to my trips</ButtonLink> : <Button onClick={() => trip.refetch()}>Try again</Button>}
      >
        {missing ? 'It may have been deleted, or it belongs to another account.' : trip.error.message}
      </ErrorState>
    )
  }

  const names = trip.data.interest_ids.map((iid) => interests.find((i) => i.id === iid)?.name).filter(Boolean)

  return (
    <>
      {fresh && (
        <p className="mb-6 flex items-center gap-3 rounded-2xl bg-nile-soft px-5 py-3.5 text-[15px] text-nile-strong">
          <Icon name="check" size={18} />
          Your trip is ready. It’s a suggestion — nothing is booked or paid.
        </p>
      )}
      <TripView
        trip={trip.data}
        eyebrow={trip.data.status === 'saved' ? 'Saved trip' : 'Suggested for you'}
        chips={names.length > 0 && <Chip icon="spark">{names.join(' · ')}</Chip>}
      />
    </>
  )
}
