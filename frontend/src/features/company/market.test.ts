import { describe, expect, it } from 'vitest'
import { marketFor } from './market'

describe('marketFor', () => {
  it('ranks a price among competitors', () => {
    expect(marketFor(1290, [1380])).toEqual({ others: 1, lowest: 1380, average: 1380, position: 1, total: 2 })
    expect(marketFor(1400, [1200, 1300, 1500])).toMatchObject({ position: 3, total: 4, lowest: 1200, average: 1333 })
    expect(marketFor(1200, [1200])).toMatchObject({ position: 1 }) // a tie is still the lowest
    expect(marketFor(900, [])).toEqual({ others: 0, lowest: null, average: null, position: 1, total: 1 })
  })
})
