import { useRef, useState, type FormEvent } from 'react'
import { useSearchParams } from 'react-router-dom'
import { useAdminHotels, useAdminOffers, useDeleteHotel, useFlagOffer, useImportHotels, useSaveHotel, type AdminOffer, type HotelInput } from '@/api/admin'
import { useCities, type HotelCard } from '@/api/queries'
import { Button } from '@/components/ui/Button'
import { Dialog } from '@/components/ui/Dialog'
import { Select, TextArea } from '@/components/ui/fields'
import { Icon } from '@/components/ui/Icon'
import { PageLoader } from '@/components/ui/Spinner'
import { TextField } from '@/components/ui/TextField'
import { useToast } from '@/components/ui/Toast'
import { downloadFile } from '@/lib/ics'
import { formatEgp } from '@/lib/format'
import { ConfirmDialog } from '../trips/edit/ConfirmDialog'
import { card, rowClass } from './styles'
import { AdminHeader, Tabs } from './ui'

const HOTEL_TEMPLATE = 'city,name,stars,address,lat,lng,description,amenities,image_url\nLuxor,Theban Palms Hotel,4,"Corniche El Nile, Luxor",25.70,32.64,Nile views,pool;wifi;breakfast,\n'

/** A3 · One hotel catalog; companies compete with offers on each hotel. */
export function HotelsPage() {
  const [params, setParams] = useSearchParams()
  const tab = params.get('tab') === 'offers' ? 'offers' : 'hotels'
  const [adding, setAdding] = useState(false)
  const [importing, setImporting] = useState(false)

  return (
    <>
      <AdminHeader
        title="Hotels & offers"
        subtitle="One catalog of hotels. Companies compete with offers on each one."
        actions={
          <>
            <Button variant="outline" leadingIcon="upload" onClick={() => setImporting(true)}>
              Import CSV
            </Button>
            <Button leadingIcon="plus" onClick={() => setAdding(true)}>
              Add hotel
            </Button>
          </>
        }
      />
      <div className="mt-6">
        <Tabs
          value={tab}
          onChange={(t) => setParams(t === 'offers' ? { tab: 'offers' } : {}, { replace: true })}
          items={[
            { value: 'hotels', label: 'Hotels' },
            { value: 'offers', label: 'Offers to check' },
          ]}
        />
      </div>
      {tab === 'hotels' ? <HotelsTab /> : <OffersTab />}
      <Dialog open={adding} onClose={() => setAdding(false)} title="Add a hotel" size="lg">
        {adding && <HotelForm onDone={() => setAdding(false)} />}
      </Dialog>
      <ImportHotels open={importing} onClose={() => setImporting(false)} />
    </>
  )
}

function HotelsTab() {
  const cities = useCities().data ?? []
  const [search, setSearch] = useState('')
  const [cityId, setCityId] = useState<number | undefined>()
  const hotels = useAdminHotels(search.trim(), cityId)
  const [selectedId, setSelectedId] = useState<number | null>(null)
  const list = hotels.data?.data ?? []
  const selected = list.find((h) => h.id === selectedId) ?? list[0]

  return (
    <div className="mt-5 grid gap-5 lg:grid-cols-[minmax(0,1fr)_420px]">
      <div className="min-w-0">
        <div className="flex flex-wrap items-center gap-3">
          <label className="flex h-11 min-w-0 flex-1 items-center gap-2 rounded-xl border-[1.5px] border-line bg-card px-3 sm:max-w-xs">
            <Icon name="search" size={16} className="text-ink-3" />
            <span className="sr-only">Search hotels</span>
            <input value={search} onChange={(e) => setSearch(e.target.value)} placeholder="Search hotels" className="min-w-0 flex-1 bg-transparent text-sm outline-none" />
          </label>
          <select
            aria-label="City"
            value={cityId ?? ''}
            onChange={(e) => setCityId(e.target.value ? Number(e.target.value) : undefined)}
            className="h-11 rounded-xl border-[1.5px] border-line bg-card px-3 text-sm"
          >
            <option value="">All cities</option>
            {cities.map((c) => (
              <option key={c.id} value={c.id}>
                {c.name}
              </option>
            ))}
          </select>
          <span className="ml-auto text-sm text-ink-3">{hotels.data?.total ?? 0} hotels</span>
        </div>
        <div className={`${card} mt-4 overflow-hidden`}>
          {hotels.isPending ? (
            <PageLoader />
          ) : list.length === 0 ? (
            <p className="px-5 py-10 text-center text-[15px] text-ink-3">No hotels match.</p>
          ) : (
            <ul>
              {list.map((h) => (
                <li key={h.id}>
                  <button type="button" onClick={() => setSelectedId(h.id)} className={`${rowClass(selected?.id === h.id)} grid grid-cols-[1fr_60px_100px] items-center gap-3`}>
                    <span className="min-w-0">
                      <span className="block truncate font-bold">{h.name}</span>
                      <span className="block text-[13px] text-ink-3">
                        {h.city_name}
                        {h.stars ? ` · ${h.stars}★` : ''}
                      </span>
                    </span>
                    <span className="text-sm text-ink-2">{h.offers_count} offers</span>
                    <span className="text-right text-sm font-bold">{h.min_price ? formatEgp(h.min_price) : '—'}</span>
                  </button>
                </li>
              ))}
            </ul>
          )}
        </div>
      </div>
      {selected && <HotelPanel key={selected.id} hotel={selected} />}
    </div>
  )
}

function HotelPanel({ hotel }: { hotel: HotelCard }) {
  const offers = useAdminOffers({ hotel_id: hotel.id })
  const [editing, setEditing] = useState(false)
  const [deleting, setDeleting] = useState(false)
  const remove = useDeleteHotel()
  const toast = useToast()
  const live = (offers.data?.data ?? []).filter((o) => o.status === 'active').map((o) => o.price_per_night)

  return (
    <section className={`${card} p-5 sm:p-6 lg:sticky lg:top-6 lg:max-h-[calc(100dvh-48px)] lg:overflow-y-auto`}>
      {hotel.image_url ? (
        <img src={hotel.image_url} alt="" className="h-36 w-full rounded-2xl object-cover" />
      ) : (
        <div className="grid h-28 place-items-center rounded-2xl bg-placeholder text-terracotta/60">
          <Icon name="bed" size={30} />
        </div>
      )}
      <div className="mt-4 flex items-start justify-between gap-3">
        <div>
          <h2 className="font-display text-[24px] leading-tight">{hotel.name}</h2>
          <p className="mt-1 text-sm text-ink-2">{[hotel.city_name, hotel.address, hotel.stars ? `${hotel.stars}★` : null].filter(Boolean).join(' · ')}</p>
        </div>
        <Button size="sm" variant="outline" leadingIcon="edit" onClick={() => setEditing(true)}>
          Edit
        </Button>
      </div>
      {live.length > 0 && (
        <dl className="mt-4 grid grid-cols-3 gap-2 rounded-2xl bg-raised p-3.5">
          {[
            ['Lowest', formatEgp(Math.min(...live))],
            ['Average', formatEgp(Math.round(live.reduce((a, b) => a + b, 0) / live.length))],
            ['Live offers', String(live.length)],
          ].map(([k, v]) => (
            <div key={k}>
              <dd className="font-bold">{v}</dd>
              <dt className="text-[12px] text-ink-3">{k}</dt>
            </div>
          ))}
        </dl>
      )}
      <p className="mt-5 text-[12px] font-bold tracking-[0.08em] text-ink-3">OFFERS FROM COMPANIES</p>
      {offers.isPending ? <PageLoader /> : <OfferRows offers={offers.data?.data ?? []} />}
      <button type="button" onClick={() => setDeleting(true)} className="mt-5 text-sm font-semibold text-ink-3 hover:text-terracotta">
        Delete hotel
      </button>
      <Dialog open={editing} onClose={() => setEditing(false)} title={`Edit ${hotel.name}`} size="lg">
        {editing && <HotelForm hotel={hotel} onDone={() => setEditing(false)} />}
      </Dialog>
      <ConfirmDialog
        open={deleting}
        onClose={() => setDeleting(false)}
        title={`Delete ${hotel.name}?`}
        confirmLabel="Delete hotel"
        busy={remove.isPending}
        onConfirm={() =>
          remove.mutate(hotel.id, { onSuccess: () => (toast('Hotel deleted'), setDeleting(false)), onError: (e) => toast(e.message, 'error') })
        }
      >
        The hotel and its offers leave the catalog. Hotels already picked in trips can’t be deleted.
      </ConfirmDialog>
    </section>
  )
}

/** Offer rows with the market check and Flag / Unflag. */
function OfferRows({ offers, showHotel = false }: { offers: AdminOffer[]; showHotel?: boolean }) {
  const flag = useFlagOffer()
  const toast = useToast()
  const [flagging, setFlagging] = useState<AdminOffer | null>(null)
  const [reason, setReason] = useState('')

  if (offers.length === 0) return <p className="mt-2 text-[15px] text-ink-3">No offers.</p>
  return (
    <>
      <ul className="mt-1">
        {offers.map((o) => (
          <li key={o.id} className="flex flex-wrap items-center gap-x-3 gap-y-1.5 border-t border-line py-3 first:border-t-0">
            <div className="min-w-0 flex-1 basis-48">
              <p className="font-bold">{showHotel ? `${o.hotel_name} · ${o.company_name}` : o.company_name}</p>
              <p className="text-[13px] text-ink-3">
                {o.room_type} · {o.status === 'active' ? 'live' : o.status}
                {o.market_median ? ` · market ${formatEgp(o.market_median)}` : ''}
              </p>
              {o.flag_reason && <p className="text-[13px] text-terracotta">Flagged: {o.flag_reason}</p>}
            </div>
            {o.price_check === 'low' && <span className="rounded-full bg-terracotta-soft px-2.5 py-0.5 text-[12px] font-semibold text-terracotta-strong">Check price</span>}
            <span className="font-bold whitespace-nowrap">{formatEgp(o.price_per_night)}</span>
            {o.status === 'flagged' ? (
              <Button size="sm" variant="outline" loading={flag.isPending && flag.variables?.id === o.id} onClick={() => flag.mutate({ id: o.id, reason: null }, { onSuccess: () => toast('Offer is live again'), onError: (e) => toast(e.message, 'error') })}>
                Unflag
              </Button>
            ) : (
              <Button size="sm" variant="outline" onClick={() => (setFlagging(o), setReason(o.price_check === 'low' ? 'Price looks too low compared with the market' : ''))}>
                Flag
              </Button>
            )}
          </li>
        ))}
      </ul>
      <Dialog open={flagging !== null} onClose={() => setFlagging(null)} title="Flag this offer?" description="Flagged offers are hidden from travelers. The company sees the reason.">
        <TextArea label="Reason" value={reason} onChange={(e) => setReason(e.target.value)} />
        <div className="mt-4 flex justify-end gap-3">
          <Button variant="outline" onClick={() => setFlagging(null)}>
            Cancel
          </Button>
          <Button
            loading={flag.isPending}
            disabled={reason.trim().length < 5}
            onClick={() =>
              flagging &&
              flag.mutate({ id: flagging.id, reason: reason.trim() }, { onSuccess: () => (toast('Offer flagged'), setFlagging(null)), onError: (e) => toast(e.message, 'error') })
            }
          >
            Flag offer
          </Button>
        </div>
      </Dialog>
    </>
  )
}

function OffersTab() {
  const [which, setWhich] = useState<'low' | 'flagged' | 'active'>('low')
  const offers = useAdminOffers({ status: which === 'flagged' ? 'flagged' : 'active' })
  const list = (offers.data?.data ?? []).filter((o) => which !== 'low' || o.price_check === 'low')
  return (
    <div className={`${card} mt-5 p-5 sm:p-6`}>
      <Tabs
        value={which}
        onChange={setWhich}
        items={[
          { value: 'low', label: 'Too cheap' },
          { value: 'flagged', label: 'Flagged' },
          { value: 'active', label: 'All live' },
        ]}
      />
      <p className="mt-3 text-sm text-ink-3">“Too cheap” = under half of the other companies’ median price for the same hotel and room.</p>
      <div className="mt-2">{offers.isPending ? <PageLoader /> : <OfferRows offers={list} showHotel />}</div>
    </div>
  )
}

function HotelForm({ hotel, onDone }: { hotel?: HotelCard; onDone: () => void }) {
  const cities = useCities().data ?? []
  const save = useSaveHotel()
  const toast = useToast()
  const [v, setV] = useState({
    city_id: hotel?.city_id ?? cities[0]?.id ?? 0,
    name: hotel?.name ?? '',
    stars: hotel?.stars ? String(hotel.stars) : '',
    address: hotel?.address ?? '',
    description: hotel?.description ?? '',
    amenities: (hotel?.amenities ?? []).join(', '),
    image_url: hotel?.image_url ?? '',
    lat: hotel?.lat?.toString() ?? '',
    lng: hotel?.lng?.toString() ?? '',
  })
  const set = (k: keyof typeof v) => (e: { target: { value: string } }) => setV((s) => ({ ...s, [k]: e.target.value }))
  const num = (x: string) => (x.trim() === '' ? null : Number(x))

  const submit = (e: FormEvent) => {
    e.preventDefault()
    const body: HotelInput = {
      city_id: Number(v.city_id),
      name: v.name.trim(),
      stars: num(v.stars),
      address: v.address.trim() || null,
      description: v.description.trim() || null,
      amenities: v.amenities.split(',').map((a) => a.trim()).filter(Boolean),
      image_url: v.image_url.trim() || null,
      lat: num(v.lat),
      lng: num(v.lng),
    }
    save.mutate({ id: hotel?.id, body }, { onSuccess: () => (toast(hotel ? 'Hotel saved' : 'Hotel added'), onDone()), onError: (err) => toast(err.message, 'error') })
  }

  return (
    <form onSubmit={submit} className="grid gap-4 sm:grid-cols-2">
      <TextField label="Name" required minLength={2} value={v.name} onChange={set('name')} />
      <Select label="City" value={v.city_id} onChange={set('city_id')}>
        {cities.map((c) => (
          <option key={c.id} value={c.id}>
            {c.name}
          </option>
        ))}
      </Select>
      <Select label="Stars" value={v.stars} onChange={set('stars')}>
        <option value="">Not rated</option>
        {[1, 2, 3, 4, 5].map((n) => (
          <option key={n} value={n}>
            {n}★
          </option>
        ))}
      </Select>
      <TextField label="Address" value={v.address} onChange={set('address')} />
      <TextField className="sm:col-span-2" label="Amenities" hint="Separated by commas: pool, wifi, breakfast" value={v.amenities} onChange={set('amenities')} />
      <div className="sm:col-span-2">
        <TextArea label="Description" value={v.description} onChange={set('description')} />
      </div>
      <TextField label="Photo URL" type="url" value={v.image_url} onChange={set('image_url')} />
      <div className="grid grid-cols-2 gap-3">
        <TextField label="Latitude" inputMode="decimal" value={v.lat} onChange={set('lat')} />
        <TextField label="Longitude" inputMode="decimal" value={v.lng} onChange={set('lng')} />
      </div>
      <div className="flex justify-end gap-3 sm:col-span-2">
        <Button variant="outline" onClick={onDone}>
          Cancel
        </Button>
        <Button type="submit" loading={save.isPending} disabled={v.name.trim().length < 2}>
          {hotel ? 'Save changes' : 'Add hotel'}
        </Button>
      </div>
    </form>
  )
}

function ImportHotels({ open, onClose }: { open: boolean; onClose: () => void }) {
  const imp = useImportHotels()
  const input = useRef<HTMLInputElement>(null)
  return (
    <Dialog open={open} onClose={onClose} title="Import hotels from a CSV" description="Only city (a city name) and name are required. Hotels that already exist are skipped, so uploading again is safe.">
      {imp.isError && <p className="rounded-xl bg-terracotta-soft px-4 py-3 text-sm whitespace-pre-line text-terracotta-strong">{imp.error.message}</p>}
      {imp.isSuccess && (
        <p className="rounded-xl bg-nile-soft px-4 py-3 text-sm text-nile-strong">
          {imp.data.created} added, {imp.data.skipped} skipped{imp.data.skipped_names.length ? ` (${imp.data.skipped_names.slice(0, 5).join(', ')})` : ''}.
        </p>
      )}
      <div className="mt-5 flex flex-wrap justify-end gap-3">
        <Button variant="outline" leadingIcon="download" onClick={() => downloadFile('egyptora-hotels-template.csv', HOTEL_TEMPLATE, 'text/csv')}>
          Template
        </Button>
        <Button leadingIcon="upload" loading={imp.isPending} onClick={() => input.current?.click()}>
          Choose CSV
        </Button>
        <input
          ref={input}
          type="file"
          accept=".csv,text/csv"
          className="hidden"
          onChange={(e) => {
            const f = e.target.files?.[0]
            if (f) imp.mutate(f)
            e.target.value = ''
          }}
        />
      </div>
    </Dialog>
  )
}
