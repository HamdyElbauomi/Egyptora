import { useEffect, useMemo, useRef, useState, type FormEvent, type KeyboardEvent } from 'react'
import { useDecideChange, useMessages, useSendMessage, type ChatMessage, type Trip, type TripChange } from '@/api/queries'
import logo from '@/assets/logo.svg'
import { Button, ButtonLink } from '@/components/ui/Button'
import { ErrorState } from '@/components/ui/ErrorState'
import { Icon } from '@/components/ui/Icon'
import { PageLoader } from '@/components/ui/Spinner'
import { useToast } from '@/components/ui/Toast'
import { formatEgp, formatNumber } from '@/lib/format'
import { itemTitle } from '../trips/tripMath'
import { useCurrentTrip } from '../trips/TripLayout'

/** Change the trip by asking. Each proposed change waits for Keep or Undo. */
export function ChatPage() {
  const trip = useCurrentTrip()
  const messages = useMessages(trip.id)
  const send = useSendMessage(trip.id)
  const toast = useToast()
  const [text, setText] = useState('')
  const [pending, setPending] = useState<string | null>(null)
  const end = useRef<HTMLDivElement>(null)

  const list = useMemo(() => messages.data ?? [], [messages.data])
  const latest = [...list].reverse().find((m) => m.change)?.change ?? null

  useEffect(() => {
    end.current?.scrollIntoView({ behavior: 'smooth', block: 'end' })
  }, [list.length, pending])

  const ask = (content: string) => {
    const message = content.trim()
    if (!message || send.isPending) return
    setPending(message)
    setText('')
    send.mutate(message, {
      onError: (err) => {
        toast(err.message, 'error')
        setText(message)
      },
      onSettled: () => setPending(null),
    })
  }

  const submit = (e: FormEvent) => {
    e.preventDefault()
    ask(text)
  }

  const onKey = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      ask(text)
    }
  }

  return (
    <div className="grid gap-8 lg:grid-cols-[minmax(0,1fr)_380px]">
      <section aria-label="Chat" className="flex min-h-[calc(100dvh-160px)] min-w-0 flex-col">
        <MobileTotal trip={trip} change={latest} />
        <div className="flex-1">
          {messages.isPending ? (
            <PageLoader label="Loading the conversation…" />
          ) : messages.isError ? (
            <ErrorState title="We couldn’t load the chat" action={<Button onClick={() => messages.refetch()}>Try again</Button>} />
          ) : list.length === 0 && !pending ? (
            <Welcome title={trip.title} />
          ) : (
            <ol className="flex flex-col gap-6 pb-6">
              {list.map((m) => (
                <li key={m.id}>{m.role === 'user' ? <UserBubble text={m.content} /> : <AssistantMessage tripId={trip.id} message={m} />}</li>
              ))}
              {pending && (
                <>
                  <li>
                    <UserBubble text={pending} />
                  </li>
                  <li className="flex items-start gap-3.5">
                    <Avatar />
                    <p className="flex items-center gap-2.5 rounded-2xl border border-line bg-card px-4 py-3 text-[15px] text-ink-2">
                      <span className="flex gap-1" aria-hidden>
                        <span className="size-1.5 animate-bounce rounded-full bg-terracotta" />
                        <span className="size-1.5 animate-bounce rounded-full bg-gold [animation-delay:120ms]" />
                        <span className="size-1.5 animate-bounce rounded-full bg-nile [animation-delay:240ms]" />
                      </span>
                      Working on your trip…
                    </p>
                  </li>
                </>
              )}
            </ol>
          )}
          <div ref={end} />
        </div>

        <div className="sticky bottom-0 -mx-4 bg-canvas/95 px-4 pt-3 pb-4 backdrop-blur sm:mx-0 sm:px-0">
          <div className="mb-3 flex gap-2 overflow-x-auto pb-1">
            {suggestions(trip).map((s) => (
              <button
                key={s}
                type="button"
                onClick={() => ask(s)}
                disabled={send.isPending}
                className="shrink-0 rounded-full border-[1.5px] border-line-strong bg-card px-4 py-2 text-[15px] font-medium hover:border-line-muted disabled:opacity-50"
              >
                {s}
              </button>
            ))}
          </div>
          <form onSubmit={submit} className="flex items-end gap-2 rounded-[18px] border-[1.5px] border-terracotta bg-card p-2 pl-4">
            <label htmlFor="chat-input" className="sr-only">
              Ask for any change
            </label>
            <textarea
              id="chat-input"
              rows={1}
              value={text}
              onChange={(e) => setText(e.target.value)}
              onKeyDown={onKey}
              maxLength={1000}
              placeholder="Ask for any change…"
              className="max-h-40 min-h-11 flex-1 resize-none bg-transparent py-2.5 text-base outline-none placeholder:text-ink-4"
            />
            <button
              type="submit"
              aria-label="Send"
              disabled={!text.trim() || send.isPending}
              className="grid size-11 shrink-0 place-items-center rounded-xl bg-terracotta text-white hover:bg-terracotta-strong disabled:opacity-40"
            >
              <Icon name="send" size={20} />
            </button>
          </form>
        </div>
      </section>

      <LivePanel trip={trip} change={latest} />
    </div>
  )
}

/** Quick asks the rule-based agent understands, filled in with this trip's own days and cities. */
function suggestions(trip: Trip): string[] {
  const busiest = [...trip.itinerary].sort((a, b) => b.items.length - a.items.length)[0]
  const firstCity = trip.itinerary[0]?.city_name
  const lastCity = trip.itinerary[trip.itinerary.length - 1]?.city_name
  return [
    busiest ? `Make day ${busiest.day_number} lighter` : null,
    firstCity ? `Cheaper hotel in ${firstCity}` : null,
    lastCity ? `Better hotel in ${lastCity}` : null,
  ].filter((s): s is string => Boolean(s))
}

function Avatar() {
  return <img src={logo} alt="" width={36} height={36} className="shrink-0 rounded-[10px]" />
}

function UserBubble({ text }: { text: string }) {
  return (
    <p className="ml-auto w-fit max-w-[85%] rounded-[18px] rounded-br-md bg-terracotta px-[18px] py-3 text-base whitespace-pre-wrap text-white">
      {text}
    </p>
  )
}

function AssistantMessage({ tripId, message }: { tripId: number; message: ChatMessage }) {
  return (
    <div className="flex items-start gap-3.5">
      <Avatar />
      <div className="min-w-0 flex-1">
        <p className="pt-1.5 text-base leading-relaxed whitespace-pre-wrap">{message.content}</p>
        {message.change && <ChangeCard tripId={tripId} change={message.change} />}
      </div>
    </div>
  )
}

function Delta({ amount }: { amount: number }) {
  if (amount === 0) return <span className="font-bold text-ink-3">±0</span>
  return (
    <span className={`font-bold tabular-nums ${amount < 0 ? 'text-nile' : 'text-terracotta'}`}>
      {amount < 0 ? '−' : '+'}
      {formatNumber(Math.abs(amount))}
    </span>
  )
}

function ChangeCard({ tripId, change }: { tripId: number; change: TripChange }) {
  const decide = useDecideChange(tripId)
  const toast = useToast()
  const act = (decision: 'keep' | 'undo') =>
    decide.mutate(
      { changeId: change.id, decision },
      {
        onSuccess: ({ change: c }) => toast(c.status === 'kept' ? 'Change kept' : 'Change undone'),
        onError: (err) => toast(err.message, 'error'),
      },
    )
  const days = change.day_numbers.length ? `Day ${change.day_numbers.join(', ')}` : null

  return (
    <div className="mt-3 max-w-[620px]">
      <div className={`rounded-[18px] border bg-card ${change.status === 'undone' ? 'border-line opacity-60' : 'border-line'}`}>
        <div className="flex items-start gap-3.5 p-4">
          <span className="grid size-9 shrink-0 place-items-center rounded-[10px] bg-nile-soft text-nile">
            <Icon name="edit" size={18} />
          </span>
          <div className="min-w-0 flex-1">
            <p className={`font-bold ${change.status === 'undone' ? 'line-through' : ''}`}>{change.summary}</p>
            {change.explanation && <p className="mt-1 text-[15px] text-ink-2">{change.explanation}</p>}
            {days && <p className="mt-1 text-[13px] text-ink-3">{days}</p>}
          </div>
          <Delta amount={change.cost_delta} />
        </div>
      </div>
      <div className="mt-3 flex flex-wrap items-center gap-2.5">
        {change.status === 'proposed' && (
          <>
            <button
              type="button"
              onClick={() => act('keep')}
              disabled={decide.isPending}
              className="inline-flex items-center gap-2 rounded-xl bg-nile px-5 py-3 text-[15px] font-bold text-white hover:bg-nile-strong disabled:opacity-50"
            >
              <Icon name="check" size={18} />
              Keep changes
            </button>
            <Button variant="outline" size="sm" className="!py-3" onClick={() => act('undo')} disabled={decide.isPending}>
              Undo
            </Button>
          </>
        )}
        {change.status === 'kept' && (
          <>
            <span className="inline-flex items-center gap-1.5 rounded-full bg-nile-soft px-3 py-1.5 text-sm font-semibold text-nile-strong">
              <Icon name="check" size={15} /> Kept
            </span>
            <Button variant="ghost" onClick={() => act('undo')} disabled={decide.isPending}>
              Undo
            </Button>
          </>
        )}
        {change.status === 'undone' && <span className="text-sm font-semibold text-ink-3">Undone — your trip is as it was.</span>}
      </div>
    </div>
  )
}

function Welcome({ title }: { title: string }) {
  return (
    <div className="flex items-start gap-3.5 pt-2">
      <Avatar />
      <div className="pt-1.5">
        <p className="text-base leading-relaxed">
          Hi! Ask me to change <strong>{title}</strong> in plain words — a cheaper hotel, a lighter day, a place to add or
          remove. I’ll show you exactly what changes and what it costs before anything is kept.
        </p>
      </div>
    </div>
  )
}

function LivePanel({ trip, change }: { trip: Trip; change: TripChange | null }) {
  const pending = change?.status === 'proposed' ? change : null
  const changed = new Set(change && change.status !== 'undone' ? change.day_numbers : [])

  return (
    <aside className="hidden lg:block">
      <div className="sticky top-[96px] flex max-h-[calc(100dvh-120px)] flex-col">
        <div className="flex items-center justify-between">
          <h2 className="font-display text-[26px]">Your trip, live</h2>
          {change?.status === 'kept' && (
            <span className="rounded-full bg-nile-soft px-3 py-1 text-[13px] font-semibold text-nile-strong">Updated</span>
          )}
        </div>
        <div className="mt-4 rounded-[20px] border border-line bg-card p-5">
          <p className="text-[15px] text-ink-2">Per person</p>
          <p className="mt-1 font-display text-[34px] leading-none">{formatEgp(trip.total_cost)}</p>
          {pending && pending.cost_delta !== 0 && (
            <p className="mt-3 inline-block rounded-full bg-gold-soft px-3 py-1 text-[13px] font-semibold text-warning">
              {formatEgp(trip.total_cost + pending.cost_delta)} if you keep the change
            </p>
          )}
          {trip.budget_total !== null && trip.budget_total !== undefined && (
            <p className={`mt-3 text-sm font-semibold ${trip.over_budget ? 'text-terracotta' : 'text-nile'}`}>
              {trip.over_budget
                ? `${formatEgp(trip.total_cost - trip.budget_total)} over your budget`
                : `${formatEgp(trip.budget_total - trip.total_cost)} under your budget`}
            </p>
          )}
        </div>
        <ol className="mt-4 flex min-h-0 flex-col gap-2 overflow-y-auto">
          {trip.itinerary.map((d) => {
            const isChanged = changed.has(d.day_number)
            return (
              <li
                key={d.id}
                className={`flex items-center gap-4 rounded-2xl border px-4 py-3 ${isChanged ? 'border-gold/40 bg-gold-soft' : 'border-line bg-card'}`}
              >
                <span className="w-11 shrink-0 text-sm font-semibold text-ink-2">Day {d.day_number}</span>
                <span className="min-w-0 flex-1">
                  <span className="block font-bold">{d.city_name}</span>
                  <span className="block truncate text-[13px] text-ink-2">
                    {d.items.length ? d.items.map(itemTitle).join(', ') : 'Free day'}
                  </span>
                </span>
                {isChanged && <span className="shrink-0 text-[13px] font-bold text-warning">{pending ? 'Changing' : 'Changed'}</span>}
              </li>
            )
          })}
        </ol>
        <ButtonLink to={`/trips/${trip.id}`} variant="outline" icon="arrowR" className="mt-4 w-full">
          View full plan
        </ButtonLink>
      </div>
    </aside>
  )
}

function MobileTotal({ trip, change }: { trip: Trip; change: TripChange | null }) {
  const pending = change?.status === 'proposed' ? change : null
  return (
    <div className="mb-5 flex items-center justify-between rounded-2xl border border-line bg-card px-4 py-3 lg:hidden">
      <div>
        <p className="text-[13px] text-ink-3">Per person</p>
        <p className="text-lg font-bold">{formatEgp(trip.total_cost)}</p>
      </div>
      {pending && pending.cost_delta !== 0 && (
        <p className="text-sm text-ink-2">
          Change: <Delta amount={pending.cost_delta} />
        </p>
      )}
    </div>
  )
}
