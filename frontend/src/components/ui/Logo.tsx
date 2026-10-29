import { Link } from 'react-router-dom'
import logo from '@/assets/logo.svg'

const sizes = {
  lg: { mark: 36, text: 'text-[26px]' },
  md: { mark: 32, text: 'text-[22px]' },
  sm: { mark: 28, text: 'text-[20px]' },
}

export function Logo({ size = 'lg', to = '/' }: { size?: keyof typeof sizes; to?: string }) {
  const s = sizes[size]
  return (
    <Link to={to} className="inline-flex items-center gap-2.5 rounded-lg" aria-label="Egyptora home">
      <img src={logo} width={s.mark} height={s.mark} alt="" />
      <span className={`font-display ${s.text} leading-none tracking-[-0.01em] text-ink`}>Egyptora</span>
    </Link>
  )
}
