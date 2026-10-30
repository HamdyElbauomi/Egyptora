import { useState, type FormEvent } from 'react'
import { useInsights, useMyReviews, useUpdateCompany, type Company } from '@/api/company'
import { Button, ButtonLink } from '@/components/ui/Button'
import { Dialog } from '@/components/ui/Dialog'
import { Icon } from '@/components/ui/Icon'
import { PageLoader } from '@/components/ui/Spinner'
import { TextField } from '@/components/ui/TextField'
import { useToast } from '@/components/ui/Toast'
import { formatDate, initials, plural } from '@/lib/format'
import { ReviewList } from '../companies/ReviewList'
import { useCurrentCompany } from './useCompanyContext'

/** Weight of the initial score, in "reviews", in the trust formula (backend trust.py). */
const INITIAL_WEIGHT = 10

/** C6 · What travelers see, and how the trust score is built. */
export function ProfilePage() {
  const company = useCurrentCompany()
  const insights = useInsights()
  const [page, setPage] = useState(1)
  const reviews = useMyReviews(page)
  const [editing, setEditing] = useState(false)

  const links = [
    ['Website', company.website],
    ['Facebook', company.facebook_url],
    ['Instagram', company.instagram_url],
  ].filter(([, url]) => url) as [string, string][]

  return (
    <>
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <h1 className="font-display text-[32px] leading-tight sm:text-[38px]">Company profile</h1>
          <p className="mt-1.5 text-[15px] text-ink-2">What travelers see about you, and how your trust score is built.</p>
        </div>
        <div className="flex flex-wrap gap-3">
          {company.status === 'approved' && (
            <ButtonLink to={`/companies/${company.id}`} variant="outline" leadingIcon="eye">
              Preview as traveler
            </ButtonLink>
          )}
          <Button leadingIcon="edit" onClick={() => setEditing(true)}>
            Edit profile
          </Button>
        </div>
      </div>

      <div className="mt-7 grid gap-5 lg:grid-cols-[minmax(0,1fr)_380px]">
        <div className="flex flex-col gap-5">
          <section className="rounded-[20px] border border-line bg-card p-6">
            <div className="flex items-center gap-4">
              <span className="grid size-16 shrink-0 place-items-center rounded-2xl bg-nile font-display text-2xl text-white">{initials(company.name)}</span>
              <div>
                <h2 className="font-display text-[26px] leading-tight">{company.name}</h2>
                <p className="mt-1 flex flex-wrap items-center gap-2 text-sm text-ink-2">
                  {company.approved_at ? `Partner since ${formatDate(company.approved_at.slice(0, 10), true)}` : `Applied ${formatDate(company.created_at.slice(0, 10), true)}`}
                  {company.status === 'approved' && (
                    <span className="inline-flex items-center gap-1 rounded-full bg-nile-soft px-2.5 py-0.5 font-semibold text-nile-strong">
                      <Icon name="check" size={14} /> License verified
                    </span>
                  )}
                </p>
              </div>
            </div>
            <dl className="mt-5 grid gap-x-6 gap-y-2 text-[15px] sm:grid-cols-2">
              {[
                ['License no.', company.license_no],
                ['Phone', company.phone],
                ['Google rating', company.google_rating ? company.google_rating.toFixed(1) : null],
                ['Years in business', company.years_active ? String(company.years_active) : null],
              ].map(([label, value]) => (
                <div key={label} className="flex gap-2">
                  <dt className="text-ink-3">{label}</dt>
                  <dd className="font-semibold">{value ?? '—'}</dd>
                </div>
              ))}
            </dl>
            {links.length > 0 && (
              <div className="mt-4 flex flex-wrap gap-4 text-[15px]">
                {links.map(([label, url]) => (
                  <a key={label} href={url} target="_blank" rel="noreferrer" className="inline-flex items-center gap-1.5 font-semibold text-terracotta hover:underline">
                    <Icon name="link" size={16} /> {label}
                  </a>
                ))}
              </div>
            )}
          </section>

          <section className="rounded-[20px] border border-line bg-card p-6">
            <div className="mb-4 flex items-center justify-between">
              <h2 className="text-lg font-bold">Traveler reviews</h2>
              <span className="rounded-full bg-muted px-3 py-1 text-sm font-semibold">{plural(company.reviews_count, 'review')}</span>
            </div>
            {reviews.isPending ? <PageLoader /> : <ReviewList reviews={reviews.data?.data ?? []} showSentiment />}
            {reviews.data && reviews.data.total > reviews.data.limit && (
              <div className="mt-4 flex gap-3">
                <Button size="sm" variant="outline" disabled={page === 1} onClick={() => setPage((p) => p - 1)}>
                  Newer
                </Button>
                <Button size="sm" variant="outline" disabled={page * reviews.data.limit >= reviews.data.total} onClick={() => setPage((p) => p + 1)}>
                  Older
                </Button>
              </div>
            )}
            {insights.data && insights.data.reviews_count > 0 && (
              <div className="mt-5 rounded-2xl bg-raised p-4">
                <p className="flex items-center gap-2 text-sm font-bold">
                  <Icon name="spark" size={16} className="text-terracotta" /> What travelers mention (AI summary)
                </p>
                <p className="mt-2 text-sm text-ink-2">
                  {insights.data.positive_share !== null && insights.data.positive_share !== undefined
                    ? `${Math.round(insights.data.positive_share * 100)}% of reviews are positive.`
                    : null}
                </p>
                {insights.data.top_complaints.length > 0 && (
                  <div className="mt-2 flex flex-wrap gap-2">
                    {insights.data.top_complaints.map((c) => (
                      <span key={c} className="rounded-full bg-gold-soft px-3 py-1 text-sm font-semibold text-warning">
                        {c}
                      </span>
                    ))}
                  </div>
                )}
              </div>
            )}
          </section>
        </div>

        <div className="flex flex-col gap-5">
          <TrustCard company={company} average={insights.data?.average_rating ?? null} />
          <section className="rounded-[20px] border border-line bg-card p-6">
            <h2 className="text-lg font-bold">How to raise your score</h2>
            <ul className="mt-3 space-y-2.5 text-[15px]">
              {['Reply to travelers within a few hours', 'Keep offer dates and prices up to date', 'Ask happy travelers to leave a review'].map((t) => (
                <li key={t} className="flex gap-2.5">
                  <Icon name="check" size={18} className="text-nile" />
                  {t}
                </li>
              ))}
            </ul>
          </section>
        </div>
      </div>
      <EditProfile company={company} open={editing} onClose={() => setEditing(false)} />
    </>
  )
}

function TrustCard({ company, average }: { company: Company; average: number | null }) {
  const initial = company.initial_score
  const n = company.reviews_count
  const bar = (value: number | null, color: string) => (
    <div className="mt-1.5 h-2 rounded-full bg-track">
      <div className={`h-full rounded-full ${color}`} style={{ width: `${((value ?? 0) / 5) * 100}%` }} />
    </div>
  )
  return (
    <section className="rounded-[20px] border border-line bg-card p-6">
      <h2 className="text-lg font-bold">Trust score</h2>
      <p className="mt-3 font-display text-[56px] leading-none">
        {company.trust_score?.toFixed(1) ?? '—'}
        <span className="font-sans text-lg text-ink-3"> / 5</span>
      </p>
      {initial === null || initial === undefined ? (
        <p className="mt-4 text-sm text-ink-2">Your score is set when the Egyptora team approves your license.</p>
      ) : (
        <>
          <div className="mt-5">
            <p className="flex justify-between text-[15px] font-semibold">
              Initial score <span>{initial.toFixed(1)}</span>
            </p>
            {bar(initial, 'bg-gold')}
            <p className="mt-1.5 text-[13px] text-ink-3">From your license, Google rating and years in business · counts as {INITIAL_WEIGHT} reviews</p>
          </div>
          <div className="mt-4">
            <p className="flex justify-between text-[15px] font-semibold">
              Traveler reviews <span>{average?.toFixed(1) ?? '—'}</span>
            </p>
            {bar(average, 'bg-nile')}
            <p className="mt-1.5 text-[13px] text-ink-3">{plural(n, 'review')} from Egyptora travelers</p>
          </div>
          {average !== null && n > 0 && (
            <p className="mt-4 rounded-xl bg-inverse px-4 py-3 font-mono text-[13px] text-on-dark">
              ({INITIAL_WEIGHT} × {initial.toFixed(1)} + {n} × {average.toFixed(1)}) ÷ {INITIAL_WEIGHT + n} ={' '}
              {((INITIAL_WEIGHT * initial + n * average) / (INITIAL_WEIGHT + n)).toFixed(2)}
            </p>
          )}
          <p className="mt-3 text-[13px] text-ink-3">As more travelers review you, their ratings count for more than the initial score.</p>
        </>
      )}
    </section>
  )
}

function EditProfile({ company, open, onClose }: { company: Company; open: boolean; onClose: () => void }) {
  return (
    <Dialog open={open} onClose={onClose} title="Edit profile" description="Travelers see your website and social pages on your company page.">
      {open && <EditForm company={company} onDone={onClose} />}
    </Dialog>
  )
}

function EditForm({ company, onDone }: { company: Company; onDone: () => void }) {
  const update = useUpdateCompany()
  const toast = useToast()
  const [v, setV] = useState({
    phone: company.phone ?? '',
    website: company.website ?? '',
    facebook_url: company.facebook_url ?? '',
    instagram_url: company.instagram_url ?? '',
  })
  const set = (k: keyof typeof v) => (e: React.ChangeEvent<HTMLInputElement>) => setV((s) => ({ ...s, [k]: e.target.value }))
  const submit = (e: FormEvent) => {
    e.preventDefault()
    const body = Object.fromEntries(Object.entries(v).map(([k, x]) => [k, x.trim() || null]))
    update.mutate(body, {
      onSuccess: () => {
        toast('Profile updated')
        onDone()
      },
      onError: (err) => toast(err.message, 'error'),
    })
  }
  return (
    <form onSubmit={submit} className="flex flex-col gap-4">
      <TextField label="Phone" type="tel" value={v.phone} onChange={set('phone')} />
      <TextField label="Website" type="url" placeholder="https://" value={v.website} onChange={set('website')} />
      <TextField label="Facebook page" type="url" placeholder="https://facebook.com/…" value={v.facebook_url} onChange={set('facebook_url')} />
      <TextField label="Instagram page" type="url" placeholder="https://instagram.com/…" value={v.instagram_url} onChange={set('instagram_url')} />
      <div className="mt-2 flex justify-end gap-3">
        <Button variant="outline" onClick={onDone}>
          Cancel
        </Button>
        <Button type="submit" loading={update.isPending}>
          Save
        </Button>
      </div>
    </form>
  )
}
