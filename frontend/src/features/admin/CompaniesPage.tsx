import { useState } from 'react'
import { useAdminCompanies, useAnalyzeReviews, useApproveCompany, useRejectCompany, useSuspendCompany, type AdminCompany } from '@/api/admin'
import { Button } from '@/components/ui/Button'
import { Dialog } from '@/components/ui/Dialog'
import { ErrorState } from '@/components/ui/ErrorState'
import { TextArea } from '@/components/ui/fields'
import { Icon } from '@/components/ui/Icon'
import { PageLoader } from '@/components/ui/Spinner'
import { TextField } from '@/components/ui/TextField'
import { useToast } from '@/components/ui/Toast'
import { formatDate, plural } from '@/lib/format'
import { ConfirmDialog } from '../trips/edit/ConfirmDialog'
import { card, rowClass } from './styles'
import { AdminHeader, Tabs } from './ui'

type Status = 'pending' | 'approved' | 'rejected' | 'suspended'

const CHIP: Record<string, string> = {
  pending: 'bg-gold-soft text-warning',
  approved: 'bg-nile-soft text-nile-strong',
  rejected: 'bg-terracotta-soft text-terracotta-strong',
  suspended: 'bg-terracotta-soft text-terracotta-strong',
}

/** A2 · Approve new partners and keep an eye on trust. */
export function CompaniesPage() {
  const [status, setStatus] = useState<Status>('pending')
  const [query, setQuery] = useState('')
  const [selectedId, setSelectedId] = useState<number | null>(null)
  const list = useAdminCompanies(status)

  const q = query.trim().toLowerCase()
  const rows = (list.data?.data ?? []).filter((c) => !q || c.name.toLowerCase().includes(q) || c.owner_email.toLowerCase().includes(q))
  const selected = rows.find((c) => c.id === selectedId) ?? rows[0]

  return (
    <>
      <AdminHeader title="Companies" subtitle="Approve new partners and keep an eye on trust scores." />
      <div className="mt-7 grid gap-5 lg:grid-cols-[minmax(0,1fr)_420px]">
        <div className="min-w-0">
          <div className={card}>
            <div className="flex flex-wrap items-center gap-3 border-b border-line p-4">
              <Tabs<Status>
                value={status}
                onChange={(s) => {
                  setStatus(s)
                  setSelectedId(null)
                }}
                items={[
                  { value: 'pending', label: 'Pending' },
                  { value: 'approved', label: 'Approved' },
                  { value: 'rejected', label: 'Rejected' },
                  { value: 'suspended', label: 'Suspended' },
                ]}
              />
              <label className="ml-auto flex h-10 w-full items-center gap-2 rounded-xl border-[1.5px] border-line bg-card px-3 sm:w-56">
                <Icon name="search" size={16} className="text-ink-3" />
                <span className="sr-only">Search companies</span>
                <input value={query} onChange={(e) => setQuery(e.target.value)} placeholder="Search companies" className="min-w-0 flex-1 bg-transparent text-sm outline-none" />
              </label>
            </div>
            {list.isPending ? (
              <PageLoader />
            ) : list.isError ? (
              <ErrorState title="We couldn’t load companies" action={<Button onClick={() => list.refetch()}>Try again</Button>} />
            ) : rows.length === 0 ? (
              <p className="px-5 py-10 text-center text-[15px] text-ink-3">No {status} companies.</p>
            ) : (
              <ul>
                {rows.map((c) => (
                  <li key={c.id}>
                    <button type="button" onClick={() => setSelectedId(c.id)} className={`${rowClass(selected?.id === c.id)} grid grid-cols-[1fr_auto] gap-2 sm:grid-cols-[1fr_110px_90px_110px]`}>
                      <span className="min-w-0">
                        <span className="block truncate font-bold">{c.name}</span>
                        <span className="block truncate text-[13px] text-ink-3">{c.owner_email}</span>
                      </span>
                      <span className="hidden self-center sm:block">
                        <span className={`rounded-full px-2.5 py-1 text-[13px] font-semibold ${c.license_doc_url ? 'bg-nile-soft text-nile-strong' : 'bg-terracotta-soft text-terracotta-strong'}`}>
                          {c.license_doc_url ? 'License' : 'Missing'}
                        </span>
                      </span>
                      <span className="hidden self-center text-sm sm:block">{c.trust_score ? `★ ${c.trust_score.toFixed(1)}` : c.google_rating ? `G ${c.google_rating}` : '—'}</span>
                      <span className="self-center text-right text-sm text-ink-2">{formatDate(c.created_at.slice(0, 10))}</span>
                    </button>
                  </li>
                ))}
              </ul>
            )}
          </div>
          <p className="mt-4 flex gap-2.5 rounded-2xl bg-muted px-4 py-3 text-sm text-ink-2">
            <Icon name="shield" size={16} className="mt-0.5 text-nile" />
            Companies can publish offers only after approval. Their trust score starts from this review and shifts to traveler ratings over time.
          </p>
        </div>
        {selected && <CompanyPanel key={selected.id} company={selected} />}
      </div>
    </>
  )
}

function CompanyPanel({ company }: { company: AdminCompany }) {
  const toast = useToast()
  const approve = useApproveCompany()
  const reject = useRejectCompany()
  const suspend = useSuspendCompany()
  const analyze = useAnalyzeReviews()
  const [license, setLicense] = useState(false)
  const [google, setGoogle] = useState(company.google_rating ? String(company.google_rating) : '')
  const [years, setYears] = useState(company.years_active ? String(company.years_active) : '')
  const [social, setSocial] = useState(2)
  const [reviews, setReviews] = useState('')
  const [rejecting, setRejecting] = useState(false)
  const [reason, setReason] = useState('')
  const [suspending, setSuspending] = useState(false)

  const canApprove = company.status === 'pending' || company.status === 'suspended'
  const googleNum = google ? Number(google) : null
  const badGoogle = googleNum !== null && (Number.isNaN(googleNum) || googleNum < 0 || googleNum > 5)
  const links = [
    ['License', company.license_doc_url],
    ['Website', company.website],
    ['Facebook', company.facebook_url],
    ['Instagram', company.instagram_url],
  ].filter(([, u]) => u) as [string, string][]

  return (
    <section className={`${card} flex flex-col p-5 sm:p-6 lg:sticky lg:top-6 lg:max-h-[calc(100dvh-48px)] lg:overflow-y-auto`}>
      <div className="flex flex-wrap items-center gap-2">
        <h2 className="font-display text-[26px] leading-tight">{company.name}</h2>
        <span className={`rounded-full px-2.5 py-0.5 text-[13px] font-semibold capitalize ${CHIP[company.status]}`}>{company.status}</span>
      </div>
      <p className="mt-1 text-sm text-ink-2">
        {company.owner_name} · {company.owner_email} · applied {formatDate(company.created_at.slice(0, 10), true)}
      </p>
      <p className="mt-1 text-sm text-ink-3">License no. {company.license_no ?? '—'}{company.phone ? ` · ${company.phone}` : ''}</p>
      {links.length > 0 && (
        <p className="mt-3 flex flex-wrap gap-4 text-sm">
          {links.map(([label, url]) => (
            <a key={label} href={url} target="_blank" rel="noreferrer" className="inline-flex items-center gap-1 font-semibold text-terracotta hover:underline">
              <Icon name="link" size={14} /> {label}
            </a>
          ))}
        </p>
      )}
      {company.reject_reason && <p className="mt-3 rounded-xl bg-terracotta-soft px-3.5 py-2.5 text-sm text-terracotta-strong">Last reason: {company.reject_reason}</p>}

      {company.status === 'approved' ? (
        <dl className="mt-5 grid grid-cols-2 gap-3">
          {[
            ['Trust score', company.trust_score?.toFixed(1) ?? '—'],
            ['Initial score', company.initial_score?.toFixed(1) ?? '—'],
            ['Live offers', String(company.active_offers)],
            ['Reviews', String(company.reviews_count)],
          ].map(([k, v]) => (
            <div key={k} className="rounded-2xl bg-raised px-4 py-3">
              <dt className="text-[13px] text-ink-3">{k}</dt>
              <dd className="font-display text-2xl">{v}</dd>
            </div>
          ))}
        </dl>
      ) : (
        <>
          <p className="mt-5 text-[12px] font-bold tracking-[0.08em] text-ink-3">TRUST CHECKLIST</p>
          <label className="mt-2 flex items-center gap-3 text-[15px]">
            <input type="checkbox" className="size-4 accent-[#2e6a58]" checked={license} onChange={(e) => setLicense(e.target.checked)} />
            Tourism license checked and valid
          </label>
          <div className="mt-3 grid grid-cols-2 gap-3">
            <TextField label="Google rating" inputMode="decimal" placeholder="4.5" value={google} onChange={(e) => setGoogle(e.target.value)} error={badGoogle ? '0 to 5' : undefined} />
            <TextField label="Years in business" inputMode="numeric" value={years} onChange={(e) => setYears(e.target.value.replace(/\D/g, ''))} />
          </div>
          <label className="mt-4 block text-[15px] font-semibold text-ink-2">
            Social pages: {social} / 5
            <input type="range" min={0} max={5} step={1} value={social} onChange={(e) => setSocial(Number(e.target.value))} className="mt-2 w-full accent-[#2e6a58]" />
          </label>

          <p className="mt-5 text-[12px] font-bold tracking-[0.08em] text-ink-3">REVIEW ANALYSIS (AI)</p>
          <div className="mt-2">
            <TextArea label="Paste reviews from Google or Facebook, one per line" rows={4} value={reviews} onChange={(e) => setReviews(e.target.value)} />
          </div>
          <Button
            size="sm"
            variant="outline"
            leadingIcon="spark"
            className="mt-2 self-start"
            loading={analyze.isPending}
            disabled={!reviews.trim()}
            onClick={() =>
              analyze.mutate(
                { id: company.id, reviews: reviews.split('\n').map((r) => r.trim()).filter(Boolean) },
                { onError: (e) => toast(e.message, 'error') },
              )
            }
          >
            Analyze reviews
          </Button>
          {analyze.data && (
            <div className="mt-3 rounded-2xl bg-raised p-4 text-sm">
              <p>
                <span className="rounded-full bg-nile-soft px-2.5 py-0.5 font-semibold text-nile-strong">{Math.round(analyze.data.positive_share * 100)}% positive</span>
                {analyze.data.top_complaints.length > 0 && <span className="ml-2 text-ink-2">Complaints: {analyze.data.top_complaints.join(' · ')}</span>}
              </p>
              <button type="button" onClick={() => setSocial(analyze.data!.suggested_social_presence)} className="mt-2 font-bold text-terracotta">
                Use suggested social score ({analyze.data.suggested_social_presence} / 5)
              </button>
            </div>
          )}
        </>
      )}

      <div className="mt-6 flex flex-wrap gap-2.5 border-t border-line pt-5">
        {canApprove && (
          <button
            type="button"
            disabled={!license || badGoogle || approve.isPending}
            onClick={() =>
              approve.mutate(
                { id: company.id, body: { license_verified: license, google_rating: googleNum, years_active: years ? Number(years) : null, social_presence: social } },
                {
                  onSuccess: (r) => toast(`${company.name} approved · starting trust ${r.initial_score.toFixed(1)}`),
                  onError: (e) => toast(e.message, 'error'),
                },
              )
            }
            className="inline-flex items-center gap-2 rounded-xl bg-nile px-5 py-3 text-[15px] font-bold text-white hover:bg-nile-strong disabled:opacity-50"
          >
            <Icon name="check" size={18} /> Approve
          </button>
        )}
        {company.status === 'pending' && (
          <Button variant="outline" onClick={() => setRejecting(true)}>
            Reject
          </Button>
        )}
        {company.status === 'approved' && (
          <Button variant="outline" onClick={() => setSuspending(true)}>
            Suspend
          </Button>
        )}
      </div>
      {canApprove && !license && <p className="mt-2 text-[13px] text-ink-3">Tick the license check to approve.</p>}

      <Dialog open={rejecting} onClose={() => setRejecting(false)} title={`Reject ${company.name}?`} description="The company sees this reason and can upload a new license.">
        <TextArea label="Reason" value={reason} onChange={(e) => setReason(e.target.value)} placeholder="e.g. The license photo is unreadable" />
        <div className="mt-4 flex justify-end gap-3">
          <Button variant="outline" onClick={() => setRejecting(false)}>
            Cancel
          </Button>
          <Button
            loading={reject.isPending}
            disabled={reason.trim().length < 5}
            onClick={() =>
              reject.mutate(
                { id: company.id, reason: reason.trim() },
                { onSuccess: () => (toast(`${company.name} rejected`), setRejecting(false)), onError: (e) => toast(e.message, 'error') },
              )
            }
          >
            Reject
          </Button>
        </div>
      </Dialog>
      <ConfirmDialog
        open={suspending}
        onClose={() => setSuspending(false)}
        title={`Suspend ${company.name}?`}
        confirmLabel="Suspend"
        busy={suspend.isPending}
        onConfirm={() =>
          suspend.mutate(company.id, {
            onSuccess: (r) => (toast(`Suspended · ${plural(r.paused_offers, 'offer')} paused`), setSuspending(false)),
            onError: (e) => toast(e.message, 'error'),
          })
        }
      >
        All its live offers are paused and travelers stop seeing them. You can approve it again later.
      </ConfirmDialog>
    </section>
  )
}
