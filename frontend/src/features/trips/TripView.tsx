import { useState, type ReactNode } from 'react'
import type { TripDay, TripItem } from '@/api/queries'
import { Chip } from '@/components/ui/Chip'
import { Icon, type IconName } from '@/components/ui/Icon'
import { formatDate, formatDateRange, formatEgp, formatNumber, formatTime, plural } from '@/lib/format'
import { costBreakdown, gapAfter, itemDuration, route } from './tripMath'

export interface TripViewData {
  title: string
  start_date?: string | null
  end_date?: string | null
  days: number
  total_cost: number
  budget_total?: number | null
  over_budget?: boolean
  itinerary: TripDay[]
}

interface TripViewProps {
  trip: TripViewData
  eyebrow?: string
  /** extra chips after route and days, e.g. interests */
  chips?: ReactNode
  actions?: ReactNode
}

const TYPE_TAG: Record<string, { label: string; tone: 'gold' | 'nile' | 'muted' } | undefined> = {
  meal: { label: 'Food', tone: 'gold' },
  transport: { label: 'Travel', tone: 'nile' },
  free_time: { label: 'Free time', tone: 'muted' },
}

const TYPE_ICON: Record<string, IconName> = { visit: 'history', meal: 'food', transport: 'train', free_time: 'leaf' }

/** Title, day tabs, the day's timeline, the cost card and tonight's hotel. */
export function TripView({ trip, eyebrow, chips, actions }: TripViewProps) {
  const [dayIndex, setDayIndex] = useState(0)
  const day = trip.itinerary[Math.min(dayIndex, trip.itinerary.length - 1)]
  const dates = formatDateRange(trip.start_date, trip.end_date)

  return (
    <div className="grid gap-6 lg:grid-cols-[minmax(0,1fr)_380px] lg:gap-8">
      <div className="min-w-0">
        <div className="flex flex-wrap items-end justify-between gap-5">
          <div className="min-w-0">
            {eyebrow && <p className="text-sm font-bold tracking-[0.08em] text-nile uppercase">{eyebrow}</p>}
            <h1 className="mt-2 font-display text-[34px] leading-[1.1] tracking-[-0.01em] sm:text-[44px]">{trip.title}</h1>
            <div className="mt-4 flex flex-wrap gap-2.5">
              <Chip icon="pin">{route(trip.itinerary)}</Chip>
              <Chip icon="cal">{dates || plural(trip.days, 'day')}</Chip>
              {dates && <Chip>{plural(trip.days, 'day')}</Chip>}
              {chips}
            </div>
          </div>
          {actions && <div className="flex flex-wrap gap-3">{actions}</div>}
        </div>

        <div role="tablist" aria-label="Days" className="-mx-4 mt-7 flex gap-2.5 overflow-x-auto px-4 pb-1 sm:mx-0 sm:flex-wrap sm:px-0">
          {trip.itinerary.map((d, i) => {
            const active = d.id === day?.id
            return (
              <button
                key={d.id}
                type="button"
                role="tab"
                aria-selected={active}
                onClick={() => setDayIndex(i)}
                className={`shrink-0 rounded-xl border-[1.5px] px-4 py-3 text-[15px] font-semibold transition-colors ${
                  active ? 'border-inverse bg-inverse text-on-dark' : 'border-line bg-card text-ink hover:border-line-strong'
                }`}
              >
                Day {d.day_number} · {d.city_name}
              </button>
            )
          })}
        </div>

        {day && <DayTimeline day={day} />}
      </div>

      <aside className="flex flex-col gap-5 lg:pt-1">
        <CostCard trip={trip} />
        {day && <HotelCard day={day} />}
      </aside>
    </div>
  )
}

function DayTimeline({ day }: { day: TripDay }) {
  return (
    <section role="tabpanel" aria-label={`Day ${day.day_number}`} className="mt-5 rounded-[22px] border border-line bg-card p-4 sm:p-6">
      <div className="mb-4 flex flex-wrap items-baseline justify-between gap-2 px-1">
        <h2 className="font-display text-[22px]">
          Day {day.day_number} · {day.city_name}
        </h2>
        <p className="text-sm text-ink-3">
          {[formatDate(day.date), plural(day.items.length, 'stop'), day.day_cost ? formatEgp(day.day_cost) : null]
            .filter(Boolean)
            .join(' · ')}
        </p>
      </div>
      {day.items.length === 0 ? (
        <p className="rounded-2xl bg-raised px-5 py-8 text-center text-[15px] text-ink-3">
          A free day — nothing planned yet.
        </p>
      ) : (
        <ol>
          {day.items.map((item, i) => {
            const gap = gapAfter(item, day.items[i + 1])
            return (
              <li key={item.id}>
                <StopRow item={item} />
                {gap !== null && gap >= 10 && (
                  <p className="my-1 ml-[74px] border-l-2 border-line py-2 pl-3 text-[13px] text-ink-3 sm:ml-[110px]">
                    {gap} min to move on
                  </p>
                )}
                {gap === null && i < day.items.length - 1 && <div className="h-3" />}
              </li>
            )
          })}
        </ol>
      )}
    </section>
  )
}

function StopRow({ item }: { item: TripItem }) {
  const tag = TYPE_TAG[item.type]
  const duration = itemDuration(item)
  const cost = item.cost ? formatEgp(item.cost) : null
  return (
    <div className="flex items-center gap-3 sm:gap-5">
      <span className="w-[62px] shrink-0 text-base font-bold tabular-nums sm:w-[90px] sm:pl-5 sm:text-[17px]">
        {formatTime(item.start_time)}
      </span>
      {item.place_image_url ? (
        <img src={item.place_image_url} alt="" className="hidden size-[76px] shrink-0 rounded-2xl object-cover sm:block" />
      ) : (
        <span className="hidden size-[76px] shrink-0 place-items-center rounded-2xl bg-placeholder text-terracotta/70 sm:grid">
          <Icon name={TYPE_ICON[item.type] ?? 'pin'} size={26} />
        </span>
      )}
      <div className="flex min-w-0 flex-1 flex-wrap items-center justify-between gap-x-4 gap-y-1 py-2">
        <div className="min-w-0">
          <p className="text-[17px] font-bold sm:text-lg">{item.place_name ?? 'Free time'}</p>
          {item.note && <p className="mt-1 text-[15px] text-ink-2">{item.note}</p>}
        </div>
        <div className="flex flex-col items-start gap-1.5 sm:items-end">
          {tag && <Chip tone={tag.tone} className="!px-2.5 !py-0.5 !text-[13px]">{tag.label}</Chip>}
          <p className="text-sm text-ink-3">{[duration, cost].filter(Boolean).join(' · ')}</p>
        </div>
      </div>
    </div>
  )
}

function CostCard({ trip }: { trip: TripViewData }) {
  const cost = costBreakdown(trip.itinerary, trip.total_cost)
  const rows = [
    { label: `Hotels · ${plural(cost.nights, 'night')}`, value: cost.hotels, color: 'bg-terracotta' },
    { label: 'Tickets', value: cost.tickets, color: 'bg-nile' },
    { label: 'Other', value: cost.other, color: 'bg-gold' },
  ].filter((r) => r.value > 0)
  const budget = trip.budget_total ?? null

  return (
    <section className="rounded-[22px] border border-line bg-card p-6">
      <p className="text-[15px] font-semibold text-ink-2">Estimated cost per person</p>
      <p className="mt-2 font-display text-[40px] leading-none">{formatEgp(trip.total_cost)}</p>
      {rows.length > 0 && (
        <div className="mt-5 flex h-2.5 gap-0.5 overflow-hidden rounded-full bg-track">
          {rows.map((r) => (
            <span key={r.label} className={r.color} style={{ width: `${(r.value / Math.max(cost.total, 1)) * 100}%` }} />
          ))}
        </div>
      )}
      <dl className="mt-4 space-y-2 text-[15px]">
        {rows.map((r) => (
          <div key={r.label} className="flex items-center justify-between">
            <dt className="flex items-center gap-2.5">
              <span className={`size-2.5 rounded-sm ${r.color}`} />
              {r.label}
            </dt>
            <dd className="font-semibold tabular-nums">{formatNumber(r.value)}</dd>
          </div>
        ))}
      </dl>
      {budget !== null && (
        <p
          className={`mt-4 flex gap-2 rounded-xl px-3.5 py-3 text-sm ${
            trip.over_budget ? 'bg-terracotta-soft text-terracotta-strong' : 'bg-nile-soft text-nile-strong'
          }`}
        >
          <Icon name={trip.over_budget ? 'alert' : 'check'} size={16} className="mt-0.5" />
          {trip.over_budget
            ? `${formatEgp(trip.total_cost - budget)} over your ${formatEgp(budget)} budget.`
            : `Within your ${formatEgp(budget)} budget.`}
        </p>
      )}
      <p className="mt-4 text-[13px] text-ink-3">Estimates. Final prices are confirmed when you book.</p>
    </section>
  )
}

function HotelCard({ day }: { day: TripDay }) {
  const hotel = day.hotel
  return (
    <section className="flex gap-4 rounded-[22px] border border-line bg-card p-5">
      <span className="grid size-11 shrink-0 place-items-center rounded-xl bg-nile-soft text-nile">
        <Icon name="bed" size={22} />
      </span>
      <div className="min-w-0">
        <p className="text-sm text-ink-3">Tonight · Day {day.day_number}</p>
        {hotel ? (
          <>
            <p className="mt-0.5 text-[17px] font-bold">
              {hotel.hotel_name}
              {hotel.stars ? <span className="ml-1.5 text-sm font-semibold text-gold">{'★'.repeat(hotel.stars)}</span> : null}
            </p>
            <p className="mt-1 text-sm text-ink-2">
              via {hotel.company_name} · {formatEgp(hotel.price_per_night)} / night
            </p>
            <div className="mt-2 flex flex-wrap gap-1.5">
              <Chip className="!px-2.5 !py-0.5 !text-[13px]">{hotel.room_type}</Chip>
              {hotel.breakfast_included && <Chip tone="gold" className="!px-2.5 !py-0.5 !text-[13px]">Breakfast</Chip>}
              {hotel.free_cancellation && <Chip tone="nile" className="!px-2.5 !py-0.5 !text-[13px]">Free cancellation</Chip>}
            </div>
          </>
        ) : (
          <p className="mt-0.5 text-[15px] text-ink-2">No hotel picked for this night yet.</p>
        )}
      </div>
    </section>
  )
}
