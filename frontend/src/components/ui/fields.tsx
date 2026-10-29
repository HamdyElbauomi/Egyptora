import { useId, type ReactNode, type SelectHTMLAttributes, type TextareaHTMLAttributes } from 'react'

const box =
  'w-full rounded-[14px] border-[1.5px] border-line-strong bg-card px-4 text-base text-ink outline-none transition-colors placeholder:text-ink-4 focus:border-terracotta'

export function TextArea({ label, hint, ...props }: TextareaHTMLAttributes<HTMLTextAreaElement> & { label: string; hint?: ReactNode }) {
  const id = useId()
  return (
    <div>
      <label htmlFor={id} className="mb-2 block text-[15px] font-semibold text-ink-2">
        {label}
      </label>
      <textarea id={id} rows={3} className={`${box} resize-y py-3`} {...props} />
      {hint && <p className="mt-2 text-sm text-ink-3">{hint}</p>}
    </div>
  )
}

export function Select({ label, children, ...props }: SelectHTMLAttributes<HTMLSelectElement> & { label: string }) {
  const id = useId()
  return (
    <div>
      <label htmlFor={id} className="mb-2 block text-[15px] font-semibold text-ink-2">
        {label}
      </label>
      <select id={id} className={`${box} h-14`} {...props}>
        {children}
      </select>
    </div>
  )
}
