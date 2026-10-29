import { useState, type FormEvent } from 'react'
import { useUpdateTrip, type Trip } from '@/api/queries'
import { Button } from '@/components/ui/Button'
import { Dialog } from '@/components/ui/Dialog'
import { TextField } from '@/components/ui/TextField'
import { useToast } from '@/components/ui/Toast'
import { plural } from '@/lib/format'
import { MAX_DAYS, MIN_DAYS } from '../../plan/draft'

/** Title, start date, number of days and budget. */
export function TripDetailsDialog({ trip, open, onClose }: { trip: Trip; open: boolean; onClose: () => void }) {
  return (
    <Dialog open={open} onClose={onClose} title="Trip details">
      {open && <DetailsForm trip={trip} onDone={onClose} />}
    </Dialog>
  )
}

function DetailsForm({ trip, onDone }: { trip: Trip; onDone: () => void }) {
  const update = useUpdateTrip(trip.id)
  const toast = useToast()
  const [title, setTitle] = useState(trip.title)
  const [start, setStart] = useState(trip.start_date ?? '')
  const [days, setDays] = useState(String(trip.days))
  const [budget, setBudget] = useState(trip.budget_total ? String(trip.budget_total) : '')
  const dayCount = Number(days)
  const badDays = !Number.isInteger(dayCount) || dayCount < MIN_DAYS || dayCount > MAX_DAYS

  const submit = (e: FormEvent) => {
    e.preventDefault()
    if (badDays || !title.trim()) return
    update.mutate(
      {
        title: title.trim(),
        start_date: start || null,
        days: dayCount,
        budget_total: budget ? Number(budget) : null,
      },
      {
        onSuccess: () => {
          toast('Trip updated')
          onDone()
        },
        onError: (err) => toast(err.message, 'error'),
      },
    )
  }

  return (
    <form onSubmit={submit} className="flex flex-col gap-5">
      <TextField label="Title" required maxLength={160} value={title} onChange={(e) => setTitle(e.target.value)} />
      <div className="grid grid-cols-2 gap-4">
        <TextField label="Start date" type="date" value={start} onChange={(e) => setStart(e.target.value)} />
        <TextField
          label="Days"
          type="number"
          min={MIN_DAYS}
          max={MAX_DAYS}
          value={days}
          onChange={(e) => setDays(e.target.value)}
          error={badDays ? `${MIN_DAYS} to ${MAX_DAYS} days` : undefined}
        />
      </div>
      {!badDays && dayCount !== trip.days && (
        <p className="rounded-xl bg-gold-soft px-4 py-3 text-sm text-warning">
          {dayCount < trip.days
            ? `The last ${plural(trip.days - dayCount, 'day')} and their stops will be removed.`
            : `${plural(dayCount - trip.days, 'empty day')} will be added in the last city. Fill them by hand or ask in chat.`}
        </p>
      )}
      <TextField
        label="Budget per person (optional)"
        prefix="EGP"
        inputMode="numeric"
        value={budget}
        onChange={(e) => setBudget(e.target.value.replace(/\D/g, ''))}
        hint="We’ll warn you when the trip goes over it."
      />
      <div className="flex justify-end gap-3">
        <Button variant="outline" onClick={onDone}>
          Cancel
        </Button>
        <Button type="submit" loading={update.isPending} disabled={badDays || !title.trim()}>
          Save
        </Button>
      </div>
    </form>
  )
}
