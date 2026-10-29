import { useEffect, useRef, useState, type ReactNode } from 'react'
import { Icon, type IconName } from './Icon'

export interface MenuAction {
  label: string
  icon?: IconName
  onSelect: () => void
  disabled?: boolean
  danger?: boolean
}

/** A small "⋯" menu. Closes on outside click, Esc, or after picking an action. */
export function Menu({ label, actions, trigger }: { label: string; actions: MenuAction[]; trigger?: ReactNode }) {
  const [open, setOpen] = useState(false)
  const ref = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (!open) return
    const close = (e: MouseEvent | KeyboardEvent) => {
      if (e instanceof KeyboardEvent ? e.key === 'Escape' : !ref.current?.contains(e.target as Node)) setOpen(false)
    }
    document.addEventListener('mousedown', close)
    document.addEventListener('keydown', close)
    return () => {
      document.removeEventListener('mousedown', close)
      document.removeEventListener('keydown', close)
    }
  }, [open])

  return (
    <div ref={ref} className="relative">
      <button
        type="button"
        aria-label={label}
        aria-haspopup="menu"
        aria-expanded={open}
        onClick={() => setOpen((o) => !o)}
        className="grid size-9 place-items-center rounded-[10px] text-ink-2 hover:bg-muted focus-visible:outline-2 focus-visible:outline-terracotta"
      >
        {trigger ?? <Icon name="more" size={20} />}
      </button>
      {open && (
        <div role="menu" className="absolute right-0 z-30 mt-1 w-56 rounded-2xl border border-line bg-card p-1.5 shadow-[0_16px_40px_rgba(31,26,23,0.16)]">
          {actions.map((a) => (
            <button
              key={a.label}
              type="button"
              role="menuitem"
              disabled={a.disabled}
              onClick={() => {
                setOpen(false)
                a.onSelect()
              }}
              className={`flex w-full items-center gap-2.5 rounded-xl px-3 py-2.5 text-left text-[15px] font-semibold hover:bg-muted disabled:opacity-40 ${
                a.danger ? 'text-terracotta-strong' : 'text-ink'
              }`}
            >
              {a.icon && <Icon name={a.icon} size={18} />}
              {a.label}
            </button>
          ))}
        </div>
      )}
    </div>
  )
}
