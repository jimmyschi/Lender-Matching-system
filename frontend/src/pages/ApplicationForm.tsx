import { useState, useEffect } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { applicationsApi } from '../api/client'
import { INDUSTRIES, EQUIPMENT_TYPES, US_STATES } from '../types'
import type { LoanApplicationCreate } from '../types'

const BLANK: LoanApplicationCreate = {
  business_name: '',
  business_state: 'TX',
  business_industry: 'construction',
  years_in_business: 0,
  annual_revenue: null,
  is_startup: false,
  guarantor_fico: 0,
  paynet_score: null,
  is_corp_only: false,
  has_bankruptcy: false,
  years_since_bankruptcy: null,
  has_judgments: false,
  has_foreclosures: false,
  has_repossessions: false,
  has_tax_liens: false,
  loan_amount: 0,
  loan_term_months: 60,
  equipment_type: 'construction_equipment',
  equipment_age_years: null,
  is_private_party_sale: false,
  is_us_citizen: true,
  is_homeowner: false,
  years_at_current_residence: null,
  has_cdl: false,
  num_trucks_operating: null,
  personal_revolving_debt: null,
  revolving_plus_unsecured_debt: null,
}

function Field({ label, children, hint }: { label: string; children: React.ReactNode; hint?: string }) {
  return (
    <div>
      <label className="block text-sm font-medium text-gray-700 mb-1">{label}</label>
      {children}
      {hint && <p className="mt-1 text-xs text-gray-400">{hint}</p>}
    </div>
  )
}

function Input(props: React.InputHTMLAttributes<HTMLInputElement>) {
  return (
    <input
      {...props}
      className="block w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none"
    />
  )
}

function Select(props: React.SelectHTMLAttributes<HTMLSelectElement> & { children: React.ReactNode }) {
  return (
    <select
      {...props}
      className="block w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none"
    />
  )
}

function Checkbox({ label, checked, onChange }: { label: string; checked: boolean; onChange: (v: boolean) => void }) {
  return (
    <label className="flex items-center gap-2 text-sm text-gray-700 cursor-pointer">
      <input type="checkbox" checked={checked} onChange={e => onChange(e.target.checked)} className="rounded" />
      {label}
    </label>
  )
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="bg-white rounded-lg border border-gray-200 p-6">
      <h2 className="text-base font-semibold text-gray-900 mb-4">{title}</h2>
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">{children}</div>
    </div>
  )
}

export default function ApplicationForm() {
  const { id } = useParams()
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const isEdit = Boolean(id)

  const [form, setForm] = useState<LoanApplicationCreate>(BLANK)

  const { data: existing } = useQuery({
    queryKey: ['application', id],
    queryFn: () => applicationsApi.get(Number(id)),
    enabled: isEdit,
  })

  useEffect(() => {
    if (existing) {
      const { id: _id, status: _s, created_at: _c, updated_at: _u, ...rest } = existing as any
      setForm(rest)
    }
  }, [existing])

  const createMutation = useMutation({
    mutationFn: applicationsApi.create,
    onSuccess: (app) => {
      queryClient.invalidateQueries({ queryKey: ['applications'] })
      navigate(`/applications/${app.id}`)
    },
  })

  const updateMutation = useMutation({
    mutationFn: (data: LoanApplicationCreate) => applicationsApi.update(Number(id), data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['applications'] })
      navigate(`/applications/${id}`)
    },
  })

  const set = (key: keyof LoanApplicationCreate, value: unknown) =>
    setForm(prev => ({ ...prev, [key]: value }))

  const numOrNull = (v: string) => v === '' ? null : Number(v)

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (isEdit) updateMutation.mutate(form)
    else createMutation.mutate(form)
  }

  const isPending = createMutation.isPending || updateMutation.isPending
  const error = createMutation.error || updateMutation.error

  return (
    <div>
      <h1 className="text-2xl font-semibold text-gray-900 mb-6">
        {isEdit ? 'Edit Application' : 'New Loan Application'}
      </h1>

      <form onSubmit={handleSubmit} className="space-y-6">
        <Section title="Business Information">
          <Field label="Business Name">
            <Input required value={form.business_name} onChange={e => set('business_name', e.target.value)} />
          </Field>
          <Field label="State">
            <Select value={form.business_state} onChange={e => set('business_state', e.target.value)}>
              {US_STATES.map(s => <option key={s} value={s}>{s}</option>)}
            </Select>
          </Field>
          <Field label="Industry">
            <Select value={form.business_industry} onChange={e => set('business_industry', e.target.value)}>
              {INDUSTRIES.map(i => <option key={i.value} value={i.value}>{i.label}</option>)}
            </Select>
          </Field>
          <Field label="Years in Business">
            <Input type="number" min="0" step="0.5" required value={form.years_in_business}
              onChange={e => set('years_in_business', Number(e.target.value))} />
          </Field>
          <Field label="Annual Revenue ($)" hint="Optional — required for some corp-only programs">
            <Input type="number" min="0" value={form.annual_revenue ?? ''}
              onChange={e => set('annual_revenue', numOrNull(e.target.value))} />
          </Field>
          <div className="flex items-end">
            <Checkbox label="Startup business" checked={form.is_startup} onChange={v => set('is_startup', v)} />
          </div>
        </Section>

        <Section title="Credit Profile">
          <Field label="Guarantor FICO Score" hint="Use TransUnion score for Citizens Bank applications">
            <Input type="number" min="300" max="850" required value={form.guarantor_fico}
              onChange={e => set('guarantor_fico', Number(e.target.value))} />
          </Field>
          <Field label="PayNet Score" hint="Leave blank if not available">
            <Input type="number" min="0" max="999" value={form.paynet_score ?? ''}
              onChange={e => set('paynet_score', numOrNull(e.target.value))} />
          </Field>
          <Field label="Personal Revolving Debt ($)" hint="Stearns Bank: limit $30K">
            <Input type="number" min="0" value={form.personal_revolving_debt ?? ''}
              onChange={e => set('personal_revolving_debt', numOrNull(e.target.value))} />
          </Field>
          <Field label="Revolving + Unsecured Debt ($)" hint="Stearns Bank: limit $50K (excluding student loans)">
            <Input type="number" min="0" value={form.revolving_plus_unsecured_debt ?? ''}
              onChange={e => set('revolving_plus_unsecured_debt', numOrNull(e.target.value))} />
          </Field>
          <div className="sm:col-span-2">
            <Checkbox label="Corporate-only application (no personal guarantor)" checked={form.is_corp_only} onChange={v => set('is_corp_only', v)} />
          </div>
        </Section>

        <Section title="Credit History">
          <div className="sm:col-span-2 space-y-3">
            <Checkbox label="Bankruptcy on record" checked={form.has_bankruptcy} onChange={v => set('has_bankruptcy', v)} />
            {form.has_bankruptcy && (
              <Field label="Years since bankruptcy discharge">
                <Input type="number" min="0" step="0.5" value={form.years_since_bankruptcy ?? ''}
                  onChange={e => set('years_since_bankruptcy', numOrNull(e.target.value))} />
              </Field>
            )}
            <Checkbox label="Judgments in credit history" checked={form.has_judgments} onChange={v => set('has_judgments', v)} />
            <Checkbox label="Foreclosures in credit history" checked={form.has_foreclosures} onChange={v => set('has_foreclosures', v)} />
            <Checkbox label="Repossessions in credit history" checked={form.has_repossessions} onChange={v => set('has_repossessions', v)} />
            <Checkbox label="Tax liens on record" checked={form.has_tax_liens} onChange={v => set('has_tax_liens', v)} />
          </div>
        </Section>

        <Section title="Loan Request">
          <Field label="Loan Amount ($)">
            <Input type="number" min="0" required value={form.loan_amount}
              onChange={e => set('loan_amount', Number(e.target.value))} />
          </Field>
          <Field label="Loan Term (months)">
            <Select value={form.loan_term_months} onChange={e => set('loan_term_months', Number(e.target.value))}>
              {[24, 36, 48, 60, 72, 84].map(t => <option key={t} value={t}>{t} months</option>)}
            </Select>
          </Field>
        </Section>

        <Section title="Equipment">
          <Field label="Equipment Type">
            <Select value={form.equipment_type} onChange={e => set('equipment_type', e.target.value)}>
              {EQUIPMENT_TYPES.map(e => <option key={e.value} value={e.value}>{e.label}</option>)}
            </Select>
          </Field>
          <Field label="Equipment Age (years)" hint="Leave blank if new">
            <Input type="number" min="0" value={form.equipment_age_years ?? ''}
              onChange={e => set('equipment_age_years', numOrNull(e.target.value))} />
          </Field>
          <div className="sm:col-span-2">
            <Checkbox label="Private party sale" checked={form.is_private_party_sale} onChange={v => set('is_private_party_sale', v)} />
          </div>
        </Section>

        <Section title="Additional Details">
          <div className="sm:col-span-2 space-y-3">
            <Checkbox label="US Citizen" checked={form.is_us_citizen} onChange={v => set('is_us_citizen', v)} />
            <Checkbox label="Homeowner" checked={form.is_homeowner} onChange={v => set('is_homeowner', v)} />
            {!form.is_homeowner && (
              <Field label="Years at current residence">
                <Input type="number" min="0" step="0.5" value={form.years_at_current_residence ?? ''}
                  onChange={e => set('years_at_current_residence', numOrNull(e.target.value))} />
              </Field>
            )}
            <Checkbox label="Has CDL (Commercial Driver License)" checked={form.has_cdl} onChange={v => set('has_cdl', v)} />
          </div>
          <Field label="Number of Trucks Currently Operating" hint="Required for Falcon Equipment Finance trucking program">
            <Input type="number" min="0" value={form.num_trucks_operating ?? ''}
              onChange={e => set('num_trucks_operating', numOrNull(e.target.value))} />
          </Field>
        </Section>

        {error && (
          <p className="text-sm text-red-600">Something went wrong. Please check your inputs and try again.</p>
        )}

        <div className="flex gap-3">
          <button
            type="submit"
            disabled={isPending}
            className="px-5 py-2 bg-blue-600 text-white text-sm font-medium rounded-md hover:bg-blue-700 disabled:opacity-50"
          >
            {isPending ? 'Saving...' : isEdit ? 'Save Changes' : 'Create Application'}
          </button>
          <button
            type="button"
            onClick={() => navigate(isEdit ? `/applications/${id}` : '/')}
            className="px-5 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 hover:bg-gray-50"
          >
            Cancel
          </button>
        </div>
      </form>
    </div>
  )
}
