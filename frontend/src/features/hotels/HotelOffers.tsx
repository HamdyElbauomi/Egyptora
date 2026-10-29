import { useState, type ReactNode } from 'react'
import { useHotelOffers, type HotelCard, type HotelOffer } from '@/api/queries'
import { Button } from '@/components/ui/Button'
import { Chip } from '@/components/ui/Chip'
import { Icon } from '@/components/ui/Icon'
import { Spinner } from '@/components/ui/Spinner'
import { formatEgp, plural } from '@/lib/format'

const AMENITY: Record<string, string> = { wifi: 'Wi-Fi' }

function amenityText(list: string[]): string {
  return list
    .slice(0, 3)
    .map((a) => AMENITY[a] ?? a.charAt(0).toUpperCase() + a.slice(1))
    .join(' · ')
}

function cancellationText(offer: HotelOffer): string {
  if (!offer.free_cancellation) return 'Non-refundable'
  if (offer.cancellation_days) return `Free cancellation until ${plural(offer.cancellation_days, 'day')} before`
  return 'Free cancellation'
}

/** A hotel with its lowest price; opens to compare every company's offer for it. */
export function HotelRow({
  hotel,
  expanded,
  onToggle,
  renderOfferAction,
  highlight,
}: {
  hotel: HotelCard
  expanded: boolean
  onToggle: () => void
  renderOfferAction: (offer: HotelOffer) => ReactNode
  highlight?: boolean
}) {
  return (
    <article className={`overflow-hidden rounded-[20px] border bg-card ${highlight ? 'border-nile' : 'border-line'}`}>
      <button
        type="button"
        onClick={onToggle}
        aria-expanded={expanded}
        className="flex w-full flex-wrap items-center gap-x-4 gap-y-2 p-4 text-left hover:bg-raised sm:flex-nowrap sm:p-5"
      >
        {hotel.image_url ? (
          <img src={hotel.image_url} alt="" className="hidden size-[76px] shrink-0 rounded-2xl object-cover sm:block" />
        ) : (
          <span className="hidden size-[76px] shrink-0 place-items-center rounded-2xl bg-placeholder text-terracotta/70 sm:grid">
            <Icon name="bed" size={26} />
          </span>
        )}
        <span className="min-w-0 basis-full sm:flex-1 sm:basis-auto">
          <span className="block font-display text-[19px] leading-tight sm:text-[21px]">{hotel.name}</span>
          <span className="mt-1 block text-sm text-ink-2">
            {[hotel.address, hotel.stars ? `${hotel.stars}★` : null].filter(Boolean).join(' · ')}
          </span>
          {hotel.amenities.length > 0 && <span className="mt-0.5 block text-[13px] text-ink-3">{amenityText(hotel.amenities)}</span>}
        </span>
        <span className="flex w-full shrink-0 items-baseline justify-between gap-3 sm:block sm:w-auto sm:text-right">
          {hotel.min_price !== null && hotel.min_price !== undefined ? (
            <span className="block text-sm text-ink-3">
              from <span className="text-lg font-bold text-ink">{formatEgp(hotel.min_price)}</span> / night
            </span>
          ) : (
            <span className="block text-sm text-ink-3">No offers yet</span>
          )}
          <span className="mt-1 inline-flex items-center gap-1 text-sm font-bold whitespace-nowrap text-terracotta">
            {expanded ? 'Hide offers' : `Compare ${plural(hotel.offers_count, 'offer')}`}
            <Icon name="chev" size={16} className={`transition-transform ${expanded ? 'rotate-180' : ''}`} />
          </span>
        </span>
      </button>
      {expanded && <OfferList hotelId={hotel.id} renderAction={renderOfferAction} />}
    </article>
  )
}

function OfferList({ hotelId, renderAction }: { hotelId: number; renderAction: (offer: HotelOffer) => ReactNode }) {
  const [sort, setSort] = useState<'best_value' | 'lowest'>('best_value')
  const offers = useHotelOffers(hotelId, sort)

  return (
    <div className="border-t border-line px-4 pb-2 sm:px-5">
      <div className="flex items-center justify-between py-3">
        <p className="hidden text-sm font-semibold text-ink-3 sm:block">Same hotel, different companies</p>
        <div className="ml-auto inline-flex rounded-lg bg-muted p-0.5 text-[13px] font-semibold whitespace-nowrap">
          {(
            [
              ['best_value', 'Best value'],
              ['lowest', 'Lowest price'],
            ] as const
          ).map(([key, label]) => (
            <button
              key={key}
              type="button"
              aria-pressed={sort === key}
              onClick={() => setSort(key)}
              className={`rounded-md px-2.5 py-1 ${sort === key ? 'bg-card text-ink shadow-sm' : 'text-ink-2'}`}
            >
              {label}
            </button>
          ))}
        </div>
      </div>
      {offers.isPending ? (
        <div className="flex justify-center py-6 text-terracotta">
          <Spinner />
        </div>
      ) : offers.isError ? (
        <p className="py-4 text-sm text-terracotta-strong">{offers.error.message}</p>
      ) : offers.data.offers.length === 0 ? (
        <p className="py-4 text-sm text-ink-3">No company sells rooms here right now.</p>
      ) : (
        <ul>
          {offers.data.offers.map((offer) => (
            <li key={offer.offer_id} className="flex flex-wrap items-center gap-x-4 gap-y-2.5 border-t border-line py-3.5 first:border-t-0">
              <div className="min-w-0 basis-full sm:flex-1 sm:basis-56">
                <p className="flex items-center gap-1.5 font-bold">
                  {offer.company.name}
                  {offer.company.trust_score !== null && offer.company.trust_score !== undefined && (
                    <span className="inline-flex items-center gap-0.5 text-sm font-semibold text-ink-2">
                      <Icon name="star" size={14} className="text-gold" />
                      {offer.company.trust_score.toFixed(1)}
                    </span>
                  )}
                </p>
                <p className="mt-0.5 text-sm text-ink-2">
                  {[offer.room_type, offer.breakfast_included ? 'Breakfast' : null, cancellationText(offer)].filter(Boolean).join(' · ')}
                </p>
              </div>
              <div className="flex flex-1 items-center justify-end gap-x-4 sm:flex-none">
                {(offer.is_lowest || offer.is_best_value) && (
                  <Chip tone="nile" className="mr-auto !px-2.5 !py-0.5 !text-[13px] whitespace-nowrap sm:mr-0">
                    {[offer.is_lowest && 'Lowest', offer.is_best_value && 'Best value'].filter(Boolean).join(' · ')}
                  </Chip>
                )}
                <p className="text-right">
                  <span className="block font-bold whitespace-nowrap">{formatEgp(offer.price_per_night)}</span>
                  <span className="block text-[13px] text-ink-3">/ night</span>
                </p>
                <div className="text-right sm:w-[132px]">{renderAction(offer)}</div>
              </div>
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}

export function ChooseButton({ onClick, loading, disabled }: { onClick: () => void; loading?: boolean; disabled?: boolean }) {
  return (
    <Button size="sm" variant="outline" onClick={onClick} loading={loading} disabled={disabled} className="!border-terracotta !text-terracotta">
      Choose
    </Button>
  )
}
