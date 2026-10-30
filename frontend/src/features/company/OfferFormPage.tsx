import { useEffect, useState, type FormEvent } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { useCatalogHotels, useCreateOffer, useMyOffers, useOfferMarket, useUpdateOffer, type MyOffer } from '@/api/company'
import { useHotelOffers, type HotelCard } from '@/api/queries'
import { Button } from '@/components/ui/Button'
import { ErrorState } from '@/components/ui/ErrorState'
import { Icon } from '@/components/ui/Icon'
import { PageLoader } from '@/components/ui/Spinner'
import { TextField } from '@/components/ui/TextField'
import { useToast } from '@/components/ui/Toast'
import { formatEgp } from '@/lib/format'
import { marketFor } from './market'
import { useCurrentCompany } from './useCompanyContext'

const ROOMS = ['Single', 'Double', 'Twin', 'Family', 'Suite']
const POLICIES = [
  { key: '2', label: 'Free cancellation until 48 hours before', free: true, days: 2 },
  { key: '7', label: 'Free cancellation until 7 days before', free: true, days: 7 },
  { key: 'none', label: 'Non-refundable', free: false, days: null },
] as const

interface FormState {
  hotel: { id: number; name: string; city_name: string; stars?: number | null } | null
  room: string
  from: string
  to: string
  price: string
  policy: (typeof POLICIES)[number]['key']
  breakfast: boolean
}

function fromOffer(o: MyOffer): FormState {
  const policy = !o.free_cancellation ? 'none' : (o.cancellation_days ?? 2) >= 7 ? '7' : '2'
  return {
    hotel: { id: o.hotel_id, name: o.hotel_name, city_name: o.city_name },
    room: o.room_type,
    from: o.valid_from ?? '',
    to: o.valid_to ?? '',
    price: String(o.price_per_night),
    policy,
    breakfast: o.breakfast_included,
  }
}

const EMPTY: FormState = { hotel: null, room: 'Double', from: '', to: '', price: '', policy: '2', breakfast: true }

/** C5 · Add an offer, or edit one: hotel, room, dates, price and terms, with the live market beside it. */
export function OfferFormPage() {
  const id = Number(useParams().offerId) || undefined
  const offers = useMyOffers()
  if (id && offers.isPending) return <PageLoader />
  const existing = id ? offers.data?.find((o) => o.id === id) : undefined
  if (id && !existing) return <ErrorState title="Offer not found" />
  return <OfferForm key={id ?? 'new'} existing={existing} />
}

function OfferForm({ existing }: { existing?: MyOffer }) {
  const company = useCurrentCompany()
  const navigate = useNavigate()
  const toast = useToast()
  const create = useCreateOffer()
  const update = useUpdateOffer()
  const [f, setF] = useState<FormState>(existing ? fromOffer(existing) : EMPTY)
  const set = <K extends keyof FormState>(key: K, value: FormState[K]) => setF((s) => ({ ...s, [key]: value }))

  const price = Number(f.price) || 0
  const badDates = Boolean(f.from && f.to && f.to < f.from)
  const policy = POLICIES.find((p) => p.key === f.policy)!
  const ready = f.hotel && f.room.trim().length >= 2 && price > 0 && !badDates

  const submit = (e: FormEvent) => {
    e.preventDefault()
    if (!ready || !f.hotel) return
    const body = {
      room_type: f.room.trim(),
      price_per_night: price,
      breakfast_included: f.breakfast,
      free_cancellation: policy.free,
      cancellation_days: policy.days,
      valid_from: f.from || null,
      valid_to: f.to || null,
    }
    const done = { onSuccess: () => navigate('/company/offers'), onError: (err: Error) => toast(err.message, 'error') }
    if (existing)
      update.mutate({ id: existing.id, body }, { ...done, onSuccess: () => (toast('Offer updated'), done.onSuccess()) })
    else create.mutate({ hotel_id: f.hotel.id, ...body }, { ...done, onSuccess: () => (toast('Offer published'), done.onSuccess()) })
  }

  return (
    <>
      <h1 className="font-display text-[32px] leading-tight sm:text-[38px]">{existing ? 'Edit offer' : 'Add an offer'}</h1>
      <p className="mt-1.5 text-[15px] text-ink-2">
        {existing ? `${existing.hotel_name} · ${existing.city_name}` : 'Pick a hotel from the Egyptora catalog, then set your price.'}
      </p>

      <div className="mt-7 grid gap-5 lg:grid-cols-[minmax(0,1fr)_360px]">
        <form onSubmit={submit} className="flex flex-col gap-6 rounded-[20px] border border-line bg-card p-5 sm:p-6">
          {!existing && <HotelPicker value={f.hotel} onChange={(h) => set('hotel', h)} />}

          <fieldset>
            <legend className="mb-2 text-[15px] font-semibold text-ink-2">Room type</legend>
            <div className="flex flex-wrap gap-2">
              {[...new Set([...ROOMS, f.room])].map((r) => (
                <button
                  key={r}
                  type="button"
                  aria-pressed={f.room === r}
                  onClick={() => set('room', r)}
                  className={`rounded-full border-[1.5px] px-4 py-2 text-[15px] font-semibold ${
                    f.room === r ? 'border-nile bg-nile text-white' : 'border-line-strong bg-card'
                  }`}
                >
                  {r}
                </button>
              ))}
            </div>
          </fieldset>

          <div className="grid gap-4 sm:grid-cols-3">
            <TextField label="Available from" type="date" value={f.from} onChange={(e) => set('from', e.target.value)} />
            <TextField label="Until" type="date" value={f.to} onChange={(e) => set('to', e.target.value)} error={badDates ? 'Must be after the start' : undefined} />
            <TextField label="Price per night" prefix="EGP" inputMode="numeric" required value={f.price} onChange={(e) => set('price', e.target.value.replace(/\D/g, ''))} />
          </div>

          <fieldset>
            <legend className="mb-2 text-[15px] font-semibold text-ink-2">Cancellation policy</legend>
            <div className="flex flex-col gap-2">
              {POLICIES.map((p) => (
                <label
                  key={p.key}
                  className={`flex cursor-pointer items-center gap-3 rounded-[14px] border-[1.5px] px-4 py-3 text-[15px] ${
                    f.policy === p.key ? 'border-terracotta bg-selected' : 'border-line'
                  }`}
                >
                  <input type="radio" name="policy" className="size-4 accent-[#a64b28]" checked={f.policy === p.key} onChange={() => set('policy', p.key)} />
                  {p.label}
                </label>
              ))}
            </div>
          </fieldset>

          <label className="flex cursor-pointer items-center gap-3 text-[15px] font-semibold">
            <button
              type="button"
              role="switch"
              aria-checked={f.breakfast}
              onClick={() => set('breakfast', !f.breakfast)}
              className={`relative h-7 w-12 rounded-full transition-colors ${f.breakfast ? 'bg-nile' : 'bg-line-strong'}`}
            >
              <span className={`absolute top-1 size-5 rounded-full bg-white transition-all ${f.breakfast ? 'left-6' : 'left-1'}`} />
            </button>
            Breakfast included
          </label>

          <div className="flex flex-wrap gap-3 border-t border-line pt-5">
            <Button type="submit" leadingIcon="check" loading={create.isPending || update.isPending} disabled={!ready}>
              {existing ? 'Save changes' : 'Publish offer'}
            </Button>
            <Button variant="outline" onClick={() => navigate(-1)}>
              Cancel
            </Button>
          </div>
        </form>

        <div className="flex flex-col gap-5">
          {f.hotel && (
            <MarketPanel hotelId={f.hotel.id} hotelName={f.hotel.name} room={f.room} price={price} companyId={company.id} offerId={existing?.id} />
          )}
          {f.hotel && price > 0 && (
            <section className="rounded-[20px] border border-line bg-card p-5">
              <h2 className="font-bold">How travelers see it</h2>
              <div className="mt-3 flex items-start justify-between gap-3 rounded-2xl bg-raised p-4">
                <div>
                  <p className="flex items-center gap-1.5 font-bold">
                    {company.name}
                    {company.trust_score && (
                      <span className="inline-flex items-center gap-0.5 text-sm font-semibold text-ink-2">
                        <Icon name="star" size={14} className="text-gold" />
                        {company.trust_score.toFixed(1)}
                      </span>
                    )}
                  </p>
                  <p className="mt-0.5 text-sm text-ink-2">
                    {[f.room, f.breakfast ? 'Breakfast' : null, policy.free ? `Free cancellation until ${policy.days === 7 ? '7 days' : '48 h'}` : 'Non-refundable']
                      .filter(Boolean)
                      .join(' · ')}
                  </p>
                </div>
                <p className="font-bold whitespace-nowrap">{formatEgp(price)}</p>
              </div>
            </section>
          )}
        </div>
      </div>
    </>
  )
}

function HotelPicker({ value, onChange }: { value: FormState['hotel']; onChange: (h: FormState['hotel']) => void }) {
  const [text, setText] = useState('')
  const [query, setQuery] = useState('')
  useEffect(() => {
    const t = setTimeout(() => setQuery(text.trim()), 250)
    return () => clearTimeout(t)
  }, [text])
  const hotels = useCatalogHotels(query)

  if (value)
    return (
      <div>
        <p className="mb-2 text-[15px] font-semibold text-ink-2">Hotel</p>
        <div className="flex items-center gap-3 rounded-[14px] border-[1.5px] border-nile bg-nile-soft/40 px-4 py-3">
          <Icon name="bed" size={20} className="text-nile" />
          <span className="flex-1">
            <span className="font-bold">{value.name}</span>
            <span className="text-ink-2"> · {value.city_name}{value.stars ? ` · ${value.stars}★` : ''}</span>
            <span className="block text-[13px] text-ink-3">Hotel id {value.id} (for CSV imports)</span>
          </span>
          <Button size="sm" variant="ghost" onClick={() => onChange(null)}>
            Change
          </Button>
        </div>
      </div>
    )

  const pick = (h: HotelCard) => onChange({ id: h.id, name: h.name, city_name: h.city_name, stars: h.stars })

  return (
    <div>
      <TextField label="Hotel" placeholder="Search the catalog by name" value={text} onChange={(e) => setText(e.target.value)} hint="Can’t find a hotel? Ask the Egyptora team to add it to the catalog." />
      <ul className="mt-3 max-h-64 overflow-y-auto rounded-[14px] border border-line">
        {hotels.isPending ? (
          <li className="px-4 py-3 text-sm text-ink-3">Loading…</li>
        ) : (hotels.data?.data ?? []).length === 0 ? (
          <li className="px-4 py-3 text-sm text-ink-3">No hotel matches “{query}”.</li>
        ) : (
          hotels.data!.data.map((h) => (
            <li key={h.id} className="border-t border-line first:border-t-0">
              <button type="button" onClick={() => pick(h)} className="flex w-full items-center justify-between gap-3 px-4 py-3 text-left hover:bg-raised">
                <span>
                  <span className="font-semibold">{h.name}</span>
                  <span className="text-sm text-ink-3"> · {h.city_name}{h.stars ? ` · ${h.stars}★` : ''}</span>
                </span>
                <span className="text-[13px] whitespace-nowrap text-ink-3">{h.offers_count} offers</span>
              </button>
            </li>
          ))
        )}
      </ul>
    </div>
  )
}

function MarketPanel({
  hotelId,
  hotelName,
  room,
  price,
  companyId,
  offerId,
}: {
  hotelId: number
  hotelName: string
  room: string
  price: number
  companyId: number
  offerId?: number
}) {
  // an existing offer reads its own market; a new one compares against the public offers for that hotel
  const market = useOfferMarket(offerId)
  const pub = useHotelOffers(offerId ? undefined : hotelId, 'lowest')
  const others = offerId
    ? (market.data?.competitors ?? []).filter((c) => !c.is_mine).map((c) => c.price_per_night)
    : (pub.data?.offers ?? []).filter((o) => o.room_type.toLowerCase() === room.toLowerCase() && o.company.id !== companyId).map((o) => o.price_per_night)
  const loading = offerId ? market.isPending : pub.isPending
  const m = marketFor(price, others)

  return (
    <section className="rounded-[20px] border border-line bg-card p-5">
      <div className="flex items-baseline justify-between gap-3">
        <h2 className="font-bold">Market now</h2>
        <p className="truncate text-sm text-ink-3">
          {hotelName} · {room}
        </p>
      </div>
      {loading ? (
        <PageLoader label="Checking prices…" />
      ) : m.others === 0 ? (
        <p className="mt-3 rounded-xl bg-nile-soft px-4 py-3 text-sm text-nile-strong">No other company sells this room here yet — you’d be the only offer.</p>
      ) : (
        <>
          <dl className="mt-3 grid grid-cols-3 gap-2">
            {[
              ['Lowest now', formatEgp(m.lowest!)],
              ['Average', formatEgp(m.average!)],
              [m.others === 1 ? 'Other offer' : 'Other offers', String(m.others)],
            ].map(([label, value]) => (
              <div key={label}>
                <dd className="font-bold">{value}</dd>
                <dt className="text-[13px] text-ink-3">{label}</dt>
              </div>
            ))}
          </dl>
          {price > 0 && (
            <p
              className={`mt-4 flex gap-2 rounded-xl px-4 py-3 text-sm ${
                m.position === 1 ? 'bg-nile-soft text-nile-strong' : 'bg-gold-soft text-warning'
              }`}
            >
              <Icon name={m.position === 1 ? 'check' : 'trendDown'} size={16} className="mt-0.5 shrink-0" />
              {m.position === 1
                ? `At ${formatEgp(price)} you’d have the lowest price: #1 of ${m.total}.`
                : `At ${formatEgp(price)} you’d be #${m.position} of ${m.total} — ${formatEgp(price - m.lowest!)} above the lowest.`}
            </p>
          )}
        </>
      )}
    </section>
  )
}
