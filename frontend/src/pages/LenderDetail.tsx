// Open Stearns Bank. Show programs listed in priority order — Tier 1 is tried first.
// Expand Standard Tier 1 and point to the FICO criterion row (threshold 725, weight 2.0).
// Say: "Every rule is a row in the database. To change Stearns's FICO minimum I click
// Edit on this one criterion and update the threshold — no code change, no redeployment."
// Live-edit the PayNet minimum on Standard Tier 3 from 665 to 660, save, then re-run
// underwriting on the demo application to show the result changes immediately.
// Say: "When a lender sends a revised rate sheet, this is the entire update workflow."

import { useState } from 'react'
import { useParams, useNavigate, Link } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { lendersApi } from '../api/client'
import type { LenderCriterion, LenderProgram } from '../types'

const CRITERION_TYPES = [
  { value: 'min_value', label: 'Minimum Value (>=)' },
  { value: 'max_value', label: 'Maximum Value (<=)' },
  { value: 'required_true', label: 'Must Be True / Yes' },
  { value: 'required_false', label: 'Must Be False / No' },
  { value: 'excluded_values', label: 'Excluded Values (field not in list)' },
  { value: 'allowed_values', label: 'Allowed Values (field must be in list)' },
]

const APPLICABILITY_TYPES = [
  { value: 'general', label: 'General (all applications)' },
  { value: 'with_paynet', label: 'Only when PayNet score is provided' },
  { value: 'without_paynet', label: 'Only when PayNet score is absent' },
  { value: 'corp_only', label: 'Corporate-only (no personal guarantor)' },
  { value: 'medical', label: 'Medical industry only' },
  { value: 'trucking', label: 'Trucking industry / equipment only' },
]

const APPLICATION_FIELDS = [
  'guarantor_fico', 'paynet_score', 'years_in_business', 'annual_revenue',
  'loan_amount', 'loan_term_months', 'business_state', 'business_industry',
  'equipment_type', 'equipment_age_years', 'has_bankruptcy',
  'years_since_bankruptcy', 'has_judgments', 'has_foreclosures',
  'has_repossessions', 'has_tax_liens', 'is_startup', 'is_us_citizen',
  'is_homeowner', 'years_at_current_residence', 'has_cdl',
  'num_trucks_operating', 'is_corp_only', 'personal_revolving_debt',
  'revolving_plus_unsecured_debt', 'is_private_party_sale', 'is_trucking', 'is_medical',
]

function Input(props: React.InputHTMLAttributes<HTMLInputElement>) {
  return (
    <input
      {...props}
      className="block w-full rounded border border-gray-300 px-2 py-1.5 text-sm focus:border-blue-500 focus:outline-none"
    />
  )
}

function Select(props: React.SelectHTMLAttributes<HTMLSelectElement> & { children: React.ReactNode }) {
  return (
    <select
      {...props}
      className="block w-full rounded border border-gray-300 px-2 py-1.5 text-sm focus:border-blue-500 focus:outline-none"
    />
  )
}

function CriterionForm({
  programId,
  lenderId,
  criterion,
  onClose,
}: {
  programId: number
  lenderId: number
  criterion?: LenderCriterion
  onClose: () => void
}) {
  const queryClient = useQueryClient()
  const isEdit = Boolean(criterion)

  const [form, setForm] = useState({
    label: criterion?.label ?? '',
    field_name: criterion?.field_name ?? 'guarantor_fico',
    criterion_type: criterion?.criterion_type ?? 'min_value',
    threshold_value: criterion?.threshold_value ?? '',
    allowed_values_raw: criterion?.allowed_values?.join(', ') ?? '',
    is_hard_reject: criterion?.is_hard_reject ?? true,
    null_means_pass: criterion?.null_means_pass ?? false,
    weight: criterion?.weight ?? 1.0,
    description: criterion?.description ?? '',
  })

  const set = (key: string, value: unknown) => setForm(prev => ({ ...prev, [key]: value }))

  const saveMutation = useMutation({
    mutationFn: () => {
      const payload = {
        label: form.label,
        field_name: form.field_name,
        criterion_type: form.criterion_type,
        threshold_value: form.threshold_value !== '' ? Number(form.threshold_value) : null,
        allowed_values: form.allowed_values_raw
          ? form.allowed_values_raw.split(',').map((s: string) => s.trim()).filter(Boolean)
          : null,
        is_hard_reject: form.is_hard_reject,
        null_means_pass: form.null_means_pass,
        weight: Number(form.weight),
        description: form.description || null,
      }
      if (isEdit && criterion) {
        return lendersApi.updateCriterion(lenderId, programId, criterion.id, payload)
      }
      return lendersApi.addCriterion(lenderId, programId, payload)
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['lender', String(lenderId)] })
      onClose()
    },
  })

  const needsThreshold = ['min_value', 'max_value'].includes(form.criterion_type)
  const needsList = ['excluded_values', 'allowed_values'].includes(form.criterion_type)

  return (
    <div className="bg-gray-50 border border-gray-200 rounded-lg p-4 mt-2 space-y-3">
      <div className="grid grid-cols-2 gap-3">
        <div>
          <label className="block text-xs font-medium text-gray-600 mb-1">Label</label>
          <Input value={form.label} onChange={e => set('label', e.target.value)} placeholder="e.g. Minimum FICO Score" />
        </div>
        <div>
          <label className="block text-xs font-medium text-gray-600 mb-1">Application Field</label>
          <Select value={form.field_name} onChange={e => set('field_name', e.target.value)}>
            {APPLICATION_FIELDS.map(f => <option key={f} value={f}>{f}</option>)}
          </Select>
        </div>
        <div>
          <label className="block text-xs font-medium text-gray-600 mb-1">Criterion Type</label>
          <Select value={form.criterion_type} onChange={e => set('criterion_type', e.target.value)}>
            {CRITERION_TYPES.map(t => <option key={t.value} value={t.value}>{t.label}</option>)}
          </Select>
        </div>
        {needsThreshold && (
          <div>
            <label className="block text-xs font-medium text-gray-600 mb-1">Threshold Value</label>
            <Input type="number" value={form.threshold_value} onChange={e => set('threshold_value', e.target.value)} />
          </div>
        )}
        {needsList && (
          <div className="col-span-2">
            <label className="block text-xs font-medium text-gray-600 mb-1">Values (comma separated)</label>
            <Input value={form.allowed_values_raw} onChange={e => set('allowed_values_raw', e.target.value)}
              placeholder="e.g. CA, NV, ND, VT" />
          </div>
        )}
        <div>
          <label className="block text-xs font-medium text-gray-600 mb-1">Weight</label>
          <Input type="number" min="0" step="0.5" value={form.weight} onChange={e => set('weight', e.target.value)} />
        </div>
        <div className="col-span-2">
          <label className="block text-xs font-medium text-gray-600 mb-1">Description (optional)</label>
          <Input value={form.description} onChange={e => set('description', e.target.value)} />
        </div>
        <div className="col-span-2 flex gap-4 text-sm">
          <label className="flex items-center gap-2 cursor-pointer">
            <input type="checkbox" checked={form.is_hard_reject} onChange={e => set('is_hard_reject', e.target.checked)} />
            Hard reject (fail = ineligible)
          </label>
          <label className="flex items-center gap-2 cursor-pointer">
            <input type="checkbox" checked={form.null_means_pass} onChange={e => set('null_means_pass', e.target.checked)} />
            Null means pass
          </label>
        </div>
      </div>
      <div className="flex gap-2">
        <button
          onClick={() => saveMutation.mutate()}
          disabled={saveMutation.isPending}
          className="px-3 py-1.5 bg-blue-600 text-white text-xs font-medium rounded hover:bg-blue-700 disabled:opacity-50"
        >
          {saveMutation.isPending ? 'Saving...' : 'Save Criterion'}
        </button>
        <button onClick={onClose} className="px-3 py-1.5 border border-gray-300 text-xs rounded text-gray-600 hover:bg-gray-100">
          Cancel
        </button>
      </div>
    </div>
  )
}

function ProgramSection({ program, lenderId }: { program: LenderProgram; lenderId: number }) {
  const queryClient = useQueryClient()
  const [addingCriterion, setAddingCriterion] = useState(false)
  const [editingCriterion, setEditingCriterion] = useState<number | null>(null)
  const [collapsed, setCollapsed] = useState(false)

  const deleteCriterionMutation = useMutation({
    mutationFn: (criterionId: number) => lendersApi.deleteCriterion(lenderId, program.id, criterionId),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['lender', String(lenderId)] }),
  })

  const deleteProgramMutation = useMutation({
    mutationFn: () => lendersApi.deleteProgram(lenderId, program.id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['lender', String(lenderId)] }),
  })

  return (
    <div className="border border-gray-200 rounded-lg overflow-hidden">
      <div
        className="flex items-center justify-between px-4 py-3 bg-gray-50 cursor-pointer"
        onClick={() => setCollapsed(c => !c)}
      >
        <div>
          <span className="text-sm font-medium text-gray-900">{program.name}</span>
          <span className="ml-2 text-xs text-gray-400">
            Priority {program.priority} — {APPLICABILITY_TYPES.find(a => a.value === program.applicability_type)?.label ?? program.applicability_type}
          </span>
        </div>
        <div className="flex items-center gap-3" onClick={e => e.stopPropagation()}>
          <span className="text-xs text-gray-400">{program.criteria.length} criteria</span>
          <button
            onClick={() => { if (window.confirm('Delete this program and all its criteria?')) deleteProgramMutation.mutate() }}
            className="text-xs text-red-500 hover:underline"
          >
            Delete Program
          </button>
        </div>
      </div>

      {!collapsed && (
        <div className="p-4">
          {program.rate_description && (
            <p className="text-xs text-gray-500 mb-3 font-mono">{program.rate_description}</p>
          )}

          {program.criteria.length > 0 && (
            <table className="min-w-full text-xs mb-3">
              <thead>
                <tr className="border-b border-gray-200">
                  <th className="pb-1 text-left text-gray-400 pr-4">Label</th>
                  <th className="pb-1 text-left text-gray-400 pr-4">Field</th>
                  <th className="pb-1 text-left text-gray-400 pr-4">Type</th>
                  <th className="pb-1 text-left text-gray-400 pr-4">Threshold / Values</th>
                  <th className="pb-1 text-left text-gray-400 pr-4">Required</th>
                  <th className="pb-1 text-left text-gray-400" />
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {program.criteria.map(c => (
                  <tr key={c.id}>
                    <td className="py-1.5 pr-4 text-gray-800 font-medium">{c.label}</td>
                    <td className="py-1.5 pr-4 text-gray-500 font-mono">{c.field_name}</td>
                    <td className="py-1.5 pr-4 text-gray-500">{c.criterion_type}</td>
                    <td className="py-1.5 pr-4 text-gray-500">
                      {c.threshold_value != null ? c.threshold_value.toLocaleString() : ''}
                      {c.allowed_values ? c.allowed_values.slice(0, 3).join(', ') + (c.allowed_values.length > 3 ? '...' : '') : ''}
                    </td>
                    <td className="py-1.5 pr-4">
                      {c.is_hard_reject ? <span className="text-red-500">Yes</span> : <span className="text-gray-400">No</span>}
                    </td>
                    <td className="py-1.5 text-right">
                      <button onClick={() => setEditingCriterion(editingCriterion === c.id ? null : c.id)}
                        className="text-blue-500 hover:underline mr-2">Edit</button>
                      <button
                        onClick={() => { if (window.confirm('Delete this criterion?')) deleteCriterionMutation.mutate(c.id) }}
                        className="text-red-400 hover:underline">Delete</button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}

          {program.criteria.map(c =>
            editingCriterion === c.id ? (
              <CriterionForm key={c.id} programId={program.id} lenderId={lenderId} criterion={c}
                onClose={() => setEditingCriterion(null)} />
            ) : null
          )}

          {addingCriterion ? (
            <CriterionForm programId={program.id} lenderId={lenderId} onClose={() => setAddingCriterion(false)} />
          ) : (
            <button onClick={() => setAddingCriterion(true)}
              className="text-xs text-blue-600 hover:underline mt-1">
              + Add Criterion
            </button>
          )}
        </div>
      )}
    </div>
  )
}

export default function LenderDetail() {
  const { id } = useParams()
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const isNew = id === 'new'
  const [showProgramForm, setShowProgramForm] = useState(false)
  const [newProgram, setNewProgram] = useState({ name: '', description: '', applicability_type: 'general', priority: 10, rate_description: '' })

  const { data: lender, isLoading } = useQuery({
    queryKey: ['lender', id],
    queryFn: () => lendersApi.get(Number(id)),
    enabled: !isNew,
  })

  const [lenderForm, setLenderForm] = useState({ name: '', description: '', contact_email: '', contact_phone: '' })

  const createLenderMutation = useMutation({
    mutationFn: () => lendersApi.create({ ...lenderForm, programs: [] }),
    onSuccess: (created) => {
      queryClient.invalidateQueries({ queryKey: ['lenders'] })
      navigate(`/lenders/${created.id}`)
    },
  })

  const deleteLenderMutation = useMutation({
    mutationFn: () => lendersApi.delete(Number(id)),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['lenders'] })
      navigate('/lenders')
    },
  })

  const addProgramMutation = useMutation({
    mutationFn: () => lendersApi.addProgram(Number(id), { ...newProgram, criteria: [] }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['lender', id] })
      setShowProgramForm(false)
      setNewProgram({ name: '', description: '', applicability_type: 'general', priority: 10, rate_description: '' })
    },
  })

  if (isNew) {
    return (
      <div>
        <h1 className="text-2xl font-semibold text-gray-900 mb-6">Add Lender</h1>
        <div className="bg-white rounded-lg border border-gray-200 p-6 max-w-lg space-y-4">
          {(['name', 'description', 'contact_email', 'contact_phone'] as const).map(field => (
            <div key={field}>
              <label className="block text-sm font-medium text-gray-700 mb-1 capitalize">{field.replace(/_/g, ' ')}</label>
              <input
                className="block w-full rounded border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none"
                value={lenderForm[field]}
                onChange={e => setLenderForm(prev => ({ ...prev, [field]: e.target.value }))}
              />
            </div>
          ))}
          <div className="flex gap-3 pt-2">
            <button onClick={() => createLenderMutation.mutate()}
              disabled={!lenderForm.name || createLenderMutation.isPending}
              className="px-4 py-2 bg-blue-600 text-white text-sm rounded hover:bg-blue-700 disabled:opacity-50">
              Create Lender
            </button>
            <Link to="/lenders" className="px-4 py-2 border border-gray-300 text-sm rounded text-gray-700 hover:bg-gray-50">
              Cancel
            </Link>
          </div>
        </div>
      </div>
    )
  }

  if (isLoading) return <p className="text-gray-500">Loading...</p>
  if (!lender) return <p className="text-red-500">Lender not found.</p>

  return (
    <div>
      <div className="flex items-center gap-3 mb-6">
        <Link to="/lenders" className="text-sm text-gray-400 hover:text-gray-600">Lender Policies</Link>
        <span className="text-gray-300">/</span>
        <span className="text-sm text-gray-700">{lender.name}</span>
      </div>

      <div className="flex items-start justify-between mb-6">
        <div>
          <h1 className="text-2xl font-semibold text-gray-900">{lender.name}</h1>
          {lender.description && <p className="text-sm text-gray-500 mt-1 max-w-2xl">{lender.description}</p>}
          <div className="flex gap-4 mt-1 text-xs text-gray-400">
            {lender.contact_email && <span>{lender.contact_email}</span>}
            {lender.contact_phone && <span>{lender.contact_phone}</span>}
          </div>
        </div>
        <button
          onClick={() => { if (window.confirm('Delete this lender and all its programs?')) deleteLenderMutation.mutate() }}
          className="px-3 py-1.5 border border-red-300 text-sm rounded text-red-600 hover:bg-red-50"
        >
          Delete Lender
        </button>
      </div>

      <div className="flex items-center justify-between mb-3">
        <h2 className="text-base font-semibold text-gray-900">Programs ({lender.programs.length})</h2>
        <button onClick={() => setShowProgramForm(s => !s)}
          className="px-3 py-1.5 bg-blue-600 text-white text-xs font-medium rounded hover:bg-blue-700">
          Add Program
        </button>
      </div>

      {showProgramForm && (
        <div className="bg-gray-50 border border-gray-200 rounded-lg p-4 mb-4 grid grid-cols-2 gap-3">
          {['name', 'description', 'rate_description'].map(f => (
            <div key={f} className={f === 'name' ? '' : 'col-span-2'}>
              <label className="block text-xs font-medium text-gray-600 mb-1 capitalize">{f.replace(/_/g, ' ')}</label>
              <input className="block w-full rounded border border-gray-300 px-2 py-1.5 text-sm focus:outline-none"
                value={(newProgram as any)[f]}
                onChange={e => setNewProgram(p => ({ ...p, [f]: e.target.value }))} />
            </div>
          ))}
          <div>
            <label className="block text-xs font-medium text-gray-600 mb-1">Applicability</label>
            <select className="block w-full rounded border border-gray-300 px-2 py-1.5 text-sm focus:outline-none"
              value={newProgram.applicability_type}
              onChange={e => setNewProgram(p => ({ ...p, applicability_type: e.target.value }))}>
              {APPLICABILITY_TYPES.map(a => <option key={a.value} value={a.value}>{a.label}</option>)}
            </select>
          </div>
          <div>
            <label className="block text-xs font-medium text-gray-600 mb-1">Priority</label>
            <input type="number" className="block w-full rounded border border-gray-300 px-2 py-1.5 text-sm focus:outline-none"
              value={newProgram.priority}
              onChange={e => setNewProgram(p => ({ ...p, priority: Number(e.target.value) }))} />
          </div>
          <div className="col-span-2 flex gap-2">
            <button onClick={() => addProgramMutation.mutate()} disabled={!newProgram.name || addProgramMutation.isPending}
              className="px-3 py-1.5 bg-blue-600 text-white text-xs font-medium rounded hover:bg-blue-700 disabled:opacity-50">
              Save Program
            </button>
            <button onClick={() => setShowProgramForm(false)}
              className="px-3 py-1.5 border border-gray-300 text-xs rounded text-gray-600">Cancel</button>
          </div>
        </div>
      )}

      <div className="space-y-3">
        {lender.programs
          .slice()
          .sort((a, b) => a.priority - b.priority)
          .map(program => (
            <ProgramSection key={program.id} program={program} lenderId={lender.id} />
          ))}
      </div>
    </div>
  )
}
