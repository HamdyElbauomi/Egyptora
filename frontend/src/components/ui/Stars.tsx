import { Icon } from './Icon'

export function Stars({ value, size = 16 }: { value: number; size?: number }) {
  return (
    <span className="inline-flex gap-0.5" role="img" aria-label={`${value} out of 5`}>
      {[1, 2, 3, 4, 5].map((n) => (
        <Icon key={n} name="star" size={size} className={n <= Math.round(value) ? 'text-gold' : 'text-line-strong'} />
      ))}
    </span>
  )
}

/** Five tappable stars for writing a review. */
export function StarInput({ value, onChange }: { value: number; onChange: (n: number) => void }) {
  return (
    <div role="radiogroup" aria-label="Rating" className="flex gap-1">
      {[1, 2, 3, 4, 5].map((n) => (
        <button
          key={n}
          type="button"
          role="radio"
          aria-checked={value === n}
          aria-label={`${n} star${n > 1 ? 's' : ''}`}
          onClick={() => onChange(n)}
          className="rounded-md p-0.5 focus-visible:outline-2 focus-visible:outline-terracotta"
        >
          <Icon name="star" size={30} className={n <= value ? 'text-gold' : 'text-line-strong'} />
        </button>
      ))}
    </div>
  )
}
