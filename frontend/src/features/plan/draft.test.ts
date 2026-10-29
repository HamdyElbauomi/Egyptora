import { describe, expect, it } from 'vitest'
import {
  clampDays,
  emptyDraft,
  firstOpenStep,
  recommendedCityCount,
  tierForAmount,
  toGenerateBody,
  toggleId,
  type PlanDraft,
} from './draft'

const ready: PlanDraft = { ...emptyDraft, interestIds: [1, 3], budgetLevel: 'mid', days: 4, suggest: false, cityIds: [1, 2] }

describe('plan draft', () => {
  it('maps an exact amount to its budget card', () => {
    expect(tierForAmount(9_999)).toBe('low')
    expect(tierForAmount(10_000)).toBe('mid')
    expect(tierForAmount(25_000)).toBe('mid')
    expect(tierForAmount(25_001)).toBe('high')
  })

  it('keeps days between 1 and 21', () => {
    expect(clampDays(0)).toBe(1)
    expect(clampDays(30)).toBe(21)
    expect(clampDays(Number.NaN)).toBe(emptyDraft.days)
  })

  it('recommends cities like the backend', () => {
    expect([1, 3, 4, 6, 7, 14].map(recommendedCityCount)).toEqual([1, 1, 2, 2, 3, 3])
  })

  it('finds the first unanswered step', () => {
    expect(firstOpenStep(emptyDraft)).toBe('interests')
    expect(firstOpenStep({ ...ready, budgetLevel: null })).toBe('budget')
    expect(firstOpenStep({ ...ready, cityIds: [] })).toBe('destinations')
    expect(firstOpenStep({ ...ready, days: 1 })).toBe('destinations') // two cities don't fit one day
    expect(firstOpenStep(ready)).toBeNull()
  })

  it('builds the generate request', () => {
    expect(toGenerateBody(ready)).toEqual({
      interest_ids: [1, 3],
      budget_level: 'mid',
      budget_total: null,
      days: 4,
      start_date: null,
      city_ids: [1, 2],
      suggest: false,
    })
    expect(toGenerateBody({ ...ready, suggest: true })).toMatchObject({ city_ids: [], suggest: true })
  })

  it('toggles ids with a cap', () => {
    expect(toggleId([1, 2], 2)).toEqual([1])
    expect(toggleId([1], 2, 2)).toEqual([1, 2])
    expect(toggleId([1, 2], 3, 2)).toEqual([1, 2])
  })
})
