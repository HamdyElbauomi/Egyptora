import { useState, type FormEvent, type ReactNode } from 'react'
import { Link } from 'react-router-dom'
import { useAddItem, type Trip } from '@/api/queries'
import { useAskPlace, type Answer, type PlaceDetail } from '@/api/scans'
import { Button } from '@/components/ui/Button'
import { Select } from '@/components/ui/fields'
import { Icon } from '@/components/ui/Icon'
import { useToast } from '@/components/ui/Toast'
import { formatEgp, formatTime } from '@/lib/format'
import { formatDuration } from '../trips/tripMath'

const QUICK_QUESTIONS = ['Who built it?', 'When was it built?', 'Why is it famous?']

/** A place's verified facts, where it sits in the trip, and answers grounded in its verified notes. */
export function PlacePanel({ place, trip, badge }: { place: PlaceDetail; trip?: Trip; badge?: ReactNode }) {
  const facts = [
    { label: 'Era', value: place.era },
    { label: 'Open', value: place.opening_hours },
    { label: 'Ticket', value: place.ticket_price ? formatEgp(place.ticket_price) : null },
    { label: 'Plan for', value: place.visit_minutes ? formatDuration(place.visit_minutes) : null },
  ].filter((f): f is { label: string; value: string } => Boolean(f.value))

  return (
    <div>
      {badge}
      <h1 className="mt-3 font-display text-[32px] leading-[1.1] tracking-[-0.01em] sm:text-[38px]">{place.name}</h1>
      <p className="mt-2 flex items-center gap-1.5 text-[15px] text-ink-2">
        <Icon name="pin" size={16} />
        {place.city_name}
      </p>
      {place.short_description && <p className="mt-4 text-[17px] leading-relaxed">{place.short_description}</p>}

      {facts.length > 0 && (
        <dl className="mt-5 grid grid-cols-2 gap-2.5">
          {facts.map((f) => (
            <div key={f.label} className="rounded-2xl border border-line bg-card px-4 py-3">
              <dt className="text-[13px] text-ink-3">{f.label}</dt>
              <dd className="mt-0.5 font-bold">{f.value}</dd>
            </div>
          ))}
        </dl>
      )}

      {place.verified_info && (
        <details className="group mt-4 rounded-2xl border border-line bg-card px-4 py-3">
          <summary className="cursor-pointer list-none text-[15px] font-bold marker:hidden">
            <span className="flex items-center justify-between">
              The story
              <Icon name="chev" size={18} className="transition-transform group-open:rotate-180" />
            </span>
          </summary>
          <p className="mt-2 text-[15px] leading-relaxed whitespace-pre-line text-ink-2">{place.verified_info}</p>
        </details>
      )}
      <p className="mt-3 flex items-center gap-1.5 text-[13px] text-ink-3">
        <Icon name="shield" size={15} className="text-nile" />
        From verified sources
        {place.source_url && (
          <>
            {' · '}
            <a href={place.source_url} target="_blank" rel="noreferrer" className="font-semibold text-terracotta hover:underline">
              {new URL(place.source_url).hostname.replace(/^www\./, '')}
            </a>
          </>
        )}
      </p>

      {trip && <TripLink place={place} trip={trip} />}
      <Ask place={place} />
    </div>
  )
}

function TripLink({ place, trip }: { place: PlaceDetail; trip: Trip }) {
  const add = useAddItem(trip.id)
  const toast = useToast()
  const where = trip.itinerary.flatMap((d) => d.items.filter((i) => i.place_id === place.id).map((i) => ({ day: d, item: i })))[0]
  const sameCity = trip.itinerary.filter((d) => d.city_id === place.city_id)
  const [dayId, setDayId] = useState(sameCity[0]?.id)

  if (where)
    return (
      <Link
        to={`/trips/${trip.id}?day=${where.day.day_number}`}
        className="mt-5 flex items-center gap-3 rounded-2xl bg-gold-soft px-4 py-3.5 text-[15px] text-ink hover:bg-gold-soft/70"
      >
        <Icon name="cal" size={18} className="text-warning" />
        <span className="flex-1">
          <strong>Already in your trip</strong> · Day {where.day.day_number}
          {where.item.start_time ? `, ${formatTime(where.item.start_time)}` : ''}
        </span>
        <Icon name="arrowR" size={18} />
      </Link>
    )

  if (sameCity.length === 0)
    return (
      <p className="mt-5 rounded-2xl bg-muted px-4 py-3.5 text-[15px] text-ink-2">
        {place.city_name} isn’t in this trip, so it can’t be added to a day.
      </p>
    )

  return (
    <div className="mt-5 flex flex-wrap items-end gap-3 rounded-2xl bg-nile-soft p-4">
      <div className="min-w-[180px] flex-1">
        <Select label="Add it to your trip" value={dayId} onChange={(e) => setDayId(Number(e.target.value))}>
          {sameCity.map((d) => (
            <option key={d.id} value={d.id}>
              Day {d.day_number} · {d.city_name}
            </option>
          ))}
        </Select>
      </div>
      <Button
        leadingIcon="plus"
        loading={add.isPending}
        onClick={() =>
          dayId &&
          add.mutate(
            { dayId, body: { place_id: place.id, type: 'visit' } },
            {
              onSuccess: () => toast(`${place.name} added to your trip`),
              onError: (err) => toast(err.message, 'error'),
            },
          )
        }
      >
        Add
      </Button>
    </div>
  )
}

function Ask({ place }: { place: PlaceDetail }) {
  const ask = useAskPlace(place.id)
  const toast = useToast()
  const [question, setQuestion] = useState('')
  const [answers, setAnswers] = useState<{ q: string; a: Answer }[]>([])

  if (!place.verified_info) return null

  const send = (q: string) => {
    const text = q.trim()
    if (!text || ask.isPending) return
    setQuestion('')
    ask.mutate(text, {
      onSuccess: (a) => setAnswers((list) => [...list, { q: text, a }]),
      onError: (err) => toast(err.message, 'error'),
    })
  }

  const submit = (e: FormEvent) => {
    e.preventDefault()
    send(question)
  }

  return (
    <section className="mt-7" aria-label="Ask about this place">
      <h2 className="text-[15px] font-bold text-ink-2">Ask about it</h2>
      <div className="mt-3 flex flex-wrap gap-2">
        {QUICK_QUESTIONS.map((q) => (
          <button
            key={q}
            type="button"
            onClick={() => send(q)}
            disabled={ask.isPending}
            className="rounded-full border-[1.5px] border-line-strong bg-card px-3.5 py-2 text-sm font-medium hover:border-line-muted disabled:opacity-50"
          >
            {q}
          </button>
        ))}
      </div>
      {answers.length > 0 && (
        <ol className="mt-4 flex flex-col gap-3">
          {answers.map(({ q, a }, i) => (
            <li key={i} className="rounded-2xl border border-line bg-card p-4">
              <p className="text-sm font-bold text-ink-2">{q}</p>
              <p className={`mt-1.5 text-[15px] leading-relaxed ${a.grounded ? '' : 'text-ink-3'}`}>{a.answer}</p>
              {a.grounded && (
                <p className="mt-2 flex items-center gap-1 text-[12px] text-nile">
                  <Icon name="shield" size={13} /> From the verified notes
                </p>
              )}
            </li>
          ))}
        </ol>
      )}
      <form onSubmit={submit} className="mt-4 flex items-center gap-2 rounded-[16px] border-[1.5px] border-line-strong bg-card p-1.5 pl-4 focus-within:border-terracotta">
        <label htmlFor="ask-input" className="sr-only">
          Your question
        </label>
        <input
          id="ask-input"
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          maxLength={300}
          placeholder={`Ask anything about ${place.name}…`}
          className="min-w-0 flex-1 bg-transparent py-2 text-[15px] outline-none placeholder:text-ink-4"
        />
        <button
          type="submit"
          aria-label="Ask"
          disabled={!question.trim() || ask.isPending}
          className="grid size-10 shrink-0 place-items-center rounded-xl bg-terracotta text-white disabled:opacity-40"
        >
          <Icon name="send" size={18} />
        </button>
      </form>
    </section>
  )
}
