const egp = new Intl.NumberFormat('en-US', { maximumFractionDigits: 0 })

export function formatEgp(amount: number): string {
  return `EGP ${egp.format(amount)}`
}

export function formatNumber(amount: number): string {
  return egp.format(amount)
}

/** "09:00:00" → "09:00" */
export function formatTime(time: string | null | undefined): string {
  return time ? time.slice(0, 5) : ''
}

const shortDate = new Intl.DateTimeFormat('en-GB', { day: 'numeric', month: 'short', timeZone: 'UTC' })
const longDate = new Intl.DateTimeFormat('en-GB', { day: 'numeric', month: 'short', year: 'numeric', timeZone: 'UTC' })

/** "2026-11-11" → "11 Nov" (or "11 Nov 2026" with year) */
export function formatDate(date: string | null | undefined, withYear = false): string {
  if (!date) return ''
  const d = new Date(`${date}T00:00:00Z`)
  return (withYear ? longDate : shortDate).format(d)
}

export function formatDateRange(start: string | null | undefined, end: string | null | undefined): string {
  if (!start) return ''
  if (!end || end === start) return formatDate(start, true)
  return `${formatDate(start)} – ${formatDate(end, true)}`
}

export function plural(count: number, one: string, many = `${one}s`): string {
  return `${count} ${count === 1 ? one : many}`
}
