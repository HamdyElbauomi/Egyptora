import { Outlet, useOutletContext, useParams } from 'react-router-dom'
import { ApiError } from '@/api/client'
import { useTrip, type Trip } from '@/api/queries'
import { Button, ButtonLink } from '@/components/ui/Button'
import { ErrorState } from '@/components/ui/ErrorState'
import { PageLoader } from '@/components/ui/Spinner'

/** Loads the trip once for its three screens: My trip, Chat and Summary. */
export function TripLayout() {
  const id = Number(useParams().tripId)
  const trip = useTrip(id)

  if (trip.isPending) return <PageLoader label="Loading your trip…" />
  if (trip.isError) {
    const missing = trip.error instanceof ApiError && (trip.error.status === 404 || trip.error.status === 422)
    return (
      <ErrorState
        title={missing ? 'Trip not found' : 'We couldn’t load this trip'}
        action={missing ? <ButtonLink to="/trips">Back to my trips</ButtonLink> : <Button onClick={() => trip.refetch()}>Try again</Button>}
      >
        {missing ? 'It may have been deleted, or it belongs to another account.' : trip.error.message}
      </ErrorState>
    )
  }
  return <Outlet context={trip.data satisfies Trip} />
}

// oxlint-disable-next-line react/only-export-components
export function useCurrentTrip(): Trip {
  return useOutletContext<Trip>()
}
