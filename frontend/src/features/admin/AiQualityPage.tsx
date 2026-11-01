import { useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import {
  useAddToTraining,
  useAdminPlaces,
  useDeleteExample,
  useFixQuery,
  useLabelScan,
  useMetrics,
  useQueries,
  useScanQueue,
  useTrainingExamples,
  type AdminScan,
  type Metrics,
  type NLQuery,
} from '@/api/admin'
import { Button } from '@/components/ui/Button'
import { Icon, type IconName } from '@/components/ui/Icon'
import { PageLoader } from '@/components/ui/Spinner'
import { useToast } from '@/components/ui/Toast'
import { formatDate, plural } from '@/lib/format'
import { pct } from './overview'
import { card, rowClass } from './styles'
import { AdminHeader, Tabs } from './ui'

type Tab = 'search' | 'chat' | 'scans' | 'training'

const QUERY_CHIP: Record<string, string> = {
  failed: 'bg-terracotta-soft text-terracotta-strong',
  flagged: 'bg-gold-soft text-warning',
  ok: 'bg-nile-soft text-nile-strong',
}
const QUERY_LABEL: Record<string, string> = { failed: 'Failed', flagged: 'No results', ok: 'Worked' }

/** A5 · Review what the models got wrong and turn fixes into training examples. */
export function AiQualityPage() {
  const [params, setParams] = useSearchParams()
  const tab = (params.get('tab') as Tab | null) ?? 'search'
  const metrics = useMetrics()
  const m = metrics.data

  const pills: { tab: Tab; icon: IconName; text: string }[] = [
    { tab: 'search', icon: 'search', text: m ? `Hotel search · ${pct(m.search.success_rate)} worked · ${m.search.failed} failed` : 'Hotel search' },
    { tab: 'chat', icon: 'chat', text: m ? `Chat edits · ${pct(m.chat.keep_rate)} kept` : 'Chat edits' },
    { tab: 'scans', icon: 'camera', text: m ? `Monument scans · ${m.scans.waiting_review} to review` : 'Monument scans' },
    { tab: 'training', icon: 'code', text: m ? `Training · ${m.training.nl2sql_examples} examples` : 'Training' },
  ]

  return (
    <>
      <AdminHeader title="AI quality" subtitle="Review what the models got wrong, and turn fixes into training examples." />
      <div role="tablist" className="mt-6 flex flex-wrap gap-2">
        {pills.map((p) => (
          <button
            key={p.tab}
            type="button"
            role="tab"
            aria-selected={tab === p.tab}
            onClick={() => setParams(p.tab === 'search' ? {} : { tab: p.tab }, { replace: true })}
            className={`inline-flex items-center gap-2 rounded-full border-[1.5px] px-4 py-2 text-[15px] font-semibold ${
              tab === p.tab ? 'border-nile bg-nile text-white' : 'border-line-strong bg-card text-ink'
            }`}
          >
            <Icon name={p.icon} size={16} />
            {p.text}
          </button>
        ))}
      </div>
      <div className="mt-5">
        {tab === 'search' && <SearchReview />}
        {tab === 'chat' && m && <ChatMetrics metrics={m} />}
        {tab === 'scans' && <ScanQueue threshold={m?.scans.threshold} />}
        {tab === 'training' && <Training />}
      </div>
    </>
  )
}

function SearchReview() {
  const [status, setStatus] = useState<'failed' | 'flagged' | 'ok' | 'all'>('failed')
  const queries = useQueries(status)
  const [selectedId, setSelectedId] = useState<number | null>(null)
  const list = queries.data?.data ?? []
  const selected = list.find((q) => q.id === selectedId) ?? list[0]

  return (
    <div className="grid gap-5 lg:grid-cols-[minmax(0,1fr)_480px]">
      <div className="min-w-0">
        <Tabs
          value={status}
          onChange={(s) => (setStatus(s), setSelectedId(null))}
          items={[
            { value: 'failed', label: 'Failed' },
            { value: 'flagged', label: 'No results' },
            { value: 'ok', label: 'Worked' },
            { value: 'all', label: 'All' },
          ]}
        />
        <div className={`${card} mt-4 overflow-hidden`}>
          {queries.isPending ? (
            <PageLoader />
          ) : list.length === 0 ? (
            <p className="px-5 py-10 text-center text-[15px] text-ink-3">Nothing here. Searches will show up as travelers use them.</p>
          ) : (
            <ul>
              {list.map((q) => (
                <li key={q.id}>
                  <button type="button" onClick={() => setSelectedId(q.id)} className={rowClass(selected?.id === q.id)}>
                    <span className="flex flex-wrap items-center gap-2 text-[13px]">
                      <span className={`rounded-full px-2.5 py-0.5 font-semibold ${QUERY_CHIP[q.status] ?? QUERY_CHIP.flagged}`}>{QUERY_LABEL[q.status] ?? q.status}</span>
                      {q.fixed_sql && <span className="rounded-full bg-muted px-2.5 py-0.5 font-semibold text-ink-2">Fixed</span>}
                      {q.in_training && <span className="rounded-full bg-nile-soft px-2.5 py-0.5 font-semibold text-nile-strong">In training</span>}
                      <span className="text-ink-3">{formatDate(q.created_at.slice(0, 10))}</span>
                    </span>
                    <span className="mt-1.5 block font-semibold">“{q.question}”</span>
                  </button>
                </li>
              ))}
            </ul>
          )}
        </div>
      </div>
      {selected && <QueryPanel key={selected.id} query={selected} />}
    </div>
  )
}

function Code({ children }: { children: string }) {
  return <pre className="overflow-x-auto rounded-2xl bg-inverse p-4 font-mono text-[13px] leading-relaxed whitespace-pre-wrap text-on-dark">{children}</pre>
}

function QueryPanel({ query }: { query: NLQuery }) {
  const fix = useFixQuery()
  const train = useAddToTraining()
  const toast = useToast()
  const [sql, setSql] = useState(query.fixed_sql ?? query.generated_sql ?? 'SELECT hotel_id FROM hotel_best_price WHERE ')

  return (
    <section className={`${card} p-5 sm:p-6 lg:sticky lg:top-6`}>
      <div className="flex items-baseline justify-between gap-3">
        <h2 className="text-lg font-bold">Hotel search · {QUERY_LABEL[query.status]?.toLowerCase() ?? query.status}</h2>
        <p className="text-sm text-ink-3">
          {formatDate(query.created_at.slice(0, 10))}
          {query.latency_ms ? ` · ${query.latency_ms} ms` : ''}
        </p>
      </div>
      <p className="mt-4 text-[12px] font-bold tracking-[0.08em] text-ink-3">TRAVELER ASKED</p>
      <p className="mt-2 rounded-2xl bg-raised px-4 py-3 text-[15px] font-semibold">“{query.question}”</p>
      {query.generated_sql && (
        <>
          <p className="mt-4 text-[12px] font-bold tracking-[0.08em] text-ink-3">GENERATED SQL</p>
          <div className="mt-2">
            <Code>{query.generated_sql}</Code>
          </div>
        </>
      )}
      {query.error && (
        <p className="mt-3 flex items-start gap-2 text-[13px] text-terracotta-strong">
          <Icon name="alert" size={15} className="mt-0.5" /> <span className="font-mono">{query.error}</span>
        </p>
      )}
      {query.status !== 'ok' && query.result_count !== null && query.result_count !== undefined && (
        <p className="mt-2 text-sm text-ink-3">{plural(query.result_count, 'hotel')} returned</p>
      )}

      <p className="mt-5 text-[12px] font-bold tracking-[0.08em] text-ink-3">YOUR FIX</p>
      <label htmlFor="fix-sql" className="sr-only">
        Fixed SQL
      </label>
      <textarea
        id="fix-sql"
        value={sql}
        onChange={(e) => setSql(e.target.value)}
        rows={6}
        spellCheck={false}
        className="mt-2 w-full rounded-2xl border-[1.5px] border-line-strong bg-inverse p-4 font-mono text-[13px] leading-relaxed text-on-dark outline-none focus:border-terracotta"
      />
      <p className="mt-1.5 text-[13px] text-ink-3">Only SELECT on hotel_best_price and offers, and it must return hotel_id. It runs read-only.</p>
      {fix.data && (
        <p className="mt-3 flex flex-wrap items-center gap-2 text-sm">
          <span className="inline-flex items-center gap-1 rounded-full bg-nile-soft px-2.5 py-1 font-semibold text-nile-strong">
            <Icon name="check" size={14} /> Returns {plural(fix.data.result_count, 'hotel')}
          </span>
          <span className="text-ink-2">{fix.data.preview.map((h) => h.hotel_name).slice(0, 3).join(', ')}</span>
        </p>
      )}
      <div className="mt-5 flex flex-wrap gap-3">
        <Button
          variant="outline"
          leadingIcon="code"
          loading={fix.isPending}
          disabled={!sql.trim()}
          onClick={() => fix.mutate({ id: query.id, sql: sql.trim() }, { onSuccess: () => toast('Fix saved and tested'), onError: (e) => toast(e.message, 'error') })}
        >
          Test & save fix
        </Button>
        <Button
          leadingIcon="check"
          loading={train.isPending}
          disabled={query.in_training || !(query.fixed_sql || fix.data)}
          onClick={() => train.mutate(query.id, { onSuccess: () => toast('Added to training examples'), onError: (e) => toast(e.message, 'error') })}
        >
          {query.in_training ? 'In training' : 'Add to training'}
        </Button>
      </div>
      <p className="mt-3 text-[13px] text-ink-3">Once fixed, the same question uses your SQL right away.</p>
    </section>
  )
}

function ChatMetrics({ metrics }: { metrics: Metrics }) {
  const c = metrics.chat
  const tiles = [
    ['Messages', c.messages],
    ['Changes proposed', c.changes_proposed],
    ['Kept', c.kept],
    ['Undone', c.undone],
    ['Keep rate', pct(c.keep_rate)],
  ]
  return (
    <div className={`${card} p-5 sm:p-6`}>
      <dl className="grid grid-cols-2 gap-4 sm:grid-cols-5">
        {tiles.map(([k, v]) => (
          <div key={k}>
            <dt className="text-sm text-ink-2">{k}</dt>
            <dd className="mt-1 font-display text-[30px] leading-none">{v}</dd>
          </div>
        ))}
      </dl>
      <p className="mt-5 text-sm text-ink-3">
        A change the traveler keeps means the agent understood them. A low keep rate points to requests the agent misreads — read those
        trips’ chats to find the pattern.
      </p>
    </div>
  )
}

function ScanQueue({ threshold }: { threshold?: number }) {
  const [onlyUnlabeled, setOnlyUnlabeled] = useState(true)
  const scans = useScanQueue(onlyUnlabeled)
  const list = scans.data?.data ?? []
  return (
    <div>
      <div className="flex flex-wrap items-center justify-between gap-3">
        <p className="text-[15px] text-ink-2">
          Photos the recognizer was less than {threshold ? `${Math.round(threshold * 100)}%` : ''} sure about. Labeling one teaches the next model.
        </p>
        <label className="flex items-center gap-2 text-sm font-semibold">
          <input type="checkbox" className="size-4 accent-[#2e6a58]" checked={onlyUnlabeled} onChange={(e) => setOnlyUnlabeled(e.target.checked)} />
          Only unlabeled
        </label>
      </div>
      {scans.isPending ? (
        <PageLoader />
      ) : list.length === 0 ? (
        <p className={`${card} mt-4 px-5 py-10 text-center text-[15px] text-ink-3`}>No scans waiting.</p>
      ) : (
        <ul className="mt-4 grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
          {list.map((s) => (
            <ScanCard key={s.id} scan={s} />
          ))}
        </ul>
      )}
    </div>
  )
}

function ScanCard({ scan }: { scan: AdminScan }) {
  const places = useAdminPlaces({ search: '' })
  const label = useLabelScan()
  const toast = useToast()
  const [placeId, setPlaceId] = useState<number | ''>(scan.place_id ?? '')
  const [train, setTrain] = useState(true)
  return (
    <li className={`${card} overflow-hidden`}>
      <img src={scan.image_url} alt="Traveler’s photo" className="aspect-[4/3] w-full bg-placeholder object-cover" />
      <div className="p-4">
        <p className="text-sm text-ink-2">
          Guess: <strong>{scan.place_name ?? 'nothing'}</strong>
          {scan.confidence !== null && scan.confidence !== undefined ? ` · ${Math.round(scan.confidence * 100)}%` : ''}
        </p>
        <p className="text-[13px] text-ink-3">{formatDate(scan.created_at.slice(0, 10), true)}{scan.labeled ? ' · labeled' : ''}</p>
        <label className="mt-3 block text-sm font-semibold text-ink-2">
          It shows
          <select
            value={placeId}
            onChange={(e) => setPlaceId(e.target.value ? Number(e.target.value) : '')}
            className="mt-1.5 h-11 w-full rounded-xl border-[1.5px] border-line-strong bg-card px-3 text-[15px] font-normal text-ink"
          >
            <option value="">Choose a place…</option>
            {(places.data?.data ?? []).map((p) => (
              <option key={p.id} value={p.id}>
                {p.name}
              </option>
            ))}
          </select>
        </label>
        <label className="mt-2.5 flex items-center gap-2 text-sm">
          <input type="checkbox" className="size-4 accent-[#2e6a58]" checked={train} onChange={(e) => setTrain(e.target.checked)} />
          Use this photo for training
        </label>
        <Button
          size="sm"
          className="mt-3 w-full"
          loading={label.isPending}
          disabled={placeId === ''}
          onClick={() =>
            placeId !== '' &&
            label.mutate({ id: scan.id, placeId, train }, { onSuccess: () => toast('Scan labeled'), onError: (e) => toast(e.message, 'error') })
          }
        >
          Save label
        </Button>
      </div>
    </li>
  )
}

function Training() {
  const examples = useTrainingExamples()
  const remove = useDeleteExample()
  const toast = useToast()
  if (examples.isPending) return <PageLoader />
  const list = examples.data ?? []
  return (
    <div className={`${card} p-5 sm:p-6`}>
      <p className="text-[15px] text-ink-2">Question → SQL pairs the search model learns from. Fixed searches you add show up here.</p>
      {list.length === 0 ? (
        <p className="mt-4 text-ink-3">No examples yet.</p>
      ) : (
        <ul className="mt-3">
          {list.map((ex) => (
            <li key={ex.id} className="border-t border-line py-4 first:border-t-0">
              <div className="flex items-start justify-between gap-3">
                <p className="font-semibold">“{ex.question}”</p>
                <Button size="sm" variant="ghost" onClick={() => remove.mutate(ex.id, { onSuccess: () => toast('Example removed'), onError: (e) => toast(e.message, 'error') })}>
                  Remove
                </Button>
              </div>
              <div className="mt-2">
                <Code>{ex.sql}</Code>
              </div>
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}
