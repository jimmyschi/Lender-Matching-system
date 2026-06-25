import { describe, it, expect } from 'vitest'
import { applicationsApi, lendersApi, underwritingApi } from '../api/client'

describe('applicationsApi', () => {
  it('exports all required CRUD methods', () => {
    expect(typeof applicationsApi.list).toBe('function')
    expect(typeof applicationsApi.get).toBe('function')
    expect(typeof applicationsApi.create).toBe('function')
    expect(typeof applicationsApi.update).toBe('function')
    expect(typeof applicationsApi.delete).toBe('function')
  })
})

describe('lendersApi', () => {
  it('exports lender and nested resource methods', () => {
    expect(typeof lendersApi.list).toBe('function')
    expect(typeof lendersApi.get).toBe('function')
    expect(typeof lendersApi.addProgram).toBe('function')
    expect(typeof lendersApi.addCriterion).toBe('function')
    expect(typeof lendersApi.updateCriterion).toBe('function')
    expect(typeof lendersApi.deleteCriterion).toBe('function')
  })
})

describe('underwritingApi', () => {
  it('exports run and getResults methods', () => {
    expect(typeof underwritingApi.run).toBe('function')
    expect(typeof underwritingApi.getResults).toBe('function')
  })
})
