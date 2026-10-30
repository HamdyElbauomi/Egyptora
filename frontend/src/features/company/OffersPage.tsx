import { useMemo, useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useDeleteOffer, useImportOffers, useMyOffers, usePauseOffer, type MyOffer } from '@/api/company'
import { Button, ButtonLink } from '@/components/ui/Button'
import { Dialog } from '@/components/ui/Dialog'
import { ErrorState } from '@/components/ui/ErrorState'
import { Icon } from '@/components/ui/Icon'
import { Menu } from '@/components/ui/Menu'
import { PageLoader } from '@/components/ui/Spinner'
import { useToast } from '@/components/ui/Toast'
import { downloadFile } from '@/lib/ics'
import { formatDate, formatEgp } from '@/lib/format'
import { ConfirmDialog } from '../trips/edit/ConfirmDialog'
import { PositionChip } from './PositionChip'

const TABS = [
  { status: 'active', label: 'Live' },
  { status: 'paused', label: 'Paused' },
  { status: 'expired', label: 'Expired' },
  { status: 'flagged', label: 'Flagged' },
] as const

const STATUS_CHIP: Record<string, string> = {
  active: 'bg-nile-soft text-nile-strong',
  paused: 'bg-muted text-ink-2',
  expired: 'bg-muted text-ink-3',
  flagged: 'bg-terracotta-soft text-terracotta-strong',
}

const TEMPLATE =
  'hotel_id,room_type,price_per_night,breakfast_included,free_cancellation,cancellation_days,valid_from,valid_to\n' +
  '5,Double,1350,true,true,2,2026-11-01,2026-12-31\n'

function dates(o: MyOffer): string {
  if (!o.valid_from && !o.valid_to) return 'Any date'
  return `${o.valid_from ? formatDate(o.valid_from) : '…'} – ${o.valid_to ? formatDate(o.valid_to) : '…'}`
}

/** C4 · Every offer, where it stands, and quick actions. */
export function OffersPage() {
  const offers = useMyOffers()
  const navigate = useNavigate()
  const toast = useToast()
  const pause = usePauseOffer()
  const remove = useDeleteOffer()
  const [tab, setTab] = useState<(typeof TABS)[number]['status']>('active')
  const [query, setQuery] = useState('')
  const [deleting, setDeleting] = useState<MyOffer | null>(null)
  const [importing, setImporting] = useState(false)

  const counts = useMemo(() => {
    const c: Record<string, number> = {}
    for (const o of offers.data ?? []) c[o.status] = (c[o.status] ?? 0) + 1
    return c
  }, [offers.data])

  if (offers.isPending) return <PageLoader />
  if (offers.isError) return <ErrorState title="We couldn’t load your offers" action={<Button onClick={() => offers.refetch()}>Try again</Button>} />

  const q = query.trim().toLowerCase()
  const list = offers.data.filter((o) => o.status === tab && (!q || o.hotel_name.toLowerCase().includes(q)))

  const togglePause = (o: MyOffer) =>
    pause.mutate(
      { id: o.id, pause: o.status === 'active' },
      { onSuccess: (r) => toast(r.status === 'paused' ? 'Offer paused' : 'Offer is live again'), onError: (e) => toast(e.message, 'error') },
    )

  const actions = (o: MyOffer) => (
    <Menu
      label={`Options for ${o.hotel_name}`}
      actions={[
        { label: 'Edit price and details', icon: 'edit', onSelect: () => navigate(`/company/offers/${o.id}/edit`) },
        ...(o.status === 'active' || o.status === 'paused'
          ? [{ label: o.status === 'active' ? 'Pause' : 'Make live again', icon: o.status === 'active' ? ('clock' as const) : ('zap' as const), onSelect: () => togglePause(o) }]
          : []),
        { label: 'Delete', icon: 'x', danger: true, onSelect: () => setDeleting(o) },
      ]}
    />
  )

  return (
    <>
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <h1 className="font-display text-[32px] leading-tight sm:text-[38px]">My offers</h1>
          <p className="mt-1.5 text-[15px] text-ink-2">
            {counts.active ?? 0} live · {counts.paused ?? 0} paused · {counts.expired ?? 0} expired
          </p>
        </div>
        <div className="flex flex-wrap gap-3">
          <Button variant="outline" leadingIcon="upload" onClick={() => setImporting(true)}>
            Import CSV
          </Button>
          <ButtonLink to="/company/offers/new" leadingIcon="plus">
            Add offer
          </ButtonLink>
        </div>
      </div>

      <div className="mt-7 flex flex-wrap items-center gap-2.5">
        {TABS.filter((t) => t.status !== 'flagged' || counts.flagged).map((t) => (
          <button
            key={t.status}
            type="button"
            aria-pressed={tab === t.status}
            onClick={() => setTab(t.status)}
            className={`rounded-full border-[1.5px] px-4 py-2 text-[15px] font-semibold ${
              tab === t.status ? 'border-nile bg-nile text-white' : 'border-line-strong bg-card text-ink'
            }`}
          >
            {t.label} · {counts[t.status] ?? 0}
          </button>
        ))}
        <label className="ml-auto flex h-11 w-full items-center gap-2 rounded-xl border-[1.5px] border-line bg-card px-3 sm:w-64">
          <Icon name="search" size={18} className="text-ink-3" />
          <span className="sr-only">Search hotels</span>
          <input value={query} onChange={(e) => setQuery(e.target.value)} placeholder="Search hotels" className="min-w-0 flex-1 bg-transparent text-[15px] outline-none" />
        </label>
      </div>

      {list.length === 0 ? (
        <p className="mt-6 rounded-[20px] border border-dashed border-line-strong bg-raised px-5 py-12 text-center text-[15px] text-ink-3">
          {q ? 'No offer matches that hotel.' : 'Nothing here.'}
        </p>
      ) : (
        <>
          {/* table on wide screens */}
          <div className="mt-6 hidden overflow-hidden rounded-[20px] border border-line bg-card md:block">
            <table className="w-full text-left text-[15px]">
              <thead className="bg-raised text-[12px] font-bold tracking-[0.06em] text-ink-3 uppercase">
                <tr>
                  {['Hotel', 'Room', 'Dates', 'Your price', 'Lowest', 'Position', 'Status', ''].map((h) => (
                    <th key={h} className="px-4 py-3 font-bold">
                      {h}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {list.map((o) => (
                  <tr key={o.id} className="border-t border-line">
                    <td className="px-4 py-3.5">
                      <p className="font-bold">{o.hotel_name}</p>
                      <p className="text-[13px] text-ink-3">{o.city_name}</p>
                      {o.flag_reason && <p className="mt-0.5 text-[13px] text-terracotta">{o.flag_reason}</p>}
                    </td>
                    <td className="px-4 py-3.5">{o.room_type}</td>
                    <td className="px-4 py-3.5 whitespace-nowrap text-ink-2">{dates(o)}</td>
                    <td className="px-4 py-3.5 font-bold whitespace-nowrap">{formatEgp(o.price_per_night)}</td>
                    <td className="px-4 py-3.5 whitespace-nowrap text-ink-2">{o.lowest_price ? formatEgp(o.lowest_price) : '—'}</td>
                    <td className="px-4 py-3.5">
                      <PositionChip offer={o} />
                    </td>
                    <td className="px-4 py-3.5">
                      <span className={`rounded-full px-2.5 py-1 text-[13px] font-semibold capitalize ${STATUS_CHIP[o.status]}`}>
                        {o.status === 'active' ? 'Live' : o.status}
                      </span>
                    </td>
                    <td className="px-2 py-3.5">{actions(o)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          {/* cards on phones */}
          <ul className="mt-5 flex flex-col gap-3 md:hidden">
            {list.map((o) => (
              <li key={o.id} className="rounded-[18px] border border-line bg-card p-4">
                <div className="flex items-start justify-between gap-2">
                  <div>
                    <p className="font-bold">{o.hotel_name}</p>
                    <p className="text-sm text-ink-3">
                      {o.city_name} · {o.room_type} · {dates(o)}
                    </p>
                  </div>
                  {actions(o)}
                </div>
                <div className="mt-3 flex items-center justify-between gap-3">
                  <p className="text-[15px]">
                    <strong>{formatEgp(o.price_per_night)}</strong>
                    {o.lowest_price && o.position !== 1 ? <span className="text-ink-3"> · lowest {formatEgp(o.lowest_price)}</span> : null}
                  </p>
                  <PositionChip offer={o} />
                </div>
              </li>
            ))}
          </ul>
        </>
      )}

      <p className="mt-5 flex gap-2.5 rounded-2xl bg-nile-soft px-4 py-3 text-sm text-nile-strong">
        <Icon name="spark" size={16} className="mt-0.5" />
        Position compares your nightly price with every other company offering the same hotel and room type.
      </p>

      <ConfirmDialog
        open={deleting !== null}
        onClose={() => setDeleting(null)}
        title="Delete this offer?"
        confirmLabel="Delete offer"
        busy={remove.isPending}
        onConfirm={() =>
          deleting &&
          remove.mutate(deleting.id, {
            onSuccess: () => {
              toast('Offer deleted')
              setDeleting(null)
            },
            onError: (e) => toast(e.message, 'error'),
          })
        }
      >
        {deleting?.hotel_name} · {deleting?.room_type} will disappear for travelers. Trips that already picked it keep their night.
        To hide it for a while instead, pause it.
      </ConfirmDialog>
      <ImportDialog open={importing} onClose={() => setImporting(false)} />
    </>
  )
}

function ImportDialog({ open, onClose }: { open: boolean; onClose: () => void }) {
  const imp = useImportOffers()
  const toast = useToast()
  const input = useRef<HTMLInputElement>(null)
  return (
    <Dialog open={open} onClose={onClose} title="Import offers from a CSV" description="A row for a hotel and room type you already sell updates that offer; other rows create new ones.">
      <ol className="space-y-2 text-[15px] text-ink-2">
        <li>1. Download the template and fill one row per hotel and room type.</li>
        <li>2. Hotel ids are shown when you add an offer by hand.</li>
        <li>3. Upload it. If any row is wrong, nothing is saved and we list every problem.</li>
      </ol>
      {imp.isError && <p className="mt-4 rounded-xl bg-terracotta-soft px-4 py-3 text-sm whitespace-pre-line text-terracotta-strong">{imp.error.message}</p>}
      {imp.isSuccess && (
        <p className="mt-4 rounded-xl bg-nile-soft px-4 py-3 text-sm text-nile-strong">
          Done: {imp.data.created} created, {imp.data.updated} updated.
        </p>
      )}
      <div className="mt-5 flex flex-wrap justify-end gap-3">
        <Button variant="outline" leadingIcon="download" onClick={() => downloadFile('egyptora-offers-template.csv', TEMPLATE, 'text/csv')}>
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
          data-testid="csv-input"
          onChange={(e) => {
            const f = e.target.files?.[0]
            if (f) imp.mutate(f, { onSuccess: (r) => toast(`${r.created + r.updated} offers imported`) })
            e.target.value = ''
          }}
        />
      </div>
    </Dialog>
  )
}
