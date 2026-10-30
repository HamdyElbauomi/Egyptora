import { useCallback } from 'react'
import { Link } from 'react-router-dom'
import { useScan } from '@/api/scans'
import { Button } from '@/components/ui/Button'
import { Icon } from '@/components/ui/Icon'
import { useToast } from '@/components/ui/Toast'
import { useOptionalTrip } from '../trips/TripLayout'
import { Camera } from './Camera'
import { PlacePanel } from './PlacePanel'

/** Point the camera at a monument: name, verified story, and questions answered from verified notes. */
export function ScanPage() {
  const trip = useOptionalTrip()
  const scan = useScan()
  const toast = useToast()
  const { mutate } = scan

  const onPhoto = useCallback(
    (photo: Blob) => mutate(photo, { onError: (err) => toast(err.message, 'error') }),
    [mutate, toast],
  )

  const result = scan.data
  return (
    <div className="grid gap-6 lg:grid-cols-[minmax(0,1fr)_440px] lg:gap-8">
      <Camera onPhoto={onPhoto} busy={scan.isPending} hint="Point at a monument, statue or inscription" />
      <section aria-live="polite" className="min-w-0">
        {!result ? (
          <Intro />
        ) : result.status === 'recognized' && result.place ? (
          <PlacePanel
            place={result.place}
            trip={trip}
            badge={
              <p className="flex flex-wrap items-center gap-2">
                <span className="inline-flex items-center gap-1.5 rounded-full bg-nile-soft px-3 py-1 text-sm font-semibold text-nile-strong">
                  <Icon name="check" size={15} /> Recognized
                </span>
                <span className="text-sm text-ink-3">{Math.round(result.confidence * 100)}% sure</span>
              </p>
            }
          />
        ) : (
          <NotSure message={result.message} />
        )}
      </section>
    </div>
  )
}

function Intro() {
  return (
    <div className="rounded-[22px] border border-line bg-card p-6">
      <span className="grid size-12 place-items-center rounded-2xl bg-terracotta-soft text-terracotta">
        <Icon name="camera" size={24} />
      </span>
      <h1 className="mt-4 font-display text-[30px] leading-tight">Scan a monument</h1>
      <p className="mt-2 text-[15px] leading-relaxed text-ink-2">
        Take a photo, or choose one from your phone. We’ll tell you what it is, its verified story, and answer your
        questions about it.
      </p>
      <ul className="mt-5 space-y-2.5 text-[15px] text-ink-2">
        {['Fill the frame with the monument', 'Daylight works best', 'Front views are easier than close-ups'].map((tip) => (
          <li key={tip} className="flex items-center gap-2.5">
            <Icon name="check" size={16} className="text-nile" />
            {tip}
          </li>
        ))}
      </ul>
      <Link to="/scans" className="mt-6 inline-flex items-center gap-1.5 text-[15px] font-bold text-terracotta hover:text-terracotta-strong">
        <Icon name="history" size={16} /> My earlier scans
      </Link>
    </div>
  )
}

function NotSure({ message }: { message: string }) {
  return (
    <div className="rounded-[22px] border border-line bg-card p-6">
      <span className="grid size-12 place-items-center rounded-2xl bg-gold-soft text-warning">
        <Icon name="alert" size={24} />
      </span>
      <h1 className="mt-4 font-display text-[28px] leading-tight">We’re not sure what this is</h1>
      <p className="mt-2 text-[15px] leading-relaxed text-ink-2">{message}</p>
      <p className="mt-3 text-sm text-ink-3">Our team looks at photos we couldn’t recognize, so the app gets better at them.</p>
      <Button className="mt-5" variant="outline" leadingIcon="camera" onClick={() => window.scrollTo({ top: 0, behavior: 'smooth' })}>
        Try another photo
      </Button>
    </div>
  )
}
