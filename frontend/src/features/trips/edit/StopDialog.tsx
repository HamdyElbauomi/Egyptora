import { useState, type FormEvent } from 'react'
import { useUpdateItem, type TripItem } from '@/api/queries'
import { Button } from '@/components/ui/Button'
import { Dialog } from '@/components/ui/Dialog'
import { TextArea } from '@/components/ui/fields'
import { TextField } from '@/components/ui/TextField'
import { useToast } from '@/components/ui/Toast'
import { formatTime } from '@/lib/format'
import { itemTitle } from '../tripMath'

/** Change a stop's times, note or cost. */
export function StopDialog({ tripId, item, onClose }: { tripId: number; item: TripItem | null; onClose: () => void }) {
  return (
    <Dialog open={item !== null} onClose={onClose} title={item ? itemTitle(item) : ''} description="Change the time, a note or the cost.">
      {item && <StopForm key={item.id} tripId={tripId} item={item} onDone={onClose} />}
    </Dialog>
  )
}

function StopForm({ tripId, item, onDone }: { tripId: number; item: TripItem; onDone: () => void }) {
  const update = useUpdateItem(tripId)
  const toast = useToast()
  const [start, setStart] = useState(formatTime(item.start_time))
  const [end, setEnd] = useState(formatTime(item.end_time))
  const [note, setNote] = useState(item.note ?? '')
  const [cost, setCost] = useState(String(item.cost))
  const badTimes = Boolean(start && end && end <= start)

  const submit = (e: FormEvent) => {
    e.preventDefault()
    if (badTimes) return
    update.mutate(
      {
        itemId: item.id,
        body: {
          start_time: start ? `${start}:00` : null,
          end_time: end ? `${end}:00` : null,
          note: note.trim() || null,
          cost: cost === '' ? 0 : Math.max(0, Number(cost)),
        },
      },
      {
        onSuccess: () => {
          toast('Stop updated')
          onDone()
        },
        onError: (err) => toast(err.message, 'error'),
      },
    )
  }

  return (
    <form onSubmit={submit} className="flex flex-col gap-5">
      <div className="grid grid-cols-2 gap-4">
        <TextField label="Starts" type="time" value={start} onChange={(e) => setStart(e.target.value)} />
        <TextField
          label="Ends"
          type="time"
          value={end}
          onChange={(e) => setEnd(e.target.value)}
          error={badTimes ? 'Must be after the start' : undefined}
        />
      </div>
      <TextArea label="Note" placeholder="e.g. Book tickets online the day before" value={note} onChange={(e) => setNote(e.target.value)} maxLength={500} />
      <TextField label="Cost per person" prefix="EGP" inputMode="numeric" value={cost} onChange={(e) => setCost(e.target.value.replace(/\D/g, ''))} />
      <div className="flex justify-end gap-3">
        <Button variant="outline" onClick={onDone}>
          Cancel
        </Button>
        <Button type="submit" loading={update.isPending} disabled={badTimes}>
          Save changes
        </Button>
      </div>
    </form>
  )
}
