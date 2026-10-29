import type { GenerateTrip } from '@/api/queries'

/** The traveler's answers while planning. Kept in the browser until the trip is built. */
export interface PlanDraft {
  interestIds: number[]
  budgetLevel: BudgetLevel | null
  /** exact amount in EGP, when the traveler typed one */
  budgetTotal: number | null
  days: number
  /** yyyy-mm-dd */
  startDate: string | null
  suggest: boolean
  /** chosen cities in visiting order */
  cityIds: number[]
}

export type BudgetLevel = 'low' | 'mid' | 'high'

export const MIN_DAYS = 1
export const MAX_DAYS = 21

export const emptyDraft: PlanDraft = {
  interestIds: [],
  budgetLevel: null,
  budgetTotal: null,
  days: 5,
  startDate: null,
  suggest: true,
  cityIds: [],
}

export const STEPS = [
  { key: 'interests', title: 'Interests' },
  { key: 'budget', title: 'Budget' },
  { key: 'length', title: 'Trip length' },
  { key: 'destinations', title: 'Destinations' },
] as const

export type StepKey = (typeof STEPS)[number]['key']

export const BUDGETS: { level: BudgetLevel; tier: string; price: string; description: string }[] = [
  { level: 'low', tier: 'Budget-friendly', price: 'Under EGP 10,000', description: 'Guesthouses, trains, local food spots' },
  { level: 'mid', tier: 'Comfortable', price: 'EGP 10k–25k', description: '3–4★ hotels, a domestic flight or two' },
  { level: 'high', tier: 'Premium', price: 'EGP 25,000+', description: '5★ hotels, private guides and drivers' },
]

/** The budget card an exact amount falls into. */
export function tierForAmount(amount: number): BudgetLevel {
  if (amount < 10_000) return 'low'
  if (amount <= 25_000) return 'mid'
  return 'high'
}

export function clampDays(days: number): number {
  if (!Number.isFinite(days)) return emptyDraft.days
  return Math.min(MAX_DAYS, Math.max(MIN_DAYS, Math.round(days)))
}

/** Same rule as the backend's recommended_city_count. */
export function recommendedCityCount(days: number): number {
  if (days <= 3) return 1
  if (days <= 6) return 2
  return 3
}

export function lengthHint(days: number): string {
  const cities = recommendedCityCount(days)
  if (cities === 1) return 'Enough for one city, seen properly. Cairo and the pyramids fit well.'
  if (cities === 2) return 'Room for Cairo plus Luxor or Aswan at an easy pace.'
  return 'Time for Cairo, Luxor and Aswan, with slower days in between.'
}

export function stepDone(step: StepKey, draft: PlanDraft): boolean {
  switch (step) {
    case 'interests':
      return draft.interestIds.length > 0
    case 'budget':
      return draft.budgetLevel !== null
    case 'length':
      return draft.days >= MIN_DAYS && draft.days <= MAX_DAYS
    case 'destinations':
      return draft.suggest || (draft.cityIds.length > 0 && draft.cityIds.length <= draft.days)
  }
}

/** The first step that still needs an answer, or null when the draft is ready to build. */
export function firstOpenStep(draft: PlanDraft): StepKey | null {
  return STEPS.find((s) => !stepDone(s.key, draft))?.key ?? null
}

export function toGenerateBody(draft: PlanDraft): GenerateTrip {
  const suggest = draft.suggest || draft.cityIds.length === 0
  return {
    interest_ids: draft.interestIds,
    budget_level: draft.budgetLevel ?? 'mid',
    budget_total: draft.budgetTotal,
    days: clampDays(draft.days),
    start_date: draft.startDate || null,
    city_ids: suggest ? [] : draft.cityIds,
    suggest,
  }
}

/** Toggles an id; when `max` is reached the new id is not added. */
export function toggleId(ids: number[], id: number, max = Infinity): number[] {
  if (ids.includes(id)) return ids.filter((x) => x !== id)
  return ids.length >= max ? ids : [...ids, id]
}

const KEY = 'egyptora.plan-draft'

export function loadDraft(): PlanDraft {
  try {
    const raw = localStorage.getItem(KEY)
    if (!raw) return emptyDraft
    return { ...emptyDraft, ...(JSON.parse(raw) as Partial<PlanDraft>) }
  } catch {
    return emptyDraft
  }
}

export function saveDraft(draft: PlanDraft | null): void {
  try {
    if (draft) localStorage.setItem(KEY, JSON.stringify(draft))
    else localStorage.removeItem(KEY)
  } catch {
    // storage blocked: the draft lives only while the page is open
  }
}
