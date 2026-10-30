import { Link } from 'react-router-dom'
import { useAuth } from '@/auth/AuthProvider'
import { homeFor } from '@/auth/tokens'
import { ButtonLink } from '@/components/ui/Button'
import { Icon, type IconName } from '@/components/ui/Icon'
import { Logo } from '@/components/ui/Logo'
import { HeroVisual } from './HeroVisual'

const FEATURES: { icon: IconName; title: string; text: string }[] = [
  { icon: 'spark', title: 'A plan in a minute', text: 'Built from your interests, budget and days.' },
  { icon: 'chat', title: 'Change it by asking', text: '“Cheaper”, “one more day” — and it tells you what changed.' },
  { icon: 'camera', title: 'Scan any monument', text: 'Its name and verified history in seconds.' },
]

export function WelcomePage() {
  const { session } = useAuth()

  return (
    <div className="min-h-dvh">
      <header className="flex h-[72px] items-center justify-between px-4 sm:px-10 lg:h-[88px] lg:px-20">
        <Logo />
        {session ? (
          <Link to={homeFor(session.role)} className="text-base font-bold text-terracotta hover:text-terracotta-strong">
            {session.role === 'traveler' ? 'My trips' : 'Dashboard'}
          </Link>
        ) : (
          <div className="flex items-center gap-6">
            <Link to="/partner/sign-up" className="hidden text-[15px] font-semibold text-ink-2 hover:text-ink sm:block">
              For travel companies
            </Link>
            <Link to="/sign-in" className="text-base font-bold text-terracotta hover:text-terracotta-strong">
              Sign in
            </Link>
          </div>
        )}
      </header>

      <main className="flex items-center justify-between gap-20 px-4 pt-6 pb-16 sm:px-10 lg:px-20 lg:pt-9">
        <div className="max-w-[640px] flex-1">
          <span className="inline-flex items-center gap-2 rounded-full bg-muted px-4 py-2 text-sm font-semibold text-terracotta-strong">
            <Icon name="spark" size={16} />
            AI trip planner for Egypt
          </span>
          <h1 className="mt-7 font-display text-[42px] leading-[1.05] tracking-[-0.02em] sm:text-[60px]">
            Tell us what you love. We’ll plan Egypt around it.
          </h1>
          <p className="mt-7 max-w-[600px] text-[17px] leading-relaxed text-ink-2 sm:text-[19px]">
            Egyptora turns your interests, budget and time into a day-by-day trip in about a minute. Change anything just by
            asking — and point your camera at a monument to hear its story.
          </p>
          <div className="mt-8 flex flex-wrap gap-3.5">
            <ButtonLink to="/plan/interests" size="lg" icon="arrowR">
              Start planning
            </ButtonLink>
            <ButtonLink to="/shared/sample" size="lg" variant="outline">
              See a sample trip
            </ButtonLink>
          </div>
          <p className="mt-9 text-sm text-ink-2">About a minute · No account needed to start</p>

          <div className="mt-9 grid gap-6 border-t border-line-divider pt-7 sm:grid-cols-3">
            {FEATURES.map((f) => (
              <div key={f.title}>
                <span className="grid size-10 place-items-center rounded-[10px] bg-muted text-terracotta">
                  <Icon name={f.icon} size={18} />
                </span>
                <h2 className="mt-4 text-base font-bold">{f.title}</h2>
                <p className="mt-2.5 text-sm leading-normal text-ink-3">{f.text}</p>
              </div>
            ))}
          </div>
        </div>
        <div className="hidden xl:block">
          <HeroVisual />
        </div>
      </main>
    </div>
  )
}
