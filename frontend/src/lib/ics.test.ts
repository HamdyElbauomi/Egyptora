import { describe, expect, it } from 'vitest'
import { buildIcs } from './ics'

describe('buildIcs', () => {
  it('makes one all-day event per day and escapes text', () => {
    const ics = buildIcs(7, [{ date: '2026-11-30', title: 'Day 1 · Cairo', details: 'Pyramids, Sphinx\nHotel; Inn' }], new Date('2026-10-01T10:00:00Z'))
    expect(ics).toContain('DTSTART;VALUE=DATE:20261130')
    expect(ics).toContain('DTEND;VALUE=DATE:20261201')
    expect(ics).toContain('DESCRIPTION:Pyramids\\, Sphinx\\nHotel\\; Inn')
    expect(ics).toContain('DTSTAMP:20261001T100000Z')
    expect(ics.split('BEGIN:VEVENT')).toHaveLength(2)
    expect(ics.endsWith('END:VCALENDAR\r\n')).toBe(true)
  })
})
