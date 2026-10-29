import type { ReactNode } from 'react'
import { Icon, type IconName } from './Icon'

const tones = {
  muted: 'bg-muted text-ink-2',
  accent: 'bg-terracotta-soft text-terracotta-strong',
  nile: 'bg-nile-soft text-nile-strong',
  gold: 'bg-gold-soft text-warning',
}

export function Chip({
  icon,
  tone = 'muted',
  children,
  className = '',
}: {
  icon?: IconName
  tone?: keyof typeof tones
  children: ReactNode
  className?: string
}) {
  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-full px-3.5 py-1.5 text-[15px] font-semibold ${tones[tone]} ${className}`}
    >
      {icon && <Icon name={icon} size={16} />}
      {children}
    </span>
  )
}
