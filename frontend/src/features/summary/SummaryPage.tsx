import { useState } from 'react'
import { Link } from 'react-router-dom'
import { useSaveTrip, useShareTrip, useSummary, type Summary, type Trip } from '@/api/queries'
import { Button } from '@/components/ui/Button'
import { ErrorState } from '@/components/ui/ErrorState'
import { Icon } from '@/components/ui/Icon'
import { PageLoader } from '@/components/ui/Spinner'
import { useToast } from '@/components/ui/Toast'
import { formatDate, formatDateRange, formatEgp, formatNumber, plural } from '@/lib/format'
import { buildIcs, downloadFile } from '@/lib/ics'
import { TripDetailsDialog } from '../trips/edit/TripDetailsDialog'
import { useCurrentTrip } from '../trips/TripLayout'
import { itemTitle, route } from '../trips/tripMath'

/** Where the money goes, the hotels to book, and Save / Share. */
export function SummaryPage() {
  const trip = useCurrentTrip()
  const summary = useSummary(trip.id)
  const save = useSaveTrip(trip.id)
  const toast = useToast()
  const [details, setDetails] = useState(false)

  if (summary.isPending) return <PageLoader label="Adding it all up…" />
  if (summary.isError)
    return <ErrorState title="We couldn’t load the summary" action={<Button onClick={() => summary.refetch()}>Try again</Button>} />

  const s = summary.data
  const saved = trip.status === 'saved'
  const dates = formatDateRange(s.start_date, s.end_date)

  return (
    <>
      <div className="flex flex-wrap items-end justify-between gap-5">
        <div className="min-w-0">
          <p className="text-sm font-bold tracking-[0.08em] text-nile uppercase">Trip summary</p>
          <h1 className="mt-2 font-display text-[34px] leading-[1.1] tracking-[-0.01em] sm:text-[44px]">{s.title}</h1>
          <p className="mt-2 text-[17px] text-ink-2">
            {[route(trip.itinerary), plural(s.days, 'day'), plural(s.places_count, 'place'), dates || 'No start date yet'].join(' · ')}
          </p>
        </div>
        <div className="flex flex-wrap gap-3 print:hidden">
          <Button variant="outline" leadingIcon="edit" onClick={() => setDetails(true)}>
            Edit
          </Button>
          <Button
            variant="outline"
            leadingIcon={saved ? 'check' : 'bookmark'}
            loading={save.isPending}
            disabled={saved}
            onClick={() =>
              save.mutate(undefined, {
                onSuccess: () => toast('Trip saved'),
                onError: (err) => toast(err.message, 'error'),
              })
            }
          >
            {saved ? 'Saved' : 'Save'}
          </Button>
        </div>
      </div>

      <div className="mt-7 grid gap-6 lg:grid-cols-[minmax(0,1fr)_400px] lg:gap-7">
        <DayList trip={trip} summary={s} />
        <div className="flex flex-col gap-5">
          <CostCard summary={s} />
          <HotelsToBook summary={s} />
          <ShareCard trip={trip} summary={s} />
        </div>
      </div>
      <TripDetailsDialog trip={trip} open={details} onClose={() => setDetails(false)} />
    </>
  )
}

function DayList({ trip, summary }: { trip: Trip; summary: Summary }) {
  return (
    <ol className="self-start overflow-hidden rounded-[22px] border border-line bg-card">
      {summary.per_day.map((d, i) => {
        const day = trip.itinerary.find((x) => x.day_number === d.day_number)
        const stops = day?.items.map(itemTitle).join(' · ')
        return (
          <li key={d.day_number} className="flex items-center gap-4 border-t border-line px-4 py-5 first:border-t-0 sm:gap-5 sm:px-6">
            <span
              className={`grid size-[64px] shrink-0 place-content-center rounded-2xl text-center sm:size-[72px] ${
                i === 0 ? 'bg-terracotta text-white' : 'bg-muted text-ink'
              }`}
            >
              <span className={`text-[11px] font-bold tracking-[0.08em] ${i === 0 ? 'text-white/85' : 'text-ink-3'}`}>DAY</span>
              <span className="font-display text-[28px] leading-none">{d.day_number}</span>
            </span>
            <div className="min-w-0 flex-1">
              <p className="font-display text-[21px] leading-tight">
                {d.city_name}
                {d.date && <span className="ml-2 font-sans text-sm font-semibold text-ink-3">{formatDate(d.date)}</span>}
              </p>
              <p className="mt-1 text-[15px] text-ink-2">{stops || 'A free day'}</p>
              <p className="mt-1.5 flex items-center gap-1.5 text-sm text-ink-2 md:hidden">
                <Icon name="bed" size={16} className="text-nile" />
                {d.hotel_name ?? 'No hotel yet'}
              </p>
            </div>
            <p className="hidden w-[200px] shrink-0 items-center gap-2 text-sm text-ink-2 md:flex">
              <Icon name="bed" size={18} className="text-nile" />
              {d.hotel_name ?? 'No hotel yet'}
            </p>
            <Link
              to={`/trips/${trip.id}?day=${d.day_number}`}
              aria-label={`Edit day ${d.day_number}`}
              className="grid size-10 shrink-0 place-items-center rounded-xl bg-muted text-ink-2 hover:text-terracotta print:hidden"
            >
              <Icon name="edit" size={18} />
            </Link>
          </li>
        )
      })}
    </ol>
  )
}

function CostCard({ summary }: { summary: Summary }) {
  const c = summary.costs
  const rows = [
    { label: `Hotels · ${plural(summary.nights_with_hotel, 'night')}`, value: c.hotels },
    { label: 'Tickets', value: c.tickets },
    { label: 'Other', value: c.other },
  ]
  return (
    <section className="rounded-[22px] bg-inverse p-6 text-on-dark">
      <p className="text-[15px] text-on-dark-muted">Estimated total per person</p>
      <p className="mt-2 font-display text-[44px] leading-none text-gold-light">{formatEgp(c.total)}</p>
      <dl className="mt-5">
        {rows.map((r) => (
          <div key={r.label} className="flex justify-between border-t border-white/10 py-3 text-[15px] first:border-t-0">
            <dt className="text-on-dark-muted">{r.label}</dt>
            <dd className="font-semibold tabular-nums">{formatNumber(r.value)}</dd>
          </div>
        ))}
      </dl>
      {summary.remaining !== null && summary.remaining !== undefined && (
        <p
          className={`mt-2 rounded-xl px-3.5 py-2.5 text-sm font-semibold ${
            summary.over_budget ? 'bg-terracotta text-white' : 'bg-nile text-white'
          }`}
        >
          {summary.over_budget
            ? `${formatEgp(-summary.remaining)} over your ${formatEgp(summary.budget_total ?? 0)} budget`
            : `${formatEgp(summary.remaining)} left of your ${formatEgp(summary.budget_total ?? 0)} budget`}
        </p>
      )}
      <p className="mt-4 text-[13px] text-on-dark-muted">Estimates. Final prices are confirmed when you book.</p>
    </section>
  )
}

function HotelsToBook({ summary }: { summary: Summary }) {
  if (summary.hotels.length === 0) return null
  return (
    <section className="rounded-[22px] border border-line bg-card p-6">
      <h2 className="text-lg font-bold">Hotels to book</h2>
      <ul className="mt-3">
        {summary.hotels.map((h) => (
          <li key={`${h.offer_id}-${h.first_night}`} className="border-t border-line py-3.5 first:border-t-0">
            <div className="flex items-start justify-between gap-3">
              <div className="min-w-0">
                <p className="font-bold">{h.hotel_name}</p>
                <p className="mt-0.5 text-sm text-ink-2">
                  via {h.company_name} · {h.room_type} · {plural(h.nights, 'night')}
                  {h.first_night ? ` from ${formatDate(h.first_night)}` : ''}
                </p>
                <p className="mt-0.5 text-[13px] text-ink-3">
                  {[h.breakfast_included ? 'Breakfast' : null, h.free_cancellation ? 'Free cancellation' : 'Non-refundable']
                    .filter(Boolean)
                    .join(' · ')}
                </p>
              </div>
              <p className="shrink-0 text-right font-bold tabular-nums">{formatNumber(h.subtotal)}</p>
            </div>
          </li>
        ))}
      </ul>
    </section>
  )
}

function ShareCard({ trip, summary }: { trip: Trip; summary: Summary }) {
  const share = useShareTrip(trip.id)
  const toast = useToast()
  const link = summary.share_token ? `${window.location.origin}/shared/${summary.share_token}` : null

  const copy = async () => {
    if (!link) return
    try {
      await navigator.clipboard.writeText(link)
      toast('Link copied')
    } catch {
      toast('Couldn’t copy — select the link and copy it', 'error')
    }
  }

  const calendar = () => {
    const days = trip.itinerary
      .filter((d) => d.date)
      .map((d) => ({
        date: d.date!,
        title: `Egyptora · Day ${d.day_number} · ${d.city_name}`,
        details: [d.items.map(itemTitle).join(', '), d.hotel ? `Hotel: ${d.hotel.hotel_name}` : null].filter(Boolean).join('\n'),
      }))
    downloadFile(`egyptora-trip-${trip.id}.ics`, buildIcs(trip.id, days), 'text/calendar')
  }

  return (
    <section className="rounded-[22px] border border-line bg-card p-6 print:hidden">
      <h2 className="text-lg font-bold">Share with your travel group</h2>
      <p className="mt-1 text-sm text-ink-2">Anyone with the link sees the latest plan. They can’t change it.</p>
      {link ? (
        <>
          <div className="mt-4 flex items-center gap-2 rounded-[14px] border-[1.5px] border-line-strong bg-raised p-1.5 pl-3.5">
            <input
              readOnly
              value={link}
              aria-label="Share link"
              onFocus={(e) => e.target.select()}
              className="min-w-0 flex-1 bg-transparent text-sm text-ink-2 outline-none"
            />
            <Button size="sm" variant="dark" onClick={copy}>
              Copy link
            </Button>
          </div>
          <button
            type="button"
            onClick={() => share.mutate(false, { onSuccess: () => toast('The link no longer works') })}
            disabled={share.isPending}
            className="mt-2 text-sm font-semibold text-ink-3 hover:text-terracotta"
          >
            Stop sharing
          </button>
        </>
      ) : (
        <Button
          className="mt-4 w-full"
          leadingIcon="share"
          loading={share.isPending}
          onClick={() => share.mutate(true, { onError: (err) => toast(err.message, 'error') })}
        >
          Create a share link
        </Button>
      )}
      <div className="mt-4 grid grid-cols-2 gap-2.5">
        <Button size="sm" variant="outline" leadingIcon="download" onClick={() => window.print()}>
          Save as PDF
        </Button>
        <Button size="sm" variant="outline" leadingIcon="cal" onClick={calendar} disabled={!trip.start_date}>
          Add to calendar
        </Button>
      </div>
      {!trip.start_date && <p className="mt-2 text-[13px] text-ink-3">Set a start date (Edit) to add the days to your calendar.</p>}
    </section>
  )
}
