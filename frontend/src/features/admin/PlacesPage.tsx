import { useRef, useState, type FormEvent } from 'react'
import { useAdminPlaces, useDeletePlace, useDeletePlaceImage, useSavePlace, useUploadPlaceImages, type AdminPlace, type PlaceInput } from '@/api/admin'
import { useCities, useInterests } from '@/api/queries'
import { usePlace } from '@/api/scans'
import { Button } from '@/components/ui/Button'
import { Select, TextArea } from '@/components/ui/fields'
import { Icon } from '@/components/ui/Icon'
import { PageLoader } from '@/components/ui/Spinner'
import { TextField } from '@/components/ui/TextField'
import { useToast } from '@/components/ui/Toast'
import { ConfirmDialog } from '../trips/edit/ConfirmDialog'
import { card, rowClass } from './styles'
import { AdminHeader } from './ui'

const TYPES = ['monument', 'museum', 'activity', 'food', 'nature']

/** A place is ready for travelers when it has verified notes and a source to cite. */
function isVerified(p: AdminPlace): boolean {
  return Boolean(p.verified_info && p.source_url)
}

/** A4 · Verified information travelers see in their plan and after a scan. */
export function PlacesPage() {
  const cities = useCities().data ?? []
  const [search, setSearch] = useState('')
  const [cityId, setCityId] = useState<number | undefined>()
  const [type, setType] = useState('')
  const places = useAdminPlaces({ search: search.trim(), city_id: cityId, type })
  const [selectedId, setSelectedId] = useState<number | 'new' | null>(null)
  const list = places.data?.data ?? []
  const selected = selectedId === 'new' ? null : (list.find((p) => p.id === selectedId) ?? list[0] ?? null)
  const cityName = (id: number) => cities.find((c) => c.id === id)?.name ?? ''

  return (
    <>
      <AdminHeader
        title="Places & monuments"
        subtitle="Verified information travelers see in their plan and after a scan."
        actions={
          <Button leadingIcon="plus" onClick={() => setSelectedId('new')}>
            Add place
          </Button>
        }
      />
      <div className="mt-6 flex flex-wrap items-center gap-3">
        <label className="flex h-11 min-w-0 flex-1 items-center gap-2 rounded-xl border-[1.5px] border-line bg-card px-3 sm:max-w-xs">
          <Icon name="search" size={16} className="text-ink-3" />
          <span className="sr-only">Search places</span>
          <input value={search} onChange={(e) => setSearch(e.target.value)} placeholder="Search places" className="min-w-0 flex-1 bg-transparent text-sm outline-none" />
        </label>
        <select aria-label="City" value={cityId ?? ''} onChange={(e) => setCityId(e.target.value ? Number(e.target.value) : undefined)} className="h-11 rounded-xl border-[1.5px] border-line bg-card px-3 text-sm">
          <option value="">All cities</option>
          {cities.map((c) => (
            <option key={c.id} value={c.id}>
              {c.name}
            </option>
          ))}
        </select>
        <select aria-label="Type" value={type} onChange={(e) => setType(e.target.value)} className="h-11 rounded-xl border-[1.5px] border-line bg-card px-3 text-sm capitalize">
          <option value="">All types</option>
          {TYPES.map((t) => (
            <option key={t} value={t}>
              {t}
            </option>
          ))}
        </select>
        <span className="ml-auto text-sm text-ink-3">{places.data?.total ?? 0} places</span>
      </div>

      <div className="mt-4 grid gap-5 lg:grid-cols-[minmax(0,1fr)_480px]">
        <div className={`${card} self-start overflow-hidden`}>
          {places.isPending ? (
            <PageLoader />
          ) : list.length === 0 ? (
            <p className="px-5 py-10 text-center text-[15px] text-ink-3">No places match.</p>
          ) : (
            <ul>
              {list.map((p) => (
                <li key={p.id}>
                  <button type="button" onClick={() => setSelectedId(p.id)} className={`${rowClass(selected?.id === p.id && selectedId !== 'new')} flex items-center gap-3`}>
                    {p.image_url ? (
                      <img src={p.image_url} alt="" className="size-11 shrink-0 rounded-xl object-cover" />
                    ) : (
                      <span className="grid size-11 shrink-0 place-items-center rounded-xl bg-placeholder text-terracotta/70">
                        <Icon name="history" size={18} />
                      </span>
                    )}
                    <span className="min-w-0 flex-1">
                      <span className="block truncate font-bold">{p.name}</span>
                      <span className="block text-[13px] text-ink-3 capitalize">
                        {cityName(p.city_id)} · {p.type}
                        {p.recognition_label ? ' · scannable' : ''}
                      </span>
                    </span>
                    <span className={`shrink-0 rounded-full px-2.5 py-0.5 text-[12px] font-semibold ${isVerified(p) ? 'bg-nile-soft text-nile-strong' : 'bg-gold-soft text-warning'}`}>
                      {isVerified(p) ? 'Verified' : 'Needs info'}
                    </span>
                  </button>
                </li>
              ))}
            </ul>
          )}
        </div>
        {(selectedId === 'new' || selected) && (
          <PlaceEditor
            key={selectedId === 'new' ? 'new' : selected!.id}
            place={selectedId === 'new' ? null : selected}
            onSaved={(id) => setSelectedId(id)}
            onDeleted={() => setSelectedId(null)}
          />
        )}
      </div>
    </>
  )
}

function PlaceEditor({ place, onSaved, onDeleted }: { place: AdminPlace | null; onSaved: (id: number) => void; onDeleted: () => void }) {
  const cities = useCities().data ?? []
  const interests = useInterests().data ?? []
  const save = useSavePlace()
  const remove = useDeletePlace()
  const toast = useToast()
  const [deleting, setDeleting] = useState(false)
  const s = (x: string | null | undefined) => x ?? ''
  const [v, setV] = useState({
    name: s(place?.name),
    city_id: place?.city_id ?? cities[0]?.id ?? 0,
    type: place?.type ?? 'monument',
    short_description: s(place?.short_description),
    verified_info: s(place?.verified_info),
    source_url: s(place?.source_url),
    era: s(place?.era),
    opening_hours: s(place?.opening_hours),
    ticket_price: place?.ticket_price?.toString() ?? '',
    visit_minutes: place?.visit_minutes?.toString() ?? '',
    image_url: s(place?.image_url),
    recognition_label: s(place?.recognition_label),
    interest_ids: place?.interest_ids ?? [],
  })
  const set = (k: keyof typeof v) => (e: { target: { value: string } }) => setV((x) => ({ ...x, [k]: e.target.value }))
  const text = (x: string) => x.trim() || null
  const int = (x: string) => (x.trim() === '' ? null : Number(x))

  const submit = (e: FormEvent) => {
    e.preventDefault()
    const body: PlaceInput = {
      name: v.name.trim(),
      city_id: Number(v.city_id),
      type: v.type,
      short_description: text(v.short_description),
      verified_info: text(v.verified_info),
      source_url: text(v.source_url),
      era: text(v.era),
      opening_hours: text(v.opening_hours),
      ticket_price: int(v.ticket_price),
      visit_minutes: int(v.visit_minutes),
      image_url: text(v.image_url),
      recognition_label: text(v.recognition_label),
      interest_ids: v.interest_ids,
      lat: place?.lat ?? null,
      lng: place?.lng ?? null,
    }
    save.mutate(
      { id: place?.id, body },
      { onSuccess: (saved) => (toast(place ? 'Place saved' : 'Place added'), onSaved(saved.id)), onError: (err) => toast(err.message, 'error') },
    )
  }

  return (
    <section className={`${card} p-5 sm:p-6 lg:sticky lg:top-6 lg:max-h-[calc(100dvh-48px)] lg:overflow-y-auto`}>
      <h2 className="font-display text-[24px] leading-tight">{place ? place.name : 'New place'}</h2>
      <form onSubmit={submit} className="mt-4 grid gap-4 sm:grid-cols-2">
        <TextField label="Name" required minLength={2} value={v.name} onChange={set('name')} />
        <Select label="City" value={v.city_id} onChange={set('city_id')}>
          {cities.map((c) => (
            <option key={c.id} value={c.id}>
              {c.name}
            </option>
          ))}
        </Select>
        <Select label="Type" value={v.type} onChange={set('type')}>
          {TYPES.map((t) => (
            <option key={t} value={t}>
              {t}
            </option>
          ))}
        </Select>
        <TextField label="Era" placeholder="New Kingdom" value={v.era} onChange={set('era')} />
        <div className="sm:col-span-2">
          <TextArea label="Short description" rows={2} value={v.short_description} onChange={set('short_description')} />
        </div>
        <div className="sm:col-span-2">
          <TextArea label="Verified notes" rows={5} hint="Questions travelers ask are answered only from these notes." value={v.verified_info} onChange={set('verified_info')} />
        </div>
        <TextField className="sm:col-span-2" label="Source" type="url" placeholder="https://" value={v.source_url} onChange={set('source_url')} hint="Cited in the traveler app" />
        <TextField label="Ticket" prefix="EGP" inputMode="numeric" value={v.ticket_price} onChange={(e) => setV((x) => ({ ...x, ticket_price: e.target.value.replace(/\D/g, '') }))} />
        <TextField label="Visit length (minutes)" inputMode="numeric" value={v.visit_minutes} onChange={(e) => setV((x) => ({ ...x, visit_minutes: e.target.value.replace(/\D/g, '') }))} />
        <TextField label="Opening hours" placeholder="6:00–17:30" value={v.opening_hours} onChange={set('opening_hours')} />
        <TextField label="Recognition label" placeholder="karnak_temple" hint="The recognizer’s class name" value={v.recognition_label} onChange={set('recognition_label')} />
        <TextField className="sm:col-span-2" label="Cover photo URL" type="url" value={v.image_url} onChange={set('image_url')} />
        <fieldset className="sm:col-span-2">
          <legend className="mb-2 text-[15px] font-semibold text-ink-2">Interests</legend>
          <div className="flex flex-wrap gap-2">
            {interests.map((i) => {
              const on = v.interest_ids.includes(i.id)
              return (
                <button
                  key={i.id}
                  type="button"
                  aria-pressed={on}
                  onClick={() => setV((x) => ({ ...x, interest_ids: on ? x.interest_ids.filter((id) => id !== i.id) : [...x.interest_ids, i.id] }))}
                  className={`rounded-full border-[1.5px] px-3 py-1.5 text-sm font-semibold ${on ? 'border-nile bg-nile text-white' : 'border-line-strong bg-card'}`}
                >
                  {i.name}
                </button>
              )
            })}
          </div>
        </fieldset>
        <div className="flex flex-wrap gap-3 sm:col-span-2">
          <Button type="submit" leadingIcon="check" loading={save.isPending} disabled={v.name.trim().length < 2}>
            {place ? 'Save changes' : 'Add place'}
          </Button>
          {place && (
            <Button variant="outline" onClick={() => setDeleting(true)}>
              Delete
            </Button>
          )}
        </div>
      </form>
      {place && <Photos placeId={place.id} />}
      <ConfirmDialog
        open={deleting}
        onClose={() => setDeleting(false)}
        title={`Delete ${place?.name}?`}
        confirmLabel="Delete place"
        busy={remove.isPending}
        onConfirm={() => place && remove.mutate(place.id, { onSuccess: () => (toast('Place deleted'), setDeleting(false), onDeleted()), onError: (e) => toast(e.message, 'error') })}
      >
        It disappears from the catalog and new trips. Places already in trips can’t be deleted.
      </ConfirmDialog>
    </section>
  )
}

function Photos({ placeId }: { placeId: number }) {
  const detail = usePlace(placeId)
  const upload = useUploadPlaceImages()
  const remove = useDeletePlaceImage()
  const toast = useToast()
  const input = useRef<HTMLInputElement>(null)
  const images = detail.data?.images ?? []
  return (
    <div className="mt-6 border-t border-line pt-5">
      <div className="flex items-center justify-between">
        <p className="text-[12px] font-bold tracking-[0.08em] text-ink-3">RECOGNITION PHOTOS · {images.length}</p>
        <Button size="sm" variant="outline" leadingIcon="upload" loading={upload.isPending} onClick={() => input.current?.click()}>
          Upload
        </Button>
        <input
          ref={input}
          type="file"
          multiple
          accept="image/jpeg,image/png,image/webp"
          className="hidden"
          onChange={(e) => {
            const files = Array.from(e.target.files ?? [])
            if (files.length)
              upload.mutate({ id: placeId, files }, { onSuccess: (r) => toast(`${r.length} photos added`), onError: (err) => toast(err.message, 'error') })
            e.target.value = ''
          }}
        />
      </div>
      {images.length === 0 ? (
        <p className="mt-2 text-sm text-ink-3">No photos yet. They’re used on the place page and to train the recognizer.</p>
      ) : (
        <ul className="mt-3 grid grid-cols-4 gap-2 sm:grid-cols-5">
          {images.map((img) => (
            <li key={img.id} className="group relative">
              <img src={img.image_url} alt="" className="aspect-square w-full rounded-xl bg-placeholder object-cover" />
              <button
                type="button"
                aria-label="Delete photo"
                onClick={() => remove.mutate(img.id, { onError: (err) => toast(err.message, 'error') })}
                className="absolute top-1 right-1 hidden size-7 place-items-center rounded-full bg-inverse/80 text-white group-hover:grid"
              >
                <Icon name="x" size={14} />
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}
