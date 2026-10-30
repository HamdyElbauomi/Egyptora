import { useState, type FormEvent } from 'react'
import { useFilteredHotels, useHotelSearch, type HotelFilters } from '@/api/hotels'
import { useChooseOffer, useCities, type HotelCard, type HotelOffer, type Trip } from '@/api/queries'
import { Button } from '@/components/ui/Button'
import { Dialog } from '@/components/ui/Dialog'
import { ErrorState } from '@/components/ui/ErrorState'
import { Select } from '@/components/ui/fields'
import { Icon } from '@/components/ui/Icon'
import { PageLoader } from '@/components/ui/Spinner'
import { TextField } from '@/components/ui/TextField'
import { useToast } from '@/components/ui/Toast'
import { formatEgp, plural } from '@/lib/format'
import { useOptionalTrip } from '../trips/TripLayout'
import { ChooseButton, HotelRow } from './HotelOffers'

const EXAMPLES = ['3-star in Luxor under 1,500', 'Hotels in Aswan with free cancellation', 'Luxury hotel in Cairo']

/** Search hotels in plain words, or with filters; compare companies; pick one for the trip. */
export function HotelsPage() {
  const trip = useOptionalTrip()
  const search = useHotelSearch()
  const [question, setQuestion] = useState('')
  const [mode, setMode] = useState<'search' | 'filters'>('filters')
  const [filters, setFilters] = useState<HotelFilters>({ city_id: trip?.itinerary[0]?.city_id, sort: 'price' })
  const filtered = useFilteredHotels(filters, mode === 'filters')
  const [open, setOpen] = useState<number | null>(null)
  const [choosing, setChoosing] = useState<{ hotel: HotelCard; offer: HotelOffer } | null>(null)

  const ask = (q: string) => {
    const text = q.trim()
    if (!text) return
    setQuestion(text)
    setMode('search')
    setOpen(null)
    search.mutate({ question: text, trip_id: trip?.id ?? null }, { onSuccess: (r) => r.fallback && setMode('filters') })
  }

  const submit = (e: FormEvent) => {
    e.preventDefault()
    ask(question)
  }

  const result = mode === 'search' ? search.data : undefined
  const hotels = mode === 'search' ? (result?.results ?? []) : (filtered.data?.data ?? [])
  const loading = mode === 'search' ? search.isPending : filtered.isPending
  const tripCities = new Set(trip?.itinerary.map((d) => d.city_id))

  return (
    <div className="grid gap-6 lg:grid-cols-[minmax(0,1fr)_340px] lg:gap-8">
      <div className="min-w-0">
        <form onSubmit={submit} className="flex items-center gap-2 rounded-[18px] border-[1.5px] border-terracotta bg-card p-2 pl-4">
          <Icon name="search" size={22} className="text-terracotta" />
          <label htmlFor="hotel-q" className="sr-only">
            Describe the hotel you want
          </label>
          <input
            id="hotel-q"
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            maxLength={300}
            placeholder="hotel in Luxor under 1,500 a night with breakfast"
            className="min-w-0 flex-1 bg-transparent py-2.5 text-[17px] outline-none placeholder:text-ink-4"
          />
          <Button type="submit" loading={search.isPending} disabled={!question.trim()}>
            Search
          </Button>
        </form>

        <div className="mt-4 flex flex-wrap items-center gap-2">
          {mode === 'search' && result?.understood ? (
            <>
              <span className="text-[15px] text-ink-3">Understood as</span>
              <span className="rounded-full bg-muted px-3.5 py-1.5 text-[15px] font-semibold">{result.understood}</span>
            </>
          ) : (
            <>
              <span className="text-[15px] text-ink-3">Try</span>
              {EXAMPLES.map((ex) => (
                <button
                  key={ex}
                  type="button"
                  onClick={() => ask(ex)}
                  className="rounded-full border-[1.5px] border-line-strong bg-card px-3.5 py-1.5 text-sm font-medium hover:border-line-muted"
                >
                  {ex}
                </button>
              ))}
            </>
          )}
          <button
            type="button"
            onClick={() => setMode(mode === 'filters' ? 'search' : 'filters')}
            disabled={mode === 'search' && !search.data && !search.isPending}
            className="ml-auto inline-flex items-center gap-1.5 text-[15px] font-bold text-terracotta disabled:opacity-0"
          >
            <Icon name="sliders" size={16} />
            {mode === 'filters' ? 'Back to search results' : 'Use filters'}
          </button>
        </div>

        {search.data?.fallback && mode === 'filters' && (
          <p className="mt-4 rounded-2xl bg-gold-soft px-4 py-3 text-[15px] text-warning">{search.data.message}</p>
        )}
        {mode === 'filters' && <FilterBar filters={filters} onChange={setFilters} />}

        <div className="mt-5">
          {loading ? (
            <PageLoader label="Finding hotels…" />
          ) : mode === 'filters' && filtered.isError ? (
            <ErrorState title="We couldn’t load hotels" action={<Button onClick={() => filtered.refetch()}>Try again</Button>} />
          ) : (
            <>
              <p className="mb-3 text-[15px] text-ink-2">
                <strong className="text-ink">{plural(hotels.length, 'hotel')}</strong>
                {mode === 'search' && result?.message ? ` · ${result.message}` : ' match'}
              </p>
              <div className="flex flex-col gap-3">
                {hotels.map((hotel) => (
                  <HotelRow
                    key={hotel.id}
                    hotel={hotel}
                    expanded={open === hotel.id}
                    onToggle={() => setOpen(open === hotel.id ? null : hotel.id)}
                    highlight={trip?.itinerary.some((d) => d.hotel?.hotel_id === hotel.id)}
                    renderOfferAction={(offer) =>
                      !trip ? null : trip.itinerary.some((d) => d.hotel?.offer_id === offer.offer_id) ? (
                        <span className="inline-flex items-center gap-1.5 rounded-full bg-nile-soft px-3 py-1.5 text-sm font-semibold whitespace-nowrap text-nile-strong">
                          <Icon name="check" size={15} /> In your trip
                        </span>
                      ) : tripCities.has(hotel.city_id) ? (
                        <ChooseButton onClick={() => setChoosing({ hotel, offer })} />
                      ) : (
                        <span className="text-[13px] text-ink-3">Not in your trip’s cities</span>
                      )
                    }
                  />
                ))}
              </div>
            </>
          )}
        </div>
      </div>

      <aside className="flex flex-col gap-5">
        {trip ? <TripNights trip={trip} /> : <SearchTips />}
      </aside>
      {trip && <ChooseNights trip={trip} choice={choosing} onClose={() => setChoosing(null)} />}
    </div>
  )
}

function FilterBar({ filters, onChange }: { filters: HotelFilters; onChange: (f: HotelFilters) => void }) {
  const cities = useCities().data ?? []
  const [price, setPrice] = useState(filters.max_price ? String(filters.max_price) : '')
  return (
    <div className="mt-4 grid grid-cols-2 gap-3 rounded-[18px] border border-line bg-card p-4 sm:grid-cols-4">
      <Select label="City" value={filters.city_id ?? ''} onChange={(e) => onChange({ ...filters, city_id: e.target.value ? Number(e.target.value) : undefined })}>
        <option value="">All cities</option>
        {cities.map((c) => (
          <option key={c.id} value={c.id}>
            {c.name}
          </option>
        ))}
      </Select>
      <Select label="Stars" value={filters.stars ?? ''} onChange={(e) => onChange({ ...filters, stars: e.target.value ? Number(e.target.value) : undefined })}>
        <option value="">Any</option>
        {[5, 4, 3, 2].map((n) => (
          <option key={n} value={n}>
            {n}★
          </option>
        ))}
      </Select>
      <TextField
        label="Max per night"
        prefix="EGP"
        inputMode="numeric"
        value={price}
        onChange={(e) => setPrice(e.target.value.replace(/\D/g, ''))}
        onBlur={() => onChange({ ...filters, max_price: price ? Number(price) : undefined })}
        onKeyDown={(e) => e.key === 'Enter' && onChange({ ...filters, max_price: price ? Number(price) : undefined })}
      />
      <Select label="Sort" value={filters.sort} onChange={(e) => onChange({ ...filters, sort: e.target.value as HotelFilters['sort'] })}>
        <option value="price">Lowest price</option>
        <option value="stars">Most stars</option>
        <option value="name">Name</option>
      </Select>
    </div>
  )
}

function TripNights({ trip }: { trip: Trip }) {
  return (
    <section className="rounded-[22px] bg-nile-soft p-5">
      <p className="text-sm font-semibold text-nile-strong">For your trip</p>
      <ul className="mt-2 flex flex-col gap-2.5">
        {trip.itinerary.map((d) => (
          <li key={d.id} className="text-[15px]">
            <span className="font-semibold">
              Day {d.day_number} · {d.city_name}
            </span>
            <span className="block text-sm text-ink-2">
              {d.hotel ? `${d.hotel.hotel_name} via ${d.hotel.company_name} · ${formatEgp(d.hotel.price_per_night)}` : 'No hotel yet'}
            </span>
          </li>
        ))}
      </ul>
    </section>
  )
}

function SearchTips() {
  return (
    <section className="rounded-[22px] border border-line bg-card p-5">
      <h2 className="font-bold">Search like you’d ask a friend</h2>
      <ul className="mt-3 space-y-2 text-[15px] text-ink-2">
        <li>Name a city: “in Aswan”</li>
        <li>Add a price: “under 2,000”</li>
        <li>Stars or style: “4-star”, “luxury”, “cheap”</li>
        <li>Extras: “with free cancellation”</li>
      </ul>
      <p className="mt-3 text-sm text-ink-3">Arabic works too: “فندق 4 نجوم في الأقصر”.</p>
    </section>
  )
}

function ChooseNights({ trip, choice, onClose }: { trip: Trip; choice: { hotel: HotelCard; offer: HotelOffer } | null; onClose: () => void }) {
  return (
    <Dialog open={choice !== null} onClose={onClose} title={choice ? `${choice.hotel.name}` : ''} description={choice ? `via ${choice.offer.company.name} · ${formatEgp(choice.offer.price_per_night)} / night` : undefined}>
      {choice && <NightsForm key={choice.offer.offer_id} trip={trip} choice={choice} onDone={onClose} />}
    </Dialog>
  )
}

function NightsForm({ trip, choice, onDone }: { trip: Trip; choice: { hotel: HotelCard; offer: HotelOffer }; onDone: () => void }) {
  const choose = useChooseOffer(trip.id)
  const toast = useToast()
  const nights = trip.itinerary.filter((d) => d.city_id === choice.hotel.city_id)
  const [picked, setPicked] = useState<number[]>(nights.map((d) => d.id))
  const [busy, setBusy] = useState(false)

  const apply = async () => {
    setBusy(true)
    try {
      for (const id of picked) await choose.mutateAsync({ dayId: id, offerId: choice.offer.offer_id })
      toast(`${choice.hotel.name} set for ${plural(picked.length, 'night')}`)
      onDone()
    } catch (err) {
      toast(err instanceof Error ? err.message : 'Couldn’t set the hotel', 'error')
      setBusy(false)
    }
  }

  return (
    <div>
      <p className="text-[15px] font-semibold text-ink-2">Which nights?</p>
      <ul className="mt-3 flex flex-col gap-2">
        {nights.map((d) => (
          <li key={d.id}>
            <label className="flex cursor-pointer items-center gap-3 rounded-2xl border border-line bg-raised px-4 py-3">
              <input
                type="checkbox"
                className="size-4 accent-[#a64b28]"
                checked={picked.includes(d.id)}
                onChange={() => setPicked((p) => (p.includes(d.id) ? p.filter((x) => x !== d.id) : [...p, d.id]))}
              />
              <span className="flex-1">
                <span className="font-semibold">Day {d.day_number}</span>
                <span className="block text-sm text-ink-3">Now: {d.hotel ? `${d.hotel.hotel_name} · ${formatEgp(d.hotel.price_per_night)}` : 'no hotel'}</span>
              </span>
            </label>
          </li>
        ))}
      </ul>
      <div className="mt-5 flex justify-end gap-3">
        <Button variant="outline" onClick={onDone}>
          Cancel
        </Button>
        <Button onClick={apply} loading={busy} disabled={picked.length === 0}>
          Use for {plural(picked.length, 'night')}
        </Button>
      </div>
    </div>
  )
}
