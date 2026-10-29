import { useEffect, useRef, useState, type ReactNode } from 'react'
import { Link, NavLink, Outlet, useNavigate } from 'react-router-dom'
import { useAuth } from '@/auth/AuthProvider'
import { Icon } from '@/components/ui/Icon'
import { Logo } from '@/components/ui/Logo'

export interface NavItem {
  to: string
  label: string
  end?: boolean
}

/** Top bar shared by all signed-in areas: logo, section links and the account menu. */
export function AppShell({ nav, home, children }: { nav: NavItem[]; home: string; children?: ReactNode }) {
  return (
    <div className="min-h-dvh">
      <header className="sticky top-0 z-20 border-b border-line bg-canvas/95 backdrop-blur print:hidden">
        <div className="mx-auto flex max-w-[1440px] flex-wrap items-center gap-x-4 gap-y-2 px-4 py-3 sm:px-10 lg:h-[72px] lg:flex-nowrap lg:py-0">
          <Logo size="sm" to={home} />
          <nav aria-label="Main" className="order-3 -mx-1 flex w-full gap-1 overflow-x-auto px-1 lg:order-none lg:mx-auto lg:w-auto">
            {nav.map((item) => (
              <NavLink
                key={item.to}
                to={item.to}
                end={item.end}
                className={({ isActive }) =>
                  `shrink-0 rounded-full px-4 py-2.5 text-[15px] font-semibold transition-colors ${
                    isActive ? 'bg-inverse text-on-dark' : 'text-ink hover:bg-muted'
                  }`
                }
              >
                {item.label}
              </NavLink>
            ))}
          </nav>
          <AccountMenu />
        </div>
      </header>
      <main className="mx-auto max-w-[1440px] px-4 py-7 sm:px-10 lg:py-9">{children ?? <Outlet />}</main>
    </div>
  )
}

function AccountMenu() {
  const { user, session, signOut } = useAuth()
  const navigate = useNavigate()
  const [open, setOpen] = useState(false)
  const ref = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (!open) return
    const close = (e: MouseEvent | KeyboardEvent) => {
      if (e instanceof KeyboardEvent ? e.key === 'Escape' : !ref.current?.contains(e.target as Node)) setOpen(false)
    }
    document.addEventListener('mousedown', close)
    document.addEventListener('keydown', close)
    return () => {
      document.removeEventListener('mousedown', close)
      document.removeEventListener('keydown', close)
    }
  }, [open])

  const initial = (user?.name ?? '?').trim().charAt(0).toUpperCase()

  return (
    <div ref={ref} className="relative ml-auto lg:ml-0">
      <button
        type="button"
        aria-haspopup="menu"
        aria-expanded={open}
        aria-label="Account"
        onClick={() => setOpen((o) => !o)}
        className="grid size-10 place-items-center rounded-full bg-nile text-base font-bold text-white focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-terracotta"
      >
        {initial}
      </button>
      {open && (
        <div role="menu" className="absolute right-0 mt-2 w-64 rounded-2xl border border-line bg-card p-2 shadow-[0_16px_40px_rgba(31,26,23,0.14)]">
          <div className="px-3 py-2.5">
            <p className="truncate font-bold">{user?.name ?? '…'}</p>
            <p className="truncate text-sm text-ink-3">{user?.email}</p>
            <p className="mt-1 text-xs font-bold tracking-[0.08em] text-nile uppercase">{session?.role}</p>
          </div>
          {session?.role === 'traveler' && (
            <Link
              to="/trips"
              role="menuitem"
              onClick={() => setOpen(false)}
              className="flex w-full items-center gap-2.5 rounded-xl px-3 py-2.5 text-[15px] font-semibold hover:bg-muted"
            >
              <Icon name="list" size={18} />
              My trips
            </Link>
          )}
          <button
            type="button"
            role="menuitem"
            onClick={() => {
              signOut()
              navigate('/', { replace: true })
            }}
            className="flex w-full items-center gap-2.5 rounded-xl px-3 py-2.5 text-left text-[15px] font-semibold hover:bg-muted"
          >
            <Icon name="arrowL" size={18} />
            Sign out
          </button>
        </div>
      )}
    </div>
  )
}

