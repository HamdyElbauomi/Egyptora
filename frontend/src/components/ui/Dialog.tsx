import { useEffect, useRef, type ReactNode } from 'react'
import { Icon } from './Icon'

interface DialogProps {
  open: boolean
  onClose: () => void
  title: string
  description?: ReactNode
  children: ReactNode
  /** buttons row at the bottom */
  footer?: ReactNode
  size?: 'md' | 'lg'
}

/** Modal built on the native <dialog>: focus trap, Esc to close and a backdrop for free.
    On phones it opens as a bottom sheet. */
export function Dialog({ open, onClose, title, description, children, footer, size = 'md' }: DialogProps) {
  const ref = useRef<HTMLDialogElement>(null)

  useEffect(() => {
    const dialog = ref.current
    if (!dialog) return
    if (open && !dialog.open) dialog.showModal()
    if (!open && dialog.open) dialog.close()
  }, [open])

  return (
    <dialog
      ref={ref}
      onClose={onClose}
      onClick={(e) => e.target === ref.current && onClose()}
      aria-labelledby="dialog-title"
      className={`m-0 mt-auto max-h-[92dvh] w-full max-w-none overflow-hidden rounded-t-[24px] bg-card p-0 text-ink shadow-[0_24px_60px_rgba(31,26,23,0.25)] backdrop:bg-inverse/45 sm:m-auto sm:rounded-[24px] ${
        size === 'lg' ? 'sm:max-w-[720px]' : 'sm:max-w-[520px]'
      }`}
    >
      {open && (
        <div className="flex max-h-[92dvh] flex-col">
          <header className="flex items-start gap-4 border-b border-line px-6 pt-6 pb-4">
            <div className="min-w-0 flex-1">
              <h2 id="dialog-title" className="font-display text-2xl leading-tight">
                {title}
              </h2>
              {description && <p className="mt-1.5 text-[15px] text-ink-2">{description}</p>}
            </div>
            <button
              type="button"
              onClick={onClose}
              aria-label="Close"
              className="grid size-9 shrink-0 place-items-center rounded-full text-ink-2 hover:bg-muted"
            >
              <Icon name="x" size={20} />
            </button>
          </header>
          <div className="min-h-0 flex-1 overflow-y-auto px-6 py-5">{children}</div>
          {footer && <footer className="flex flex-wrap justify-end gap-3 border-t border-line bg-raised px-6 py-4">{footer}</footer>}
        </div>
      )}
    </dialog>
  )
}
