import { describe, expect, it } from 'vitest'
import { ICON_NAMES, INTEREST_ICONS, isIconName } from './icons'

const files = Object.keys(import.meta.glob('../../assets/icons/*.svg')).map((p) => p.split('/').pop()!.replace('.svg', ''))

describe('icon set', () => {
  it('lists exactly the exported SVGs', () => {
    expect([...ICON_NAMES].sort()).toEqual(files.sort())
  })
  it('only offers real icons for interests', () => {
    expect(INTEREST_ICONS.every(isIconName)).toBe(true)
    expect(isIconName('pyramid')).toBe(false)
  })
})
