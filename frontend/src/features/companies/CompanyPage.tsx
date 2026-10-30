import { useQueryClient } from '@tanstack/react-query'
import { useState, type FormEvent } from 'react'
import { Link, useParams } from 'react-router-dom'
import { useAddReview, useCompany, useCompanyReviews } from '@/api/hotels'
import { useAuth } from '@/auth/AuthProvider'
import { Button } from '@/components/ui/Button'
import { ErrorState } from '@/components/ui/ErrorState'
import { TextArea } from '@/components/ui/fields'
import { Icon } from '@/components/ui/Icon'
import { Logo } from '@/components/ui/Logo'
import { PageLoader } from '@/components/ui/Spinner'
import { StarInput } from '@/components/ui/Stars'
import { useToast } from '@/components/ui/Toast'
import { initials, plural } from '@/lib/format'
import { ReviewList } from './ReviewList'

/** Public page of a travel company: trust score, links and traveler reviews. */
export function CompanyPage() {
  const id = Number(useParams().companyId)
  const company = useCompany(id)
  const [page, setPage] = useState(1)
  const reviews = useCompanyReviews(id, page)
  const { session } = useAuth()

  return (
    <div className="min-h-dvh">
      <header className="border-b border-line">
        <div className="mx-auto flex h-16 max-w-[1100px] items-center justify-between px-4 sm:px-10">
          <Logo size="sm" to={session?.role === 'traveler' ? '/trips' : '/'} />
          <button type="button" onClick={() => history.back()} className="inline-flex items-center gap-1.5 text-[15px] font-semibold text-ink-2 hover:text-ink">
            <Icon name="arrowL" size={18} /> Back
          </button>
        </div>
      </header>
      <main className="mx-auto max-w-[1100px] px-4 py-8 sm:px-10">
        {company.isPending ? (
          <PageLoader />
        ) : company.isError ? (
          <ErrorState title="Company not found" action={<Link to="/" className="font-bold text-terracotta">Go home</Link>}>
            It may no longer be on Egyptora.
          </ErrorState>
        ) : (
          <div className="grid gap-6 lg:grid-cols-[minmax(0,1fr)_340px]">
            <div className="flex flex-col gap-6">
              <section className="rounded-[22px] border border-line bg-card p-6">
                <div className="flex items-center gap-4">
                  <span className="grid size-16 shrink-0 place-items-center rounded-2xl bg-nile font-display text-2xl text-white">
                    {initials(company.data.name)}
                  </span>
                  <div>
                    <h1 className="font-display text-[30px] leading-tight">{company.data.name}</h1>
                    <p className="mt-1 flex flex-wrap items-center gap-2 text-sm text-ink-2">
                      {company.data.years_active ? `${plural(company.data.years_active, 'year')} in business · ` : ''}
                      <span className="inline-flex items-center gap-1 rounded-full bg-nile-soft px-2.5 py-0.5 font-semibold text-nile-strong">
                        <Icon name="check" size={14} /> License verified
                      </span>
                    </p>
                  </div>
                </div>
                <div className="mt-5 flex flex-wrap gap-x-5 gap-y-2 text-[15px]">
                  {[
                    ['Website', company.data.website],
                    ['Facebook', company.data.facebook_url],
                    ['Instagram', company.data.instagram_url],
                  ]
                    .filter(([, url]) => url)
                    .map(([label, url]) => (
                      <a key={label} href={url!} target="_blank" rel="noreferrer" className="inline-flex items-center gap-1.5 font-semibold text-terracotta hover:underline">
                        <Icon name="link" size={16} /> {label}
                      </a>
                    ))}
                  {company.data.google_rating && (
                    <span className="inline-flex items-center gap-1.5 text-ink-2">
                      <Icon name="pin" size={16} /> Google {company.data.google_rating.toFixed(1)}
                    </span>
                  )}
                </div>
              </section>

              <section className="rounded-[22px] border border-line bg-card p-6">
                <div className="mb-4 flex items-center justify-between">
                  <h2 className="text-lg font-bold">Traveler reviews</h2>
                  <span className="rounded-full bg-muted px-3 py-1 text-sm font-semibold">{plural(company.data.reviews_count, 'review')}</span>
                </div>
                {reviews.isPending ? <PageLoader /> : reviews.isError ? null : <ReviewList reviews={reviews.data.data} />}
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
              </section>
            </div>

            <aside className="flex flex-col gap-5">
              <section className="rounded-[22px] border border-line bg-card p-6">
                <p className="font-bold">Trust score</p>
                <p className="mt-2 font-display text-[52px] leading-none">
                  {company.data.trust_score?.toFixed(1) ?? '—'}
                  <span className="font-sans text-lg text-ink-3"> / 5</span>
                </p>
                <p className="mt-3 text-sm text-ink-2">
                  Starts from the company’s license, Google rating and years in business, then follows what Egyptora travelers rate them.
                </p>
              </section>
              {session?.role === 'traveler' && <WriteReview companyId={id} />}
            </aside>
          </div>
        )}
      </main>
    </div>
  )
}

function WriteReview({ companyId }: { companyId: number }) {
  const add = useAddReview(companyId)
  const queryClient = useQueryClient()
  const toast = useToast()
  const [rating, setRating] = useState(0)
  const [comment, setComment] = useState('')
  const [done, setDone] = useState(false)

  const submit = (e: FormEvent) => {
    e.preventDefault()
    if (!rating) return
    add.mutate(
      { rating, comment: comment.trim() || null, trip_id: null },
      {
        onSuccess: () => {
          setDone(true)
          toast('Thanks for your review')
          void queryClient.invalidateQueries({ queryKey: ['company', companyId] })
          void queryClient.invalidateQueries({ queryKey: ['company-reviews', companyId] })
        },
        onError: (err) => toast(err.message, 'error'),
      },
    )
  }

  if (done)
    return (
      <p className="rounded-[22px] bg-nile-soft p-5 text-[15px] text-nile-strong">
        Thanks — your review helps other travelers and updates this company’s trust score.
      </p>
    )

  return (
    <form onSubmit={submit} className="rounded-[22px] border border-line bg-card p-6">
      <h2 className="font-bold">Rate your stay</h2>
      <p className="mt-1 text-sm text-ink-2">For travelers who booked a night with this company in one of their trips.</p>
      <div className="mt-4">
        <StarInput value={rating} onChange={setRating} />
      </div>
      <div className="mt-4">
        <TextArea label="What was it like? (optional)" maxLength={2000} value={comment} onChange={(e) => setComment(e.target.value)} />
      </div>
      <Button type="submit" className="mt-4 w-full" loading={add.isPending} disabled={!rating}>
        Post review
      </Button>
    </form>
  )
}
