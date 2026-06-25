import { describe, it, expect } from 'vitest'
import { INDUSTRIES, US_STATES, EQUIPMENT_TYPES } from '../types'

describe('INDUSTRIES', () => {
  it('includes core industry types used by the matching engine', () => {
    const values = INDUSTRIES.map(i => i.value)
    expect(values).toContain('construction')
    expect(values).toContain('trucking')
    expect(values).toContain('medical_dental')
  })

  it('every industry entry has a non-empty label', () => {
    INDUSTRIES.forEach(({ value, label }) => {
      expect(label.length, `industry '${value}' has empty label`).toBeGreaterThan(0)
    })
  })
})

describe('US_STATES', () => {
  it('contains all 50 state codes', () => {
    expect(US_STATES.length).toBe(50)
  })

  it('includes states restricted by lenders', () => {
    expect(US_STATES).toContain('CA')
    expect(US_STATES).toContain('NV')
    expect(US_STATES).toContain('TX')
  })
})

describe('EQUIPMENT_TYPES', () => {
  it('includes trucking and non-trucking types', () => {
    const values = EQUIPMENT_TYPES.map(e => e.value)
    expect(values).toContain('class_8_truck')
    expect(values).toContain('construction_equipment')
    expect(values).toContain('medical_equipment')
  })
})
