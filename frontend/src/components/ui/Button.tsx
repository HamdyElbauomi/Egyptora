import type { ButtonHTMLAttributes, ReactNode } from 'react'
import { Link } from 'react-router-dom'
import { Icon, type IconName } from './Icon'
import { Spinner } from './Spinner'

type Variant = 'primary' | 'outline' | 'dark' | 'ghost'
type Size = 'lg' | 'md' | 'sm'

const variants: Record<Variant, string> = {
  primary: 'bg-terracotta text-white hover:bg-terracotta-strong shadow-[0_1px_0_rgba(31,26,23,0.08)]',
  outline: 'border-[1.5px] border-line-strong bg-card text-ink hover:border-line-muted',
  dark: 'bg-inverse text-on-dark hover:bg-black',
  ghost: 'text-terracotta hover:text-terracotta-strong',
}

const sizes: Record<Size, string> = {
  lg: 'gap-3 rounded-[14px] px-7 py-[17px] text-[17px]',
  md: 'gap-2.5 rounded-xl px-[26px] py-[15px] text-base',
  sm: 'gap-2 rounded-[10px] px-4 py-2.5 text-[15px]',
}

interface Common {
  variant?: Variant
  size?: Size
  icon?: IconName
  /** icon placed before the text instead of after it */
  leadingIcon?: IconName
  loading?: boolean
  className?: string
  children: ReactNode
}

function classes({ variant = 'primary', size = 'md', className = '' }: Common) {
  return [
    'inline-flex items-center justify-center font-bold leading-none whitespace-nowrap transition-colors',
    'focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-terracotta',
    'disabled:opacity-50',
    variants[variant],
    variant === 'ghost' ? 'px-0 py-1' : sizes[size],
    className,
  ].join(' ')
}

function Content({ icon, leadingIcon, loading, children, size = 'md' }: Common) {
  const iconSize = size === 'lg' ? 20 : 18
  return (
    <>
      {loading ? <Spinner size={iconSize} /> : leadingIcon && <Icon name={leadingIcon} size={iconSize} />}
      <span>{children}</span>
      {icon && <Icon name={icon} size={iconSize} />}
    </>
  )
}

export function Button(props: Common & Omit<ButtonHTMLAttributes<HTMLButtonElement>, 'children' | 'className'>) {
  const { variant, size, icon, leadingIcon, loading, className, children, disabled, ...rest } = props
  return (
    <button
      type="button"
      {...rest}
      disabled={disabled || loading}
      className={classes({ variant, size, className, children })}
    >
      <Content {...{ icon, leadingIcon, loading, size, children }} />
    </button>
  )
}

export function ButtonLink(props: Common & { to: string }) {
  const { to, variant, size, icon, leadingIcon, className, children } = props
  return (
    <Link to={to} className={classes({ variant, size, className, children })}>
      <Content {...{ icon, leadingIcon, size, children }} />
    </Link>
  )
}
