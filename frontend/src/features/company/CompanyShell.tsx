import { NavLink, Outlet, useLocation, useNavigate } from 'react-router-dom'
import { useMyCompany, type Company } from '@/api/company'
import { useAuth } from '@/auth/AuthProvider'
import { Button } from '@/components/ui/Button'
import { ErrorState } from '@/components/ui/ErrorState'
import { Icon, type IconName } from '@/components/ui/Icon'
import { Logo } from '@/components/ui/Logo'
import { PageLoader } from '@/components/ui/Spinner'
import { initials } from '@/lib/format'
import { PendingPage } from './PendingPage'

const NAV: { to: string; label: string; icon: IconName; end?: boolean }[] = [
  { to: '/company', label: 'Dashboard', icon: 'chart', end: true },
  { to: '/company/offers', label: 'My offers', icon: 'list', end: true },
  { to: '/company/offers/new', label: 'Add offer', icon: 'plus' },
  { to: '/company/profile', label: 'Company profile', icon: 'briefcase' },
]

const STATUS: Record<string, { label: string; tone: string }> = {
  approved: { label: 'Approved', tone: 'bg-nile-soft text-nile-strong' },
  pending: { label: 'In review', tone: 'bg-gold-soft text-warning' },
  rejected: { label: 'Not approved', tone: 'bg-terracotta-soft text-terracotta-strong' },
  suspended: { label: 'Suspended', tone: 'bg-terracotta-soft text-terracotta-strong' },
}

/** The company portal frame: sidebar on desktop, top bar with tabs on phones.
    Until the company is approved, every page except the profile shows the application status. */
export function CompanyShell() {
  const company = useMyCompany()
  const { signOut } = useAuth()
  const navigate = useNavigate()
  const { pathname } = useLocation()
  const out = () => {
    signOut()
    navigate('/', { replace: true })
  }

  if (company.isPending) return <PageLoader />
  if (company.isError)
    return <ErrorState title="We couldn’t load your company" action={<Button onClick={() => company.refetch()}>Try again</Button>} />

  const c = company.data
  const approved = c.status === 'approved'

  return (
    <div className="min-h-dvh lg:flex">
      <aside className="sticky top-0 hidden h-dvh w-[248px] shrink-0 flex-col border-r border-line bg-raised p-6 lg:flex print:hidden">
        <div className="flex items-center gap-2">
          <Logo size="sm" to="/company" />
          <span className="rounded-full bg-nile-soft px-2.5 py-0.5 text-[12px] font-semibold text-nile-strong">Partner</span>
        </div>
        <CompanyCard company={c} />
        <nav aria-label="Portal" className="mt-6 flex flex-col gap-1">
          {NAV.map((n) => (
            <NavLink
              key={n.to}
              to={n.to}
              end={n.end}
              className={({ isActive }) =>
                `flex items-center gap-3 rounded-xl border px-3.5 py-2.5 text-[15px] font-semibold ${
                  isActive ? 'border-line bg-card text-ink' : 'border-transparent text-ink-2 hover:bg-muted'
                }`
              }
            >
              <Icon name={n.icon} size={18} />
              {n.label}
            </NavLink>
          ))}
        </nav>
        <div className="mt-auto">
          <button type="button" onClick={out} className="mb-4 flex items-center gap-2 px-3.5 text-[15px] font-semibold text-ink-2 hover:text-terracotta">
            <Icon name="arrowL" size={18} /> Sign out
          </button>
          <div className="rounded-2xl bg-muted p-4 text-sm">
            <p className="font-bold">Need help with an offer?</p>
            <p className="mt-1 text-ink-2">Write to the Egyptora team from your company email.</p>
          </div>
        </div>
      </aside>

      <div className="min-w-0 flex-1">
        <header className="sticky top-0 z-20 border-b border-line bg-canvas/95 px-4 py-3 backdrop-blur lg:hidden">
          <div className="flex items-center justify-between">
            <Logo size="sm" to="/company" />
            <button type="button" onClick={out} className="text-[15px] font-semibold text-terracotta">
              Sign out
            </button>
          </div>
          <nav aria-label="Portal" className="-mx-1 mt-2 flex gap-1 overflow-x-auto px-1">
            {NAV.map((n) => (
              <NavLink
                key={n.to}
                to={n.to}
                end={n.end}
                className={({ isActive }) =>
                  `shrink-0 rounded-full px-3.5 py-2 text-sm font-semibold ${isActive ? 'bg-inverse text-on-dark' : 'text-ink'}`
                }
              >
                {n.label}
              </NavLink>
            ))}
          </nav>
        </header>
        <main className="mx-auto max-w-[1200px] px-4 py-7 sm:px-10 lg:py-10">
          {approved || pathname.startsWith('/company/profile') ? <Outlet context={c} /> : <PendingPage company={c} />}
        </main>
      </div>
    </div>
  )
}

function CompanyCard({ company }: { company: Company }) {
  const status = STATUS[company.status] ?? STATUS.pending
  return (
    <div className="mt-6 flex items-center gap-3 rounded-2xl border border-line bg-card p-3.5">
      <span className="grid size-10 shrink-0 place-items-center rounded-xl bg-nile font-bold text-white">{initials(company.name)}</span>
      <div className="min-w-0">
        <p className="truncate text-[15px] font-bold">{company.name}</p>
        <span className={`mt-1 inline-block rounded-full px-2.5 py-0.5 text-[12px] font-semibold ${status.tone}`}>{status.label}</span>
      </div>
    </div>
  )
}
