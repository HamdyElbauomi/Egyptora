import { describe, expect, it } from 'vitest'
import type { TripDay, TripItem } from '@/api/queries'
import { costBreakdown, formatDuration, gapAfter, itemDuration, route, stayOf } from './tripMath'

const item = (start: string, end: string, cost = 0): TripItem => ({
  id: 1, place_id: 1, place_name: 'X', place_image_url: null, type: 'visit',
  start_time: start, end_time: end, note: null, cost, position: 0,
})

const day = (n: number, city: string, items: TripItem[], price?: number): TripDay => ({
  id: n, day_number: n, date: null, city_id: 1, city_name: city, title: null, items, day_cost: 0,
  hotel: price === undefined ? null : {
    offer_id: 1, hotel_id: 1, hotel_name: 'H', stars: 3, company_id: 1, company_name: 'C',
    room_type: 'Double', price_per_night: price, free_cancellation: false, breakfast_included: false,
  },
})

describe('trip math', () => {
  it('formats durations', () => {
    expect(formatDuration(45)).toBe('45 min')
    expect(formatDuration(90)).toBe('1.5 h')
    expect(itemDuration(item('09:00:00', '12:00:00'))).toBe('3 h')
  })

  it('finds the gap between stops', () => {
    expect(gapAfter(item('09:00:00', '12:00:00'), item('12:30:00', '13:00:00'))).toBe(30)
    expect(gapAfter(item('09:00:00', '12:00:00'), undefined)).toBeNull()
  })

  it('splits the cost and lists the route', () => {
    const days = [day(1, 'Cairo', [item('09:00:00', '10:00:00', 600)], 1200), day(2, 'Cairo', [], 1200), day(3, 'Luxor', [])]
    expect(costBreakdown(days, 3500)).toEqual({ hotels: 2400, nights: 2, tickets: 600, other: 500, total: 3500 })
    expect(route(days)).toBe('Cairo → Luxor')
  })
})

describe('stayOf', () => {
  it('returns the nights in a row in the same city', () => {
    const days = [day(1, 'Cairo', []), day(2, 'Cairo', []), day(3, 'Luxor', []), day(4, 'Luxor', [])]
    days[2].city_id = days[3].city_id = 2
    expect(stayOf(days, days[1]).map((d) => d.day_number)).toEqual([1, 2])
    expect(stayOf(days, days[2]).map((d) => d.day_number)).toEqual([3, 4])
  })
})
