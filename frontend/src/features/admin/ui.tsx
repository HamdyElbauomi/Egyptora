import type { ReactNode } from 'react'

/** Page title row used on every admin screen. */
export function AdminHeader({ title, subtitle, actions }: { title: string; subtitle: string; actions?: ReactNode }) {
  return (
    <div className="flex flex-wrap items-end justify-between gap-4">
      <div>
        <h1 className="font-display text-[32px] leading-tight sm:text-[38px]">{title}</h1>
        <p className="mt-1.5 text-[15px] text-ink-2">{subtitle}</p>
      </div>
      {actions && <div className="flex flex-wrap gap-3">{actions}</div>}
    </div>
  )
}

/** Pill tabs with counts: "Pending · 3". */
export function Tabs<T extends string>({
  value,
  onChange,
  items,
}: {
  value: T
  onChange: (v: T) => void
  items: { value: T; label: string; count?: number }[]
}) {
  return (
    <div role="tablist" className="flex flex-wrap gap-2">
      {items.map((t) => (
        <button
          key={t.value}
          type="button"
          role="tab"
          aria-selected={value === t.value}
          onClick={() => onChange(t.value)}
          className={`rounded-full border-[1.5px] px-4 py-2 text-[15px] font-semibold ${
            value === t.value ? 'border-nile bg-nile text-white' : 'border-line-strong bg-card text-ink hover:border-line-muted'
          }`}
        >
          {t.label}
          {t.count !== undefined ? ` · ${t.count}` : ''}
        </button>
      ))}
    </div>
  )
}
