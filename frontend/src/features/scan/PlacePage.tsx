import { useParams } from 'react-router-dom'
import { usePlace } from '@/api/scans'
import { Button } from '@/components/ui/Button'
import { ErrorState } from '@/components/ui/ErrorState'
import { PageLoader } from '@/components/ui/Spinner'
import { PlacePanel } from './PlacePanel'

export function PlacePage() {
  const place = usePlace(Number(useParams().placeId))
  if (place.isPending) return <PageLoader />
  if (place.isError) return <ErrorState title="We couldn’t load this place" action={<Button onClick={() => place.refetch()}>Try again</Button>} />
  const photo = place.data.image_url ?? place.data.images[0]?.image_url
  return (
    <div className="grid gap-8 lg:grid-cols-[minmax(0,1fr)_440px]">
      <div className="order-2 lg:order-1">
        <PlacePanel place={place.data} />
      </div>
      {photo && <img src={photo} alt={place.data.name} className="order-1 w-full rounded-[24px] object-cover lg:order-2" />}
    </div>
  )
}
