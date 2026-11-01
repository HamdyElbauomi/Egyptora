import { NavLink, Outlet, useNavigate } from 'react-router-dom'
import { useAuth } from '@/auth/AuthProvider'
import { Icon, type IconName } from '@/components/ui/Icon'
import logo from '@/assets/logo.svg'

const NAV: { to: string; label: string; icon: IconName; end?: boolean }[] = [
  { to: '/admin', label: 'Overview', icon: 'chart', end: true },
  { to: '/admin/companies', label: 'Companies', icon: 'briefcase' },
  { to: '/admin/hotels', label: 'Hotels & offers', icon: 'bed' },
  { to: '/admin/places', label: 'Places & monuments', icon: 'history' },
  { to: '/admin/catalog', label: 'Cities & interests', icon: 'pin' },
  { to: '/admin/ai', label: 'AI quality', icon: 'spark' },
]

/** Admin frame: dark sidebar on desktop, top bar with tabs on phones. */
export function AdminShell() {
  const { user, signOut } = useAuth()
  const navigate = useNavigate()
  const out = () => {
    signOut()
    navigate('/', { replace: true })
  }

  return (
    <div className="min-h-dvh lg:flex">
      <aside className="sticky top-0 hidden h-dvh w-[248px] shrink-0 flex-col bg-inverse p-5 text-on-dark lg:flex">
        <div className="flex items-center gap-2.5 px-1">
          <img src={logo} alt="" width={30} height={30} />
          <span className="font-display text-[21px]">Egyptora</span>
          <span className="rounded-full bg-gold-soft px-2.5 py-0.5 text-[12px] font-bold text-warning">Admin</span>
        </div>
        <p className="mt-8 px-3 text-[11px] font-bold tracking-[0.12em] text-on-dark-muted/70">WORKSPACE</p>
        <nav aria-label="Admin" className="mt-2 flex flex-col gap-1">
          {NAV.map((n) => (
            <NavLink
              key={n.to}
              to={n.to}
              end={n.end}
              className={({ isActive }) =>
                `flex items-center gap-3 rounded-xl px-3 py-2.5 text-[15px] font-semibold ${
                  isActive ? 'bg-white/10 text-white' : 'text-on-dark-muted hover:bg-white/5 hover:text-white'
                }`
              }
            >
              {({ isActive }) => (
                <>
                  <Icon name={n.icon} size={18} className={isActive ? 'text-gold-light' : ''} />
                  {n.label}
                </>
              )}
            </NavLink>
          ))}
        </nav>
        <div className="mt-auto border-t border-white/10 pt-4">
          <div className="flex items-center gap-3 px-1">
            <span className="grid size-9 place-items-center rounded-full bg-nile font-bold text-white">
              {(user?.name ?? 'A').charAt(0).toUpperCase()}
            </span>
            <div className="min-w-0 flex-1">
              <p className="truncate text-[15px] font-semibold">{user?.name ?? 'Admin'}</p>
              <p className="text-[12px] text-on-dark-muted">Egyptora team</p>
            </div>
            <button type="button" onClick={out} aria-label="Sign out" className="rounded-lg p-2 text-on-dark-muted hover:bg-white/10 hover:text-white">
              <Icon name="arrowL" size={18} />
            </button>
          </div>
        </div>
      </aside>

      <div className="min-w-0 flex-1">
        <header className="sticky top-0 z-20 bg-inverse px-4 py-3 text-on-dark lg:hidden">
          <div className="flex items-center justify-between">
            <span className="flex items-center gap-2">
              <img src={logo} alt="" width={26} height={26} />
              <span className="font-display text-lg">Egyptora</span>
              <span className="rounded-full bg-gold-soft px-2 py-0.5 text-[11px] font-bold text-warning">Admin</span>
            </span>
            <button type="button" onClick={out} className="text-sm font-semibold text-on-dark-muted">
              Sign out
            </button>
          </div>
          <nav aria-label="Admin" className="-mx-1 mt-2 flex gap-1 overflow-x-auto px-1">
            {NAV.map((n) => (
              <NavLink
                key={n.to}
                to={n.to}
                end={n.end}
                className={({ isActive }) =>
                  `shrink-0 rounded-full px-3 py-1.5 text-sm font-semibold ${isActive ? 'bg-white/15 text-white' : 'text-on-dark-muted'}`
                }
              >
                {n.label}
              </NavLink>
            ))}
          </nav>
        </header>
        <main className="mx-auto max-w-[1280px] px-4 py-7 sm:px-10 lg:py-10">
          <Outlet />
        </main>
      </div>
    </div>
  )
}
