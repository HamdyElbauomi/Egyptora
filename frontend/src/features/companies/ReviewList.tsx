import type { Review } from '@/api/hotels'
import { Stars } from '@/components/ui/Stars'
import { formatDate } from '@/lib/format'

const SENTIMENT = {
  positive: 'bg-nile-soft text-nile-strong',
  neutral: 'bg-muted text-ink-2',
  negative: 'bg-terracotta-soft text-terracotta-strong',
} as const

export function ReviewList({ reviews, showSentiment = false }: { reviews: Review[]; showSentiment?: boolean }) {
  if (reviews.length === 0) return <p className="rounded-2xl bg-raised px-5 py-8 text-center text-[15px] text-ink-3">No reviews yet.</p>
  return (
    <ul>
      {reviews.map((r) => (
        <li key={r.id} className="border-t border-line py-4 first:border-t-0 first:pt-0">
          <p className="flex flex-wrap items-center gap-2 text-sm text-ink-3">
            <Stars value={r.rating} size={15} />
            {r.reviewer_name} · {formatDate(r.created_at.slice(0, 10), true)}
            {showSentiment && r.sentiment && (
              <span className={`rounded-full px-2 py-0.5 text-[12px] font-semibold ${SENTIMENT[r.sentiment as keyof typeof SENTIMENT] ?? SENTIMENT.neutral}`}>
                {r.sentiment}
              </span>
            )}
          </p>
          {r.comment && <p className="mt-1.5 text-[15px]">{r.comment}</p>}
        </li>
      ))}
    </ul>
  )
}
