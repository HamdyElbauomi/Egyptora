import { useState } from 'react'
import { useChooseOffer, useCityHotels, type Trip, type TripDay } from '@/api/queries'
import { Button } from '@/components/ui/Button'
import { Dialog } from '@/components/ui/Dialog'
import { ErrorState } from '@/components/ui/ErrorState'
import { Icon } from '@/components/ui/Icon'
import { PageLoader } from '@/components/ui/Spinner'
import { useToast } from '@/components/ui/Toast'
import { plural } from '@/lib/format'
import { ChooseButton, HotelRow } from '../../hotels/HotelOffers'
import { stayOf } from '../tripMath'

/** Compare hotels and companies for one night, or for the whole stay in that city. */
export function HotelDialog({ trip, day, onClose }: { trip: Trip; day: TripDay | null; onClose: () => void }) {
  return (
    <Dialog
      open={day !== null}
      onClose={onClose}
      size="lg"
      title={day ? `Hotel in ${day.city_name}` : ''}
      description="Same hotel, different companies — compare price, trust and cancellation."
    >
      {day && <HotelPicker key={day.id} trip={trip} day={day} onDone={onClose} />}
    </Dialog>
  )
}

function HotelPicker({ trip, day, onDone }: { trip: Trip; day: TripDay; onDone: () => void }) {
  const hotels = useCityHotels(day.city_id)
  const choose = useChooseOffer(trip.id)
  const toast = useToast()
  const stay = stayOf(trip.itinerary, day)
  const [wholeStay, setWholeStay] = useState(stay.length > 1)
  const [open, setOpen] = useState<number | null>(day.hotel?.hotel_id ?? null)
  const [busy, setBusy] = useState<number | null>(null)
  const nights = wholeStay ? stay : [day]

  const apply = async (offerId: number | null) => {
    setBusy(offerId ?? 0)
    try {
      for (const night of nights) await choose.mutateAsync({ dayId: night.id, offerId })
      toast(offerId === null ? 'Hotel removed' : `Hotel set for ${plural(nights.length, 'night')}`)
      onDone()
    } catch (err) {
      toast(err instanceof Error ? err.message : 'Couldn’t change the hotel', 'error')
      setBusy(null)
    }
  }

  if (hotels.isPending) return <PageLoader label="Loading hotels…" />
  if (hotels.isError) return <ErrorState title="We couldn’t load the hotels" action={<Button onClick={() => hotels.refetch()}>Try again</Button>} />

  return (
    <div>
      {stay.length > 1 && (
        <label className="mb-4 flex cursor-pointer items-center gap-3 rounded-2xl bg-nile-soft px-4 py-3 text-[15px] text-nile-strong">
          <input type="checkbox" checked={wholeStay} onChange={(e) => setWholeStay(e.target.checked)} className="size-4 accent-[#2e6a58]" />
          Use it for all {stay.length} nights in {day.city_name} (days {stay[0].day_number}–{stay[stay.length - 1].day_number})
        </label>
      )}
      {hotels.data.data.length === 0 ? (
        <p className="rounded-2xl bg-raised px-5 py-8 text-center text-[15px] text-ink-3">No hotels in {day.city_name} yet.</p>
      ) : (
        <div className="flex flex-col gap-3">
          {hotels.data.data.map((hotel) => (
            <HotelRow
              key={hotel.id}
              hotel={hotel}
              highlight={hotel.id === day.hotel?.hotel_id}
              expanded={open === hotel.id}
              onToggle={() => setOpen(open === hotel.id ? null : hotel.id)}
              renderOfferAction={(offer) =>
                offer.offer_id === day.hotel?.offer_id && nights.every((n) => n.hotel?.offer_id === offer.offer_id) ? (
                  <span className="inline-flex items-center gap-1.5 rounded-full bg-nile-soft px-3 py-1.5 text-sm font-semibold whitespace-nowrap text-nile-strong">
                    <Icon name="check" size={15} /> In your trip
                  </span>
                ) : (
                  <ChooseButton onClick={() => apply(offer.offer_id)} loading={busy === offer.offer_id} disabled={busy !== null} />
                )
              }
            />
          ))}
        </div>
      )}
      {day.hotel && (
        <div className="mt-5 flex justify-end">
          <Button variant="ghost" onClick={() => apply(null)} disabled={busy !== null}>
            No hotel for {nights.length > 1 ? 'these nights' : 'this night'}
          </Button>
        </div>
      )}
    </div>
  )
}
