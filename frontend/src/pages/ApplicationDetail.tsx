import { useParams, Link, useNavigate } from 'react-router-dom'
import { useQuery, useMutation } from '@tanstack/react-query'
import { applicationsApi, underwritingApi } from '../api/client'
import { INDUSTRIES, EQUIPMENT_TYPES } from '../types'

function labelFor(value: string, list: { value: string; label: string }[]) {
  return list.find(i => i.value === value)?.label ?? value.replace(/_/g, ' ')
}

function Row({ label, value }: { label: string; value: React.ReactNode }) {
  return (
    <div className="flex justify-between py-2 border-b border-gray-100 last:border-0 text-sm">
      <span className="text-gray-500">{label}</span>
      <span className="text-gray-900 font-medium">{value}</span>
    </div>
  )
}

export default function ApplicationDetail() {
  const { id } = useParams()
  const navigate = useNavigate()
  const appId = Number(id)

  const { data: app, isLoading } = useQuery({
    queryKey: ['application', id],
    queryFn: () => applicationsApi.get(appId),
  })

  const runMutation = useMutation({
    mutationFn: () => underwritingApi.run(appId),
    onSuccess: () => navigate(`/applications/${appId}/results`),
  })

  if (isLoading) return <p className="text-gray-500">Loading...</p>
  if (!app) return <p className="text-red-500">Application not found.</p>

  return (
    <div>
      <div className="flex items-center gap-3 mb-6">
        <Link to="/" className="text-sm text-gray-400 hover:text-gray-600">Applications</Link>
        <span className="text-gray-300">/</span>
        <span className="text-sm text-gray-700">{app.business_name}</span>
      </div>

      <div className="flex items-start justify-between mb-6">
        <div>
          <h1 className="text-2xl font-semibold text-gray-900">{app.business_name}</h1>
          <p className="text-sm text-gray-400 mt-1">Application #{app.id} — {app.status}</p>
        </div>
        <div className="flex gap-3">
          <Link
            to={`/applications/${appId}/edit`}
            className="px-4 py-2 border border-gray-300 text-sm rounded-md text-gray-700 hover:bg-gray-50"
          >
            Edit
          </Link>
          {app.status === 'completed' && (
            <Link
              to={`/applications/${appId}/results`}
              className="px-4 py-2 bg-green-600 text-white text-sm font-medium rounded-md hover:bg-green-700"
            >
              View Results
            </Link>
          )}
          <button
            onClick={() => runMutation.mutate()}
            disabled={runMutation.isPending}
            className="px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded-md hover:bg-blue-700 disabled:opacity-50"
          >
            {runMutation.isPending ? 'Running...' : 'Run Underwriting'}
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <div className="bg-white rounded-lg border border-gray-200 p-6">
          <h2 className="text-base font-semibold text-gray-900 mb-3">Business</h2>
          <Row label="State" value={app.business_state} />
          <Row label="Industry" value={labelFor(app.business_industry, INDUSTRIES)} />
          <Row label="Years in Business" value={`${app.years_in_business} yrs`} />
          <Row label="Annual Revenue" value={app.annual_revenue ? `$${app.annual_revenue.toLocaleString()}` : 'Not provided'} />
          <Row label="Startup" value={app.is_startup ? 'Yes' : 'No'} />
          <Row label="Corp Only" value={app.is_corp_only ? 'Yes' : 'No'} />
        </div>

        <div className="bg-white rounded-lg border border-gray-200 p-6">
          <h2 className="text-base font-semibold text-gray-900 mb-3">Credit Profile</h2>
          <Row label="FICO Score" value={app.guarantor_fico} />
          <Row label="PayNet Score" value={app.paynet_score ?? 'Not provided'} />
          <Row label="Bankruptcy" value={app.has_bankruptcy ? `Yes — ${app.years_since_bankruptcy ?? '?'} yrs ago` : 'No'} />
          <Row label="Judgments" value={app.has_judgments ? 'Yes' : 'No'} />
          <Row label="Foreclosures" value={app.has_foreclosures ? 'Yes' : 'No'} />
          <Row label="Repossessions" value={app.has_repossessions ? 'Yes' : 'No'} />
          <Row label="Tax Liens" value={app.has_tax_liens ? 'Yes' : 'No'} />
          <Row label="Personal Revolving Debt" value={app.personal_revolving_debt != null ? `$${app.personal_revolving_debt.toLocaleString()}` : 'Not provided'} />
          <Row label="Revolving + Unsecured Debt" value={app.revolving_plus_unsecured_debt != null ? `$${app.revolving_plus_unsecured_debt.toLocaleString()}` : 'Not provided'} />
        </div>

        <div className="bg-white rounded-lg border border-gray-200 p-6">
          <h2 className="text-base font-semibold text-gray-900 mb-3">Loan Request</h2>
          <Row label="Amount" value={`$${app.loan_amount.toLocaleString()}`} />
          <Row label="Term" value={`${app.loan_term_months} months`} />
        </div>

        <div className="bg-white rounded-lg border border-gray-200 p-6">
          <h2 className="text-base font-semibold text-gray-900 mb-3">Equipment</h2>
          <Row label="Type" value={labelFor(app.equipment_type, EQUIPMENT_TYPES)} />
          <Row label="Age" value={app.equipment_age_years != null ? `${app.equipment_age_years} yrs` : 'New / Unknown'} />
          <Row label="Private Party Sale" value={app.is_private_party_sale ? 'Yes' : 'No'} />
        </div>

        <div className="bg-white rounded-lg border border-gray-200 p-6">
          <h2 className="text-base font-semibold text-gray-900 mb-3">Additional</h2>
          <Row label="US Citizen" value={app.is_us_citizen ? 'Yes' : 'No'} />
          <Row label="Homeowner" value={app.is_homeowner ? 'Yes' : 'No'} />
          <Row label="Years at Residence" value={app.years_at_current_residence ?? 'Not provided'} />
          <Row label="CDL" value={app.has_cdl ? 'Yes' : 'No'} />
          <Row label="Trucks Operating" value={app.num_trucks_operating ?? 'Not provided'} />
        </div>
      </div>
    </div>
  )
}
