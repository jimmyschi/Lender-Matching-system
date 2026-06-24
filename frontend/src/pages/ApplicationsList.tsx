import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { applicationsApi } from '../api/client'
import type { LoanApplication } from '../types'

function statusBadge(status: string) {
  const colors: Record<string, string> = {
    submitted: 'bg-blue-100 text-blue-700',
    underwriting: 'bg-yellow-100 text-yellow-700',
    completed: 'bg-green-100 text-green-700',
    draft: 'bg-gray-100 text-gray-600',
  }
  return (
    <span className={`inline-flex px-2 py-0.5 rounded text-xs font-medium ${colors[status] ?? 'bg-gray-100 text-gray-600'}`}>
      {status}
    </span>
  )
}

export default function ApplicationsList() {
  const queryClient = useQueryClient()
  const { data: applications, isLoading } = useQuery({
    queryKey: ['applications'],
    queryFn: applicationsApi.list,
  })

  const deleteMutation = useMutation({
    mutationFn: applicationsApi.delete,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['applications'] }),
  })

  if (isLoading) return <p className="text-gray-500">Loading...</p>

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-semibold text-gray-900">Loan Applications</h1>
        <Link
          to="/applications/new"
          className="px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded-md hover:bg-blue-700"
        >
          New Application
        </Link>
      </div>

      {(!applications || applications.length === 0) ? (
        <div className="text-center py-16 text-gray-400">
          <p className="text-lg">No applications yet.</p>
          <p className="text-sm mt-1">Create one to run underwriting.</p>
        </div>
      ) : (
        <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wide">Business</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wide">Industry</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wide">Loan Amount</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wide">FICO</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wide">Status</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wide">Date</th>
                <th className="px-6 py-3" />
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200">
              {applications.map((app: LoanApplication) => (
                <tr key={app.id} className="hover:bg-gray-50">
                  <td className="px-6 py-4 text-sm font-medium text-gray-900">
                    <Link to={`/applications/${app.id}`} className="hover:text-blue-600">
                      {app.business_name}
                    </Link>
                    <div className="text-xs text-gray-400">{app.business_state}</div>
                  </td>
                  <td className="px-6 py-4 text-sm text-gray-600">{app.business_industry.replace(/_/g, ' ')}</td>
                  <td className="px-6 py-4 text-sm text-gray-600">
                    ${app.loan_amount.toLocaleString()}
                  </td>
                  <td className="px-6 py-4 text-sm text-gray-600">{app.guarantor_fico}</td>
                  <td className="px-6 py-4">{statusBadge(app.status)}</td>
                  <td className="px-6 py-4 text-sm text-gray-400">
                    {new Date(app.created_at).toLocaleDateString()}
                  </td>
                  <td className="px-6 py-4 text-right text-sm">
                    <Link to={`/applications/${app.id}`} className="text-blue-600 hover:underline mr-3">View</Link>
                    <button
                      onClick={() => { if (window.confirm('Delete this application?')) deleteMutation.mutate(app.id) }}
                      className="text-red-500 hover:underline"
                    >
                      Delete
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
