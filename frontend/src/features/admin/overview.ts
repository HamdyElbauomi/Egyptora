import type { Stats } from '@/api/admin'

export function pct(rate: number | null | undefined): string {
  return rate === null || rate === undefined ? '—' : `${Math.round(rate * 100)}%`
}

/** The three AI rates averaged, ignoring the ones with no data yet. */
export function aiSuccess(ai: Stats['ai']): number | null {
  const rates = [ai.search_success_rate, ai.scan_recognition_rate, ai.chat_keep_rate].filter((r): r is number => r !== null && r !== undefined)
  return rates.length ? rates.reduce((a, b) => a + b, 0) / rates.length : null
}

export function reportCsv(s: Stats): string {
  const rows: [string, string | number][] = [
    ['Travelers', s.users.travelers],
    ['Company accounts', s.users.company_accounts],
    ['New users (7 days)', s.users.new_last_7_days],
    ['Trips', s.trips.total],
    ['Trips saved', s.trips.saved],
    ['Trips shared', s.trips.shared],
    ['Trips created (7 days)', s.trips.created_last_7_days],
    ['Average trip days', s.trips.avg_days ?? ''],
    ['Average trip cost (EGP)', s.trips.avg_total_cost ?? ''],
    ['Companies approved', s.companies.approved],
    ['Companies pending', s.companies.pending],
    ['Live offers', s.offers.active],
    ['Nights booked in trips', s.offers.nights_booked_in_trips],
    ['Reviews', s.reviews.total],
    ['Average rating', s.reviews.average_rating ?? ''],
    ['Hotel search success', s.ai.search_success_rate ?? ''],
    ['Scan recognition rate', s.ai.scan_recognition_rate ?? ''],
    ['Chat keep rate', s.ai.chat_keep_rate ?? ''],
    ...s.trips.per_day.map((d) => [`Trips on ${d.date}`, d.trips] as [string, number]),
    ...s.top_destinations.map((c) => [`Trips visiting ${c.city_name}`, c.trips] as [string, number]),
  ]
  return ['metric,value', ...rows.map(([k, v]) => `"${k}",${v}`)].join('\n') + '\n'
}

