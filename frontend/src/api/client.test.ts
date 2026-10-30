import { describe, expect, it } from 'vitest'
import { errorMessage } from './client'

describe('errorMessage', () => {
  it('reads plain, validation and CSV errors', () => {
    expect(errorMessage({ detail: 'Trip not found' })).toBe('Trip not found')
    expect(errorMessage({ detail: [{ loc: ['body', 'password'], msg: 'String should have at least 8 characters' }] })).toBe(
      'Password: String should have at least 8 characters',
    )
    expect(errorMessage({ detail: { message: '1 rows have errors', errors: [{ row: 2, error: 'Unknown hotel_id 99' }] } })).toBe(
      '1 rows have errors\nRow 2: Unknown hotel_id 99',
    )
    expect(errorMessage(null)).toBe('Something went wrong. Please try again.')
  })
})
