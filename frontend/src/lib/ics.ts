/** Builds an iCalendar file with one all-day event per trip day. */

export interface CalendarDay {
  date: string // yyyy-mm-dd
  title: string
  details: string
}

function escape(text: string): string {
  return text.replace(/\\/g, '\\\\').replace(/;/g, '\\;').replace(/,/g, '\\,').replace(/\r?\n/g, '\\n')
}

function compact(date: string): string {
  return date.replace(/-/g, '')
}

function nextDay(date: string): string {
  const d = new Date(`${date}T00:00:00Z`)
  d.setUTCDate(d.getUTCDate() + 1)
  return d.toISOString().slice(0, 10)
}

export function buildIcs(tripId: number, days: CalendarDay[], now = new Date()): string {
  const stamp = now.toISOString().replace(/[-:]/g, '').replace(/\.\d{3}/, '')
  const events = days.flatMap((day, i) => [
    'BEGIN:VEVENT',
    `UID:egyptora-${tripId}-${i + 1}@egyptora.app`,
    `DTSTAMP:${stamp}`,
    `DTSTART;VALUE=DATE:${compact(day.date)}`,
    `DTEND;VALUE=DATE:${compact(nextDay(day.date))}`,
    `SUMMARY:${escape(day.title)}`,
    `DESCRIPTION:${escape(day.details)}`,
    'END:VEVENT',
  ])
  return ['BEGIN:VCALENDAR', 'VERSION:2.0', 'PRODID:-//Egyptora//Trip planner//EN', 'CALSCALE:GREGORIAN', ...events, 'END:VCALENDAR', ''].join('\r\n')
}

export function downloadFile(name: string, content: string, type: string): void {
  const url = URL.createObjectURL(new Blob([content], { type }))
  const a = document.createElement('a')
  a.href = url
  a.download = name
  a.click()
  setTimeout(() => URL.revokeObjectURL(url), 1000)
}
