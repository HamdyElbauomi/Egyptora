import { useMemo, useState, type FormEvent } from 'react'
import { useAddItem, useCityPlaces, type Place, type Trip, type TripDay } from '@/api/queries'
import { Button } from '@/components/ui/Button'
import { Dialog } from '@/components/ui/Dialog'
import { ErrorState } from '@/components/ui/ErrorState'
import { Select, TextArea } from '@/components/ui/fields'
import { Icon, type IconName } from '@/components/ui/Icon'
import { PageLoader } from '@/components/ui/Spinner'
import { TextField } from '@/components/ui/TextField'
import { useToast } from '@/components/ui/Toast'
import { formatEgp } from '@/lib/format'
import { formatDuration } from '../tripMath'

type Tab = 'place' | 'other'

const PLACE_ICON: Record<string, IconName> = { monument: 'history', museum: 'image', activity: 'zap', food: 'food', nature: 'leaf' }

/** Add a place from the day's city, or a meal / free time with a note. New stops go at the end of the day. */
export function AddStopDialog({ trip, day, onClose }: { trip: Trip; day: TripDay | null; onClose: () => void }) {
  const [tab, setTab] = useState<Tab>('place')
  return (
    <Dialog
      open={day !== null}
      onClose={onClose}
      size="lg"
      title={day ? `Add to day ${day.day_number}` : ''}
      description={day ? `It goes at the end of the day in ${day.city_name}. You can move it after.` : undefined}
    >
      {day && (
        <>
          <div role="tablist" className="mb-5 inline-flex rounded-xl bg-muted p-1">
            {(
              [
                ['place', 'A place'],
                ['other', 'Meal or free time'],
              ] as const
            ).map(([key, label]) => (
              <button
                key={key}
                type="button"
                role="tab"
                aria-selected={tab === key}
                onClick={() => setTab(key)}
                className={`rounded-[10px] px-4 py-2 text-[15px] font-semibold ${tab === key ? 'bg-card text-ink shadow-sm' : 'text-ink-2'}`}
              >
                {label}
              </button>
            ))}
          </div>
          {tab === 'place' ? (
            <PlacePicker key={day.id} trip={trip} day={day} onDone={onClose} />
          ) : (
            <OtherForm key={day.id} tripId={trip.id} day={day} onDone={onClose} />
          )}
        </>
      )}
    </Dialog>
  )
}

function PlacePicker({ trip, day, onDone }: { trip: Trip; day: TripDay; onDone: () => void }) {
  const places = useCityPlaces(day.city_id)
  const add = useAddItem(trip.id)
  const toast = useToast()
  const [query, setQuery] = useState('')
  const [adding, setAdding] = useState<number | null>(null)

  const inTrip = useMemo(() => {
    const where = new Map<number, number>()
    for (const d of trip.itinerary) for (const i of d.items) if (i.place_id) where.set(i.place_id, d.day_number)
    return where
  }, [trip])

  if (places.isPending) return <PageLoader label="Loading places…" />
  if (places.isError)
    return <ErrorState title="We couldn’t load the places" action={<Button onClick={() => places.refetch()}>Try again</Button>} />

  const q = query.trim().toLowerCase()
  // places not in the trip yet come first
  const list = places.data
    .filter((p) => !q || p.name.toLowerCase().includes(q))
    .sort((a, b) => Number(inTrip.has(a.id)) - Number(inTrip.has(b.id)))

  const choose = (place: Place) => {
    setAdding(place.id)
    add.mutate(
      { dayId: day.id, body: { place_id: place.id, type: 'visit' } },
      {
        onSuccess: () => {
          toast(`${place.name} added to day ${day.day_number}`)
          onDone()
        },
        onError: (err) => {
          toast(err.message, 'error')
          setAdding(null)
        },
      },
    )
  }

  return (
    <div>
      <TextField label="Search" placeholder={`Places in ${day.city_name}`} value={query} onChange={(e) => setQuery(e.target.value)} />
      {list.length === 0 ? (
        <p className="mt-6 rounded-2xl bg-raised px-5 py-8 text-center text-[15px] text-ink-3">
          {places.data.length === 0 ? `We don’t have places for ${day.city_name} yet.` : 'No place matches that name.'}
        </p>
      ) : (
        <ul className="mt-4 flex flex-col gap-2">
          {list.map((place) => {
            const onDay = inTrip.get(place.id)
            const facts = [
              place.visit_minutes ? formatDuration(place.visit_minutes) : null,
              place.ticket_price ? formatEgp(place.ticket_price) : null,
              place.opening_hours,
            ].filter(Boolean)
            return (
              <li key={place.id} className="flex items-center gap-4 rounded-2xl border border-line bg-raised px-4 py-3.5">
                <span className="grid size-11 shrink-0 place-items-center rounded-xl bg-placeholder text-terracotta/80">
                  <Icon name={PLACE_ICON[place.type] ?? 'pin'} size={20} />
                </span>
                <div className="min-w-0 flex-1">
                  <p className="font-bold">{place.name}</p>
                  {place.short_description && <p className="mt-0.5 text-sm text-ink-2">{place.short_description}</p>}
                  {facts.length > 0 && <p className="mt-0.5 text-[13px] text-ink-3">{facts.join(' · ')}</p>}
                </div>
                {onDay ? (
                  <span className="shrink-0 text-sm font-semibold text-ink-3">On day {onDay}</span>
                ) : (
                  <Button size="sm" variant="outline" leadingIcon="plus" loading={adding === place.id} disabled={adding !== null} onClick={() => choose(place)}>
                    Add
                  </Button>
                )}
              </li>
            )
          })}
        </ul>
      )}
    </div>
  )
}

function OtherForm({ tripId, day, onDone }: { tripId: number; day: TripDay; onDone: () => void }) {
  const add = useAddItem(tripId)
  const toast = useToast()
  const [type, setType] = useState<'meal' | 'free_time'>('meal')
  const [note, setNote] = useState('')
  const [start, setStart] = useState('')
  const [end, setEnd] = useState('')
  const [cost, setCost] = useState('')
  const badTimes = Boolean(start && end && end <= start)

  const submit = (e: FormEvent) => {
    e.preventDefault()
    if (!note.trim() || badTimes) return
    add.mutate(
      {
        dayId: day.id,
        body: {
          place_id: null,
          type,
          note: note.trim(),
          start_time: start ? `${start}:00` : null,
          end_time: end ? `${end}:00` : null,
          cost: cost ? Number(cost) : null,
        },
      },
      {
        onSuccess: () => {
          toast(`Added to day ${day.day_number}`)
          onDone()
        },
        onError: (err) => toast(err.message, 'error'),
      },
    )
  }

  return (
    <form onSubmit={submit} className="flex flex-col gap-5">
      <Select label="What is it?" value={type} onChange={(e) => setType(e.target.value as 'meal' | 'free_time')}>
        <option value="meal">A meal</option>
        <option value="free_time">Free time</option>
      </Select>
      <TextArea
        label="Name it"
        required
        maxLength={500}
        placeholder={type === 'meal' ? 'e.g. Lunch on the Corniche' : 'e.g. Rest at the hotel'}
        value={note}
        onChange={(e) => setNote(e.target.value)}
      />
      <div className="grid grid-cols-2 gap-4">
        <TextField label="Starts (optional)" type="time" value={start} onChange={(e) => setStart(e.target.value)} hint="Empty = after the last stop" />
        <TextField label="Ends (optional)" type="time" value={end} onChange={(e) => setEnd(e.target.value)} error={badTimes ? 'Must be after the start' : undefined} />
      </div>
      <TextField label="Cost per person (optional)" prefix="EGP" inputMode="numeric" value={cost} onChange={(e) => setCost(e.target.value.replace(/\D/g, ''))} />
      <div className="flex justify-end gap-3">
        <Button variant="outline" onClick={onDone}>
          Cancel
        </Button>
        <Button type="submit" loading={add.isPending} disabled={!note.trim() || badTimes} leadingIcon="plus">
          Add to day {day.day_number}
        </Button>
      </div>
    </form>
  )
}
