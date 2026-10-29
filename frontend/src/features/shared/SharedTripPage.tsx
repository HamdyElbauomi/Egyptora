import { useParams } from 'react-router-dom'
import { useSharedTrip } from '@/api/queries'
import { ButtonLink } from '@/components/ui/Button'
import { ErrorState } from '@/components/ui/ErrorState'
import { Logo } from '@/components/ui/Logo'
import { PageLoader } from '@/components/ui/Spinner'
import { TripView } from '../trips/TripView'

/** Public, read-only view of a shared trip. No account needed. */
export function SharedTripPage() {
  const token = useParams().token ?? ''
  const trip = useSharedTrip(token)

  return (
    <div className="min-h-dvh">
      <header className="border-b border-line">
        <div className="mx-auto flex h-16 max-w-[1440px] items-center justify-between gap-4 px-4 sm:px-10 lg:h-[72px]">
          <Logo size="sm" />
          <ButtonLink to="/plan/interests" size="sm" icon="arrowR">
            Plan your own
          </ButtonLink>
        </div>
      </header>
      <main className="mx-auto max-w-[1440px] px-4 py-7 sm:px-10 lg:py-9">
        {trip.isPending ? (
          <PageLoader label="Loading the trip…" />
        ) : trip.isError ? (
          <ErrorState title="This link doesn’t work any more" action={<ButtonLink to="/">Go to Egyptora</ButtonLink>}>
            The trip may have been unshared by its owner.
          </ErrorState>
        ) : (
          <TripView trip={trip.data} eyebrow={token === 'sample' ? 'Sample trip' : 'Shared trip'} />
        )}
      </main>
    </div>
  )
}
