import type { ReactNode } from 'react'
import { Icon } from './Icon'

export function ErrorState({ title, children, action }: { title: string; children?: ReactNode; action?: ReactNode }) {
  return (
    <div role="alert" className="mx-auto flex max-w-md flex-col items-center gap-3 py-16 text-center">
      <span className="grid size-12 place-items-center rounded-2xl bg-terracotta-soft text-terracotta">
        <Icon name="alert" size={24} />
      </span>
      <h2 className="font-display text-2xl">{title}</h2>
      {children && <p className="text-[15px] text-ink-2">{children}</p>}
      {action && <div className="mt-2">{action}</div>}
    </div>
  )
}
