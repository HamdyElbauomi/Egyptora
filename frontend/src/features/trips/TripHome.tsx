import { useState } from 'react'
import { useLocation, useNavigate, useSearchParams } from 'react-router-dom'
import {
  useDeleteItem,
  useDeleteTrip,
  useInterests,
  useRegenerateTrip,
  useReorderDay,
  type TripDay,
  type TripItem,
} from '@/api/queries'
import { Button, ButtonLink } from '@/components/ui/Button'
import { Chip } from '@/components/ui/Chip'
import { Icon } from '@/components/ui/Icon'
import { Menu } from '@/components/ui/Menu'
import { useToast } from '@/components/ui/Toast'
import { AddStopDialog } from './edit/AddStopDialog'
import { ConfirmDialog } from './edit/ConfirmDialog'
import { HotelDialog } from './edit/HotelDialog'
import { StopDialog } from './edit/StopDialog'
import { TripDetailsDialog } from './edit/TripDetailsDialog'
import { useCurrentTrip } from './TripLayout'
import { itemTitle } from './tripMath'
import { TripView } from './TripView'

/** "My trip": the day-by-day plan, editable by hand. */
export function TripHome() {
  const trip = useCurrentTrip()
  const navigate = useNavigate()
  const toast = useToast()
  const fresh = Boolean((useLocation().state as { fresh?: boolean } | null)?.fresh)
  const [params, setParams] = useSearchParams()
  const dayNumber = Number(params.get('day')) || 1
  const interests = useInterests().data ?? []

  const [editing, setEditing] = useState<TripItem | null>(null)
  const [addingTo, setAddingTo] = useState<TripDay | null>(null)
  const [hotelFor, setHotelFor] = useState<TripDay | null>(null)
  const [details, setDetails] = useState(false)
  const [confirm, setConfirm] = useState<'regenerate' | 'delete' | null>(null)

  const remove = useDeleteItem(trip.id)
  const reorder = useReorderDay(trip.id)
  const regenerate = useRegenerateTrip(trip.id)
  const deleteTrip = useDeleteTrip()

  const names = trip.interest_ids.map((id) => interests.find((i) => i.id === id)?.name).filter(Boolean)
  const busy = remove.isPending || reorder.isPending

  const move = (day: TripDay, index: number, by: -1 | 1) => {
    const ids = day.items.map((i) => i.id)
    ;[ids[index], ids[index + by]] = [ids[index + by], ids[index]]
    reorder.mutate({ dayId: day.id, itemIds: ids }, { onError: (err) => toast(err.message, 'error') })
  }

  const removeItem = (item: TripItem) =>
    remove.mutate(item.id, {
      onSuccess: () => toast(`${itemTitle(item)} removed`),
      onError: (err) => toast(err.message, 'error'),
    })

  return (
    <>
      {fresh && (
        <p className="mb-6 flex items-center gap-3 rounded-2xl bg-nile-soft px-5 py-3.5 text-[15px] text-nile-strong">
          <Icon name="check" size={18} />
          Your trip is ready. It’s a suggestion — change anything by hand or by asking in chat.
        </p>
      )}
      <TripView
        trip={trip}
        eyebrow={trip.status === 'saved' ? 'Saved trip' : 'Suggested for you'}
        chips={names.length > 0 && <Chip icon="spark">{names.join(' · ')}</Chip>}
        dayNumber={dayNumber}
        onDayChange={(n) => setParams({ day: String(n) }, { replace: true })}
        actions={
          <>
            <ButtonLink to={`/trips/${trip.id}/chat`} leadingIcon="chat">
              Adjust with chat
            </ButtonLink>
            <Menu
              label="Trip options"
              actions={[
                { label: 'Edit trip details', icon: 'edit', onSelect: () => setDetails(true) },
                { label: 'See the summary', icon: 'list', onSelect: () => navigate(`/trips/${trip.id}/summary`) },
                { label: 'Make a new version', icon: 'flip', onSelect: () => setConfirm('regenerate') },
                { label: 'Delete trip', icon: 'x', danger: true, onSelect: () => setConfirm('delete') },
              ]}
            />
          </>
        }
        stopActions={(item, day, index) => (
          <Menu
            label={`Options for ${itemTitle(item)}`}
            actions={[
              { label: 'Edit time, note or cost', icon: 'edit', onSelect: () => setEditing(item) },
              { label: 'Move earlier', icon: 'arrowL', disabled: index === 0 || busy, onSelect: () => move(day, index, -1) },
              { label: 'Move later', icon: 'arrowR', disabled: index === day.items.length - 1 || busy, onSelect: () => move(day, index, 1) },
              { label: 'Remove', icon: 'x', danger: true, disabled: busy, onSelect: () => removeItem(item) },
            ]}
          />
        )}
        dayFooter={(day) => (
          <Button size="sm" variant="outline" leadingIcon="plus" onClick={() => setAddingTo(day)}>
            Add a stop
          </Button>
        )}
        hotelAction={(day) => (
          <Button variant="ghost" onClick={() => setHotelFor(day)}>
            {day.hotel ? 'Change' : 'Choose'}
          </Button>
        )}
      />

      <StopDialog tripId={trip.id} item={editing} onClose={() => setEditing(null)} />
      <AddStopDialog trip={trip} day={addingTo} onClose={() => setAddingTo(null)} />
      <HotelDialog trip={trip} day={hotelFor} onClose={() => setHotelFor(null)} />
      <TripDetailsDialog trip={trip} open={details} onClose={() => setDetails(false)} />
      <ConfirmDialog
        open={confirm === 'regenerate'}
        onClose={() => setConfirm(null)}
        title="Make a new version?"
        confirmLabel="Make a new version"
        busy={regenerate.isPending}
        onConfirm={() =>
          regenerate.mutate(undefined, {
            onSuccess: () => {
              setConfirm(null)
              setParams({}, { replace: true })
              toast('Here’s a new version of your trip')
            },
            onError: (err) => toast(err.message, 'error'),
          })
        }
      >
        We’ll plan the days again with the same interests, cities, days and budget. Changes you made by hand will be replaced.
      </ConfirmDialog>
      <ConfirmDialog
        open={confirm === 'delete'}
        onClose={() => setConfirm(null)}
        title="Delete this trip?"
        confirmLabel="Delete trip"
        busy={deleteTrip.isPending}
        onConfirm={() =>
          deleteTrip.mutate(trip.id, {
            onSuccess: () => {
              toast('Trip deleted')
              navigate('/trips', { replace: true })
            },
            onError: (err) => toast(err.message, 'error'),
          })
        }
      >
        “{trip.title}” and its chat will be removed. This can’t be undone.
      </ConfirmDialog>
    </>
  )
}
