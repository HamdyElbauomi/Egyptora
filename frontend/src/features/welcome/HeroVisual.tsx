import { Icon } from '@/components/ui/Icon'
import pattern from '@/assets/pattern-mashrabiya.svg'

const STOPS = [
  { time: '06:30', name: 'Karnak Temple', dot: 'bg-terracotta' },
  { time: '12:30', name: 'Lunch on the Corniche', dot: 'bg-gold' },
  { time: '17:30', name: 'Luxor Temple at sunset', dot: 'bg-nile' },
]

/** The Welcome screen's illustration: a day plan, a chat change and a recognised monument. */
export function HeroVisual() {
  return (
    <div
      aria-hidden
      className="relative h-[640px] w-[560px] shrink-0 overflow-hidden rounded-[32px] bg-terracotta"
      style={{ backgroundImage: `url("${pattern}")`, backgroundSize: '560px 640px' }}
    >
      <div className="absolute -top-[60px] left-[400px] size-[220px] rounded-full bg-gold" />

      <div className="absolute top-14 left-12 w-[330px] rounded-3xl bg-card p-[22px] shadow-[0_18px_40px_rgba(31,26,23,0.18)]">
        <div className="flex items-center justify-between">
          <p className="font-display text-xl">Day 2 · Luxor</p>
          <span className="rounded-full bg-nile-soft px-2.5 py-1 text-[13px] font-semibold text-nile-strong">3 stops</span>
        </div>
        <ul className="mt-3.5 space-y-2.5">
          {STOPS.map((s) => (
            <li key={s.time} className="flex items-center gap-4 text-[15px]">
              <span className="w-11 text-[13px] font-semibold text-ink-3 tabular-nums">{s.time}</span>
              <span className={`size-2 rounded-full ${s.dot}`} />
              <span className="font-medium">{s.name}</span>
            </li>
          ))}
        </ul>
      </div>

      <div className="absolute top-[292px] right-10 w-[320px] rounded-3xl bg-card p-[18px] shadow-[0_18px_40px_rgba(31,26,23,0.18)]">
        <p className="ml-auto w-fit rounded-xl bg-terracotta px-3.5 py-2.5 text-[15px] font-semibold text-white">
          Make it cheaper
        </p>
        <p className="mt-3 rounded-xl bg-bubble px-3.5 py-3 text-[15px] leading-snug">
          Done — saved EGP 3,800. Here’s what changed and why.
        </p>
      </div>

      <div className="absolute top-[520px] left-12 flex items-center gap-3.5 rounded-full bg-inverse py-3.5 pr-6 pl-3.5 shadow-[0_18px_40px_rgba(31,26,23,0.25)]">
        <span className="grid size-11 place-items-center rounded-full bg-gold text-ink">
          <Icon name="camera" size={22} />
        </span>
        <span>
          <span className="block text-base font-bold text-on-dark">Karnak Temple</span>
          <span className="block text-[13px] text-on-dark-muted">Recognized · tap to learn more</span>
        </span>
      </div>
    </div>
  )
}
