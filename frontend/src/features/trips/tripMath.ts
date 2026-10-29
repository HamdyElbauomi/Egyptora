import type { TripDay, TripItem } from '@/api/queries'

/** "09:00:00" → minutes after midnight */
export function minutes(time: string | null | undefined): number | null {
  if (!time) return null
  const [h, m] = time.split(':').map(Number)
  return h * 60 + m
}

/** 45 → "45 min", 90 → "1.5 h", 180 → "3 h" */
export function formatDuration(total: number): string {
  if (total < 60) return `${total} min`
  const hours = Math.round((total / 60) * 2) / 2
  return `${hours} h`
}

export function itemDuration(item: TripItem): string | null {
  const start = minutes(item.start_time)
  const end = minutes(item.end_time)
  return start !== null && end !== null && end > start ? formatDuration(end - start) : null
}

/** Free minutes between one stop's end and the next stop's start. */
export function gapAfter(item: TripItem, next: TripItem | undefined): number | null {
  const end = minutes(item.end_time)
  const start = minutes(next?.start_time)
  return end !== null && start !== null && start > end ? start - end : null
}

export interface CostBreakdown {
  hotels: number
  nights: number
  tickets: number
  other: number
  total: number
}

export function costBreakdown(itinerary: TripDay[], total: number): CostBreakdown {
  let hotels = 0
  let nights = 0
  let tickets = 0
  for (const day of itinerary) {
    if (day.hotel) {
      hotels += day.hotel.price_per_night
      nights += 1
    }
    for (const item of day.items) tickets += item.cost
  }
  return { hotels, nights, tickets, other: Math.max(0, total - hotels - tickets), total }
}

/** "Cairo → Luxor" in visiting order, one entry per stay. */
export function route(itinerary: TripDay[]): string {
  const names: string[] = []
  for (const day of itinerary) if (names[names.length - 1] !== day.city_name) names.push(day.city_name)
  return names.join(' → ')
}


export const TYPE_LABEL: Record<string, string> = { visit: 'Visit', meal: 'Meal', transport: 'Travel', free_time: 'Free time' }

export function itemTitle(item: TripItem): string {
  return item.place_name ?? item.note ?? TYPE_LABEL[item.type] ?? 'Stop'
}

/** The nights in a row spent in the same city as `day` (the stay this night belongs to). */
export function stayOf(itinerary: TripDay[], day: TripDay): TripDay[] {
  const days = itinerary
  let start = days.findIndex((d) => d.id === day.id)
  let end = start
  while (start > 0 && days[start - 1].city_id === day.city_id) start--
  while (end < days.length - 1 && days[end + 1].city_id === day.city_id) end++
  return days.slice(start, end + 1)
}
