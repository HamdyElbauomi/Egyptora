import { Link } from 'react-router-dom'
import { useAlerts, useDashboard, useInsights, useMyOffers, useMyReviews, useReadAlert } from '@/api/company'
import { Button, ButtonLink } from '@/components/ui/Button'
import { ErrorState } from '@/components/ui/ErrorState'
import { Icon } from '@/components/ui/Icon'
import { PageLoader } from '@/components/ui/Spinner'
import { Stars } from '@/components/ui/Stars'
import { formatDate, formatEgp, formatNumber } from '@/lib/format'
import { PositionChip } from './PositionChip'
import { useCurrentCompany } from './useCompanyContext'

function greeting(): string {
  const h = new Date().getHours()
  return h < 12 ? 'Good morning' : h < 18 ? 'Good afternoon' : 'Good evening'
}

/** C3 · How the company's offers are doing. */
export function DashboardPage() {
  const company = useCurrentCompany()
  const dash = useDashboard()
  const offers = useMyOffers()

  if (dash.isPending) return <PageLoader />
  if (dash.isError) return <ErrorState title="We couldn’t load the dashboard" action={<Button onClick={() => dash.refetch()}>Try again</Button>} />
  const d = dash.data

  const stats = [
    { label: 'Live offers', value: formatNumber(d.active_offers), sub: `${d.paused_offers} paused${d.flagged_offers ? ` · ${d.flagged_offers} flagged` : ''}` },
    { label: 'Chosen by travelers', value: formatNumber(d.times_chosen), sub: 'nights picked in trips' },
    { label: 'Lowest price on', value: `${d.cheapest_in_market} of ${d.active_offers}`, sub: 'hotels where you’re cheapest' },
    {
      label: 'Trust score',
      value: d.trust_score?.toFixed(1) ?? '—',
      sub: `${company.initial_score ? `initial ${company.initial_score.toFixed(1)} · ` : ''}${d.reviews_count} reviews`,
    },
  ]

  const ranked = [...(offers.data ?? [])]
    .filter((o) => o.status === 'active')
    .sort((a, b) => (b.position ?? 0) / Math.max(b.competitors, 1) - (a.position ?? 0) / Math.max(a.competitors, 1))
    .slice(0, 5)

  return (
    <>
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <h1 className="font-display text-[32px] leading-tight sm:text-[38px]">
            {greeting()}, {company.name}
          </h1>
          <p className="mt-1.5 text-[15px] text-ink-2">Here’s how your offers are doing.</p>
        </div>
        <ButtonLink to="/company/offers/new" leadingIcon="plus">
          Add offer
        </ButtonLink>
      </div>

      <div className="mt-7 grid grid-cols-2 gap-4 lg:grid-cols-4">
        {stats.map((s) => (
          <div key={s.label} className="rounded-[20px] border border-line bg-card p-5">
            <p className="text-sm text-ink-2">{s.label}</p>
            <p className="mt-2 font-display text-[32px] leading-none">{s.value}</p>
            <p className="mt-2 text-[13px] text-ink-3">{s.sub}</p>
          </div>
        ))}
      </div>

      <div className="mt-5 grid gap-5 lg:grid-cols-[minmax(0,1fr)_380px]">
        <section className="rounded-[20px] border border-line bg-card p-5 sm:p-6">
          <div className="flex flex-wrap items-baseline justify-between gap-2">
            <h2 className="text-lg font-bold">Your price position</h2>
            <p className="text-sm text-ink-3">Compared with other companies on the same hotel</p>
          </div>
          {offers.isPending ? (
            <PageLoader />
          ) : ranked.length === 0 ? (
            <p className="mt-4 rounded-2xl bg-raised px-5 py-8 text-center text-[15px] text-ink-3">
              No live offers yet. <Link to="/company/offers/new" className="font-bold text-terracotta">Add your first offer</Link>
            </p>
          ) : (
            <ul className="mt-3">
              {ranked.map((o) => (
                <li key={o.id} className="flex flex-wrap items-center gap-3 border-t border-line py-3.5 first:border-t-0">
                  <span className="hidden size-11 shrink-0 place-items-center rounded-xl bg-placeholder text-terracotta/70 sm:grid">
                    <Icon name="bed" size={20} />
                  </span>
                  <div className="min-w-0 flex-1">
                    <p className="font-bold">{o.hotel_name}</p>
                    <p className="text-sm text-ink-2">
                      You: {formatEgp(o.price_per_night)}
                      {o.position === 1 ? ' · You have the lowest price' : o.lowest_price ? ` · Lowest: ${formatEgp(o.lowest_price)}` : ''}
                    </p>
                  </div>
                  <PositionChip offer={o} />
                  <ButtonLink to={`/company/offers/${o.id}/edit`} size="sm" variant="outline" className={o.position && o.position > 1 ? '!border-terracotta !text-terracotta' : ''}>
                    {o.position && o.position > 1 ? 'Update price' : 'View offer'}
                  </ButtonLink>
                </li>
              ))}
            </ul>
          )}
        </section>

        <div className="flex flex-col gap-5">
          <Alerts />
          <LatestReview />
        </div>
      </div>
    </>
  )
}

function Alerts() {
  const alerts = useAlerts()
  const read = useReadAlert()
  const unread = (alerts.data ?? []).filter((a) => !a.is_read).slice(0, 4)
  return (
    <section className="rounded-[20px] border border-line bg-card p-5">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-bold">Price alerts</h2>
        {unread.length > 0 && <span className="rounded-full bg-terracotta px-2.5 py-0.5 text-[13px] font-bold text-white">{unread.length}</span>}
      </div>
      {unread.length === 0 ? (
        <p className="mt-2 text-[15px] text-ink-3">Nothing new. We’ll tell you when a competitor goes below your price.</p>
      ) : (
        <ul className="mt-2">
          {unread.map((a) => (
            <li key={a.id} className="flex gap-3 border-t border-line py-3 first:border-t-0">
              <Icon name={a.type === 'undercut' ? 'trendDown' : 'alert'} size={18} className="mt-0.5 shrink-0 text-terracotta" />
              <div className="min-w-0 flex-1">
                <p className="text-[15px]">{a.message}</p>
                <p className="mt-1 flex gap-3 text-sm">
                  <Link to={`/company/offers/${a.offer_id}/edit`} className="font-bold text-terracotta">
                    Review offer
                  </Link>
                  <button type="button" onClick={() => read.mutate(a.id)} className="font-semibold text-ink-3 hover:text-ink">
                    Dismiss
                  </button>
                </p>
              </div>
            </li>
          ))}
        </ul>
      )}
    </section>
  )
}

function LatestReview() {
  const reviews = useMyReviews(1)
  const insights = useInsights()
  const latest = reviews.data?.data[0]
  return (
    <section className="rounded-[20px] border border-line bg-card p-5">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-bold">Latest review</h2>
        <Link to="/company/profile" className="text-sm font-bold text-terracotta">
          All reviews
        </Link>
      </div>
      {latest ? (
        <>
          <div className="mt-3">
            <Stars value={latest.rating} />
          </div>
          {latest.comment && <p className="mt-2 text-[15px]">“{latest.comment}”</p>}
          <p className="mt-2 text-sm text-ink-3">
            {latest.reviewer_name} · {formatDate(latest.created_at.slice(0, 10))}
          </p>
        </>
      ) : (
        <p className="mt-2 text-[15px] text-ink-3">No reviews yet. Travelers can review you after picking your offer in a trip.</p>
      )}
      {insights.data && insights.data.top_complaints.length > 0 && (
        <p className="mt-4 rounded-xl bg-gold-soft px-3.5 py-2.5 text-sm text-warning">
          Travelers mention: {insights.data.top_complaints.slice(0, 3).join(', ')}
        </p>
      )}
    </section>
  )
}
