import { Link } from 'react-router-dom'
import { useStats, type Stats } from '@/api/admin'
import { Button } from '@/components/ui/Button'
import { ErrorState } from '@/components/ui/ErrorState'
import { Icon, type IconName } from '@/components/ui/Icon'
import { PageLoader } from '@/components/ui/Spinner'
import { downloadFile } from '@/lib/ics'
import { formatDate, formatEgp, formatNumber, plural } from '@/lib/format'
import { aiSuccess, pct, reportCsv } from './overview'
import { AdminHeader } from './ui'
import { card } from './styles'

/** A1 · The platform at a glance. */
export function OverviewPage() {
  const stats = useStats()
  if (stats.isPending) return <PageLoader />
  if (stats.isError) return <ErrorState title="We couldn’t load the overview" action={<Button onClick={() => stats.refetch()}>Try again</Button>} />
  const s = stats.data

  const tiles = [
    { label: 'Trips planned', value: formatNumber(s.trips.total), sub: `${s.trips.created_last_7_days} in the last 7 days` },
    { label: 'Live offers', value: formatNumber(s.offers.active), sub: `from ${plural(s.companies.approved, 'company', 'companies')}` },
    { label: 'Pending approvals', value: formatNumber(s.companies.pending), sub: s.companies.pending ? 'companies waiting' : 'all caught up' },
    { label: 'AI answer success', value: pct(aiSuccess(s.ai)), sub: 'hotel search · chat · camera' },
  ]

  return (
    <>
      <AdminHeader
        title="Overview"
        subtitle="What’s happening across Egyptora."
        actions={
          <Button leadingIcon="download" onClick={() => downloadFile(`egyptora-report-${new Date().toISOString().slice(0, 10)}.csv`, reportCsv(s), 'text/csv')}>
            Export report
          </Button>
        }
      />
      <div className="mt-7 grid grid-cols-2 gap-4 lg:grid-cols-4">
        {tiles.map((t) => (
          <div key={t.label} className={`${card} p-5`}>
            <p className="text-sm text-ink-2">{t.label}</p>
            <p className="mt-2 font-display text-[34px] leading-none">{t.value}</p>
            <p className="mt-2 text-[13px] text-ink-3">{t.sub}</p>
          </div>
        ))}
      </div>

      <div className="mt-5 grid gap-5 lg:grid-cols-[minmax(0,1fr)_400px]">
        <div className="flex min-w-0 flex-col gap-5">
          <TripsChart days={s.trips.per_day} />
          <Destinations stats={s} />
        </div>
        <Attention stats={s} />
      </div>
    </>
  )
}

const BAR_AREA = 150 // px

function TripsChart({ days }: { days: Stats['trips']['per_day'] }) {
  const max = Math.max(1, ...days.map((d) => d.trips))
  const half = Math.floor(days.length / 2)
  return (
    <section className={`${card} p-5 sm:p-6`}>
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h2 className="text-lg font-bold">Trips planned per day</h2>
        <div className="flex gap-4 text-sm text-ink-2" aria-hidden>
          <span className="flex items-center gap-1.5">
            <span className="size-2.5 rounded-full bg-terracotta" /> This week
          </span>
          <span className="flex items-center gap-1.5">
            <span className="size-2.5 rounded-full bg-gold" /> Week before
          </span>
        </div>
      </div>
      <div className="mt-5 flex items-end gap-[2px] sm:gap-1.5" style={{ height: BAR_AREA + 24 }} aria-hidden>
        {days.map((d, i) => (
          <div key={d.date} className="group relative flex h-full flex-1 flex-col justify-end">
            <div
              className={`w-full rounded-t-[4px] ${i >= half ? 'bg-terracotta' : 'bg-gold'} transition-opacity group-hover:opacity-80`}
              style={{ height: Math.max(d.trips ? 4 : 1, (d.trips / max) * BAR_AREA) }}
            />
            <span className="mt-1.5 text-center text-[11px] text-ink-3 tabular-nums">{d.date.slice(8)}</span>
            <span className="pointer-events-none absolute bottom-full left-1/2 z-10 mb-1 hidden -translate-x-1/2 rounded-lg bg-inverse px-2.5 py-1.5 text-[12px] whitespace-nowrap text-on-dark group-hover:block">
              {formatDate(d.date)} · {plural(d.trips, 'trip')}
            </span>
          </div>
        ))}
      </div>
      <table className="sr-only">
        <caption>Trips planned per day, last 14 days</caption>
        <tbody>
          {days.map((d) => (
            <tr key={d.date}>
              <th>{d.date}</th>
              <td>{d.trips}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </section>
  )
}

function Destinations({ stats }: { stats: Stats }) {
  const list = stats.top_destinations
  return (
    <section className={`${card} p-5 sm:p-6`}>
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-bold">Top destinations</h2>
        <p className="text-sm text-ink-3">Share of planned trips</p>
      </div>
      {list.length === 0 ? (
        <p className="mt-3 text-[15px] text-ink-3">No trips yet.</p>
      ) : (
        <ul className="mt-4 flex flex-col gap-3">
          {list.map((c) => (
            <li key={c.city_id} className="grid grid-cols-[110px_1fr_48px] items-center gap-3 text-[15px]" title={`${plural(c.trips, 'trip')}`}>
              <span className="truncate">{c.city_name}</span>
              <span className="h-2 rounded-full bg-track">
                <span className="block h-full rounded-full bg-nile" style={{ width: `${c.share * 100}%` }} />
              </span>
              <span className="text-right font-bold tabular-nums">{pct(c.share)}</span>
            </li>
          ))}
        </ul>
      )}
      {stats.trips.avg_total_cost !== null && stats.trips.avg_total_cost !== undefined && (
        <p className="mt-4 text-sm text-ink-3">
          Average trip: {stats.trips.avg_days} days · {formatEgp(stats.trips.avg_total_cost)} per person
        </p>
      )}
    </section>
  )
}

function Attention({ stats }: { stats: Stats }) {
  const n = stats.needs_attention
  const items: { count: number; icon: IconName; title: string; text: string; to: string }[] = [
    { count: n.pending_companies, icon: 'briefcase', title: `${plural(n.pending_companies, 'company', 'companies')} waiting for approval`, text: 'Check the license and set the starting trust score', to: '/admin/companies' },
    { count: n.failed_searches, icon: 'code', title: `${plural(n.failed_searches, 'hotel search', 'hotel searches')} failed`, text: 'Fix the SQL and add it to training', to: '/admin/ai' },
    { count: n.scans_to_review, icon: 'camera', title: `${plural(n.scans_to_review, 'low-confidence scan')}`, text: 'Label the photo so the recognizer learns', to: '/admin/ai?tab=scans' },
    { count: n.low_price_offers, icon: 'alert', title: `${plural(n.low_price_offers, 'offer')} look${n.low_price_offers === 1 ? 's' : ''} too cheap`, text: 'Under half of the market price', to: '/admin/hotels?tab=offers' },
  ]
  const open = items.filter((i) => i.count > 0)
  return (
    <section className={`${card} p-5 sm:p-6`}>
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-bold">Needs your attention</h2>
        {open.length > 0 && <span className="grid size-7 place-items-center rounded-full bg-terracotta-soft text-sm font-bold text-terracotta-strong">{open.length}</span>}
      </div>
      {open.length === 0 ? (
        <p className="mt-4 flex items-center gap-2 rounded-2xl bg-nile-soft px-4 py-3 text-[15px] text-nile-strong">
          <Icon name="check" size={18} /> Nothing waiting. Nice.
        </p>
      ) : (
        <ul className="mt-3">
          {open.map((i) => (
            <li key={i.title} className="flex items-center gap-3 border-t border-line py-3.5 first:border-t-0">
              <span className="grid size-10 shrink-0 place-items-center rounded-xl bg-muted text-terracotta">
                <Icon name={i.icon} size={18} />
              </span>
              <div className="min-w-0 flex-1">
                <p className="font-bold">{i.title}</p>
                <p className="text-sm text-ink-3">{i.text}</p>
              </div>
              <Link to={i.to} className="shrink-0 rounded-[10px] border-[1.5px] border-line-strong bg-card px-3.5 py-2 text-sm font-bold hover:border-line-muted">
                Review
              </Link>
            </li>
          ))}
        </ul>
      )}
    </section>
  )
}
