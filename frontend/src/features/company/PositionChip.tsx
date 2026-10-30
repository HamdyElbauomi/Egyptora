import type { MyOffer } from '@/api/company'

/** Where the offer's price ranks among live offers for the same hotel and room type. */
export function PositionChip({ offer }: { offer: Pick<MyOffer, 'position' | 'competitors'> }) {
  const { position, competitors } = offer
  if (position === null || position === undefined) return <span className="text-sm text-ink-3">—</span>
  const [text, tone] =
    competitors <= 1
      ? ['Only offer', 'bg-muted text-ink-2']
      : position === 1
        ? ['#1 · Lowest', 'bg-nile-soft text-nile-strong']
        : position === competitors
          ? [`#${position} of ${competitors}`, 'bg-terracotta-soft text-terracotta-strong']
          : [`#${position} of ${competitors}`, 'bg-gold-soft text-warning']
  return <span className={`inline-block rounded-full px-2.5 py-1 text-[13px] font-semibold whitespace-nowrap ${tone}`}>{text}</span>
}
