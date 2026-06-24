import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { lendersApi } from '../api/client'

export default function LenderPolicies() {
  const { data: lenders, isLoading } = useQuery({
    queryKey: ['lenders'],
    queryFn: lendersApi.list,
  })

  if (isLoading) return <p className="text-gray-500">Loading...</p>

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-semibold text-gray-900">Lender Policies</h1>
        <Link
          to="/lenders/new"
          className="px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded-md hover:bg-blue-700"
        >
          Add Lender
        </Link>
      </div>

      {(!lenders || lenders.length === 0) ? (
        <div className="text-center py-16 text-gray-400">
          <p>No lenders configured. Run the seed script to load the 5 default lenders.</p>
        </div>
      ) : (
        <div className="grid gap-4">
          {lenders.map(lender => (
            <div key={lender.id} className="bg-white rounded-lg border border-gray-200 p-5">
              <div className="flex items-start justify-between">
                <div>
                  <h2 className="text-base font-semibold text-gray-900">{lender.name}</h2>
                  {lender.description && (
                    <p className="text-sm text-gray-500 mt-1 max-w-2xl">{lender.description}</p>
                  )}
                  <div className="flex gap-4 mt-2 text-xs text-gray-400">
                    {lender.contact_email && <span>{lender.contact_email}</span>}
                    {lender.contact_phone && <span>{lender.contact_phone}</span>}
                  </div>
                </div>
                <Link
                  to={`/lenders/${lender.id}`}
                  className="ml-4 flex-shrink-0 px-3 py-1.5 border border-gray-300 text-sm rounded-md text-gray-700 hover:bg-gray-50"
                >
                  View / Edit
                </Link>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
