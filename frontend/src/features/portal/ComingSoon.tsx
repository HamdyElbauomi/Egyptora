import { useAuth } from '@/auth/AuthProvider'
import { Icon } from '@/components/ui/Icon'

/** Signed-in landing for admin accounts until their screens arrive (day 4). */
export function ComingSoon({ area }: { area: 'Admin' }) {
  const { user } = useAuth()
  return (
    <div className="mx-auto flex max-w-lg flex-col items-center py-16 text-center">
      <span className="grid size-14 place-items-center rounded-2xl bg-nile-soft text-nile">
        <Icon name="shield" size={26} />
      </span>
      <h1 className="mt-5 font-display text-[34px] leading-tight">{area}</h1>
      <p className="mt-3 text-[17px] text-ink-2">
        Welcome{user ? `, ${user.name}` : ''}. Your dashboard is being built and will appear here soon.
      </p>
    </div>
  )
}
