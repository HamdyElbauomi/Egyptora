import { describe, expect, it } from 'vitest'
import { aiSuccess, pct } from './overview'

describe('overview helpers', () => {
  it('averages only the AI rates that exist', () => {
    expect(aiSuccess({ search_success_rate: 1, scan_recognition_rate: 0.5, chat_keep_rate: null })).toBe(0.75)
    expect(aiSuccess({ search_success_rate: null, scan_recognition_rate: null, chat_keep_rate: null })).toBeNull()
    expect(pct(0.756)).toBe('76%')
    expect(pct(null)).toBe('—')
  })
})
