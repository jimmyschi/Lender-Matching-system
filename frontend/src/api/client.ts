import axios from 'axios'
import type {
  LoanApplication,
  LoanApplicationCreate,
  Lender,
  LenderSummary,
  LenderProgram,
  LenderCriterion,
  UnderwritingResults,
} from '../types'

const http = axios.create({ baseURL: '/api' })

export const applicationsApi = {
  list: () => http.get<LoanApplication[]>('/applications/').then(r => r.data),
  get: (id: number) => http.get<LoanApplication>(`/applications/${id}`).then(r => r.data),
  create: (data: LoanApplicationCreate) =>
    http.post<LoanApplication>('/applications/', data).then(r => r.data),
  update: (id: number, data: LoanApplicationCreate) =>
    http.put<LoanApplication>(`/applications/${id}`, data).then(r => r.data),
  delete: (id: number) => http.delete(`/applications/${id}`),
}

export const lendersApi = {
  list: () => http.get<LenderSummary[]>('/lenders/').then(r => r.data),
  get: (id: number) => http.get<Lender>(`/lenders/${id}`).then(r => r.data),
  create: (data: Partial<Lender>) => http.post<Lender>('/lenders/', data).then(r => r.data),
  update: (id: number, data: Partial<Lender>) =>
    http.put<Lender>(`/lenders/${id}`, data).then(r => r.data),
  delete: (id: number) => http.delete(`/lenders/${id}`),

  addProgram: (lenderId: number, data: Partial<LenderProgram>) =>
    http.post<LenderProgram>(`/lenders/${lenderId}/programs`, data).then(r => r.data),
  updateProgram: (lenderId: number, programId: number, data: Partial<LenderProgram>) =>
    http.put<LenderProgram>(`/lenders/${lenderId}/programs/${programId}`, data).then(r => r.data),
  deleteProgram: (lenderId: number, programId: number) =>
    http.delete(`/lenders/${lenderId}/programs/${programId}`),

  addCriterion: (lenderId: number, programId: number, data: Partial<LenderCriterion>) =>
    http.post<LenderCriterion>(`/lenders/${lenderId}/programs/${programId}/criteria`, data).then(r => r.data),
  updateCriterion: (lenderId: number, programId: number, criterionId: number, data: Partial<LenderCriterion>) =>
    http.put<LenderCriterion>(`/lenders/${lenderId}/programs/${programId}/criteria/${criterionId}`, data).then(r => r.data),
  deleteCriterion: (lenderId: number, programId: number, criterionId: number) =>
    http.delete(`/lenders/${lenderId}/programs/${programId}/criteria/${criterionId}`),
}

export const underwritingApi = {
  run: (applicationId: number) =>
    http.post<UnderwritingResults>(`/underwriting/${applicationId}/run`).then(r => r.data),
  getResults: (applicationId: number) =>
    http.get<UnderwritingResults>(`/underwriting/${applicationId}/results`).then(r => r.data),
}
