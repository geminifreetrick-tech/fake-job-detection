import { describe, expect, it } from 'vitest'
import { pct, safeDateTime } from '../lib/format'

describe('format helpers', () => {
  it('pct renders percentage', () => {
    expect(pct(0.5)).toBe('50.0%')
    expect(pct(0.1234, 2)).toBe('12.34%')
  })

  it('safeDateTime is robust to bad input', () => {
    expect(safeDateTime('not-a-date')).toBe('not-a-date')
    expect(safeDateTime('2024-01-01T12:34:56Z')).toContain('2024-01-01')
  })
})
