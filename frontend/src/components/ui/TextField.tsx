import { useId, type InputHTMLAttributes, type ReactNode } from 'react'

interface TextFieldProps extends InputHTMLAttributes<HTMLInputElement> {
  label: string
  hint?: ReactNode
  error?: string
  /** text shown inside the field before the value, e.g. "EGP" */
  prefix?: string
}

export function TextField({ label, hint, error, prefix, className = '', ...input }: TextFieldProps) {
  const id = useId()
  const hintId = `${id}-hint`
  return (
    <div className={className}>
      <label htmlFor={id} className="mb-2 block text-[15px] font-semibold text-ink-2">
        {label}
      </label>
      <div
        className={`flex h-14 items-center gap-2 rounded-[14px] border-[1.5px] bg-card px-4 transition-colors focus-within:border-terracotta ${
          error ? 'border-terracotta' : 'border-line-strong'
        }`}
      >
        {prefix && <span className="text-[15px] font-semibold text-ink-3">{prefix}</span>}
        <input
          id={id}
          aria-invalid={Boolean(error) || undefined}
          aria-describedby={hint || error ? hintId : undefined}
          className="h-full w-full min-w-0 bg-transparent text-base text-ink outline-none placeholder:text-ink-4"
          {...input}
        />
      </div>
      {(error || hint) && (
        <p id={hintId} className={`mt-2 text-sm ${error ? 'font-semibold text-terracotta' : 'text-ink-3'}`}>
          {error ?? hint}
        </p>
      )}
    </div>
  )
}
