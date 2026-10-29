import { createContext, useCallback, useContext, useMemo, useState, type ReactNode } from 'react'
import { Icon } from './Icon'

type Tone = 'success' | 'error'
interface ToastItem {
  id: number
  text: string
  tone: Tone
}

const ToastContext = createContext<((text: string, tone?: Tone) => void) | null>(null)
let nextId = 1

/** Short messages at the bottom of the screen: "Saved", "Couldn’t remove the stop"… */
export function ToastProvider({ children }: { children: ReactNode }) {
  const [items, setItems] = useState<ToastItem[]>([])

  const show = useCallback((text: string, tone: Tone = 'success') => {
    const id = nextId++
    setItems((list) => [...list.slice(-2), { id, text, tone }])
    setTimeout(() => setItems((list) => list.filter((t) => t.id !== id)), tone === 'error' ? 6000 : 3500)
  }, [])

  const value = useMemo(() => show, [show])

  return (
    <ToastContext.Provider value={value}>
      {children}
      <div aria-live="polite" className="pointer-events-none fixed inset-x-0 top-4 z-50 flex flex-col items-center gap-2 px-4">
        {items.map((t) => (
          <p
            key={t.id}
            role={t.tone === 'error' ? 'alert' : 'status'}
            className={`pointer-events-auto flex max-w-[520px] items-center gap-2.5 rounded-2xl px-4 py-3 text-[15px] font-semibold shadow-[0_12px_32px_rgba(31,26,23,0.25)] ${
              t.tone === 'error' ? 'bg-terracotta-strong text-white' : 'bg-inverse text-on-dark'
            }`}
          >
            <Icon name={t.tone === 'error' ? 'alert' : 'check'} size={18} />
            {t.text}
          </p>
        ))}
      </div>
    </ToastContext.Provider>
  )
}

// the hook lives next to its provider on purpose
// oxlint-disable-next-line react/only-export-components
export function useToast() {
  const show = useContext(ToastContext)
  if (!show) throw new Error('useToast must be used inside <ToastProvider>')
  return show
}
