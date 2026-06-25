// Walk results top to bottom — eligible lenders ranked by fit score, then ineligible.
// Expand Stearns Bank (rejected): "Stearns has a three-tier PayNet waterfall. This
// applicant has PayNet 662 — 3 points below the lowest tier's 665 minimum. Every tier failed."
// Expand Citizens Bank (rejected): "Single reason: homeownership required. The Non-Homeowner
// program needs 5 years at the same address — this applicant has 3. Tier 3 starts at a
// $75K minimum loan — this applicant requested $45K. Every pathway closes."
// Expand Falcon Equipment Finance (eligible): point to the PayNet criterion score.
// Say: "PayNet 662 clears Falcon's 660 minimum by 2 points. The fit score on that
// criterion is near the floor — the margin scoring makes the near-miss visible."
// Expand Apex Commercial Capital (eligible): Say: "A+ required FICO 720 and 5 years TIB.
// Standard A required TIB 5. Standard B requires FICO 670 and TIB 3 — both pass.
// The engine placed the applicant at B rate automatically."

import { useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { underwritingApi } from '../api/client'
import CriterionRow from '../components/CriterionRow'
import ScoreBadge from '../components/ScoreBadge'
import type { MatchResult } from '../types'

export default function UnderwritingResults() {
  const { id } = useParams()
  const [expanded, setExpanded] = useState<number | null>(null)

  const { data, isLoading, error } = useQuery({
    queryKey: ['results', id],
    queryFn: () => underwritingApi.getResults(Number(id)),
  })

  if (isLoading) return <p className="text-gray-500">Loading results...</p>
  if (error || !data) return <p className="text-red-500">Could not load results.</p>

  const { application, matches } = data
  const eligible = matches.filter(m => m.is_eligible)
  const ineligible = matches.filter(m => !m.is_eligible)

  return (
    <div>
      <div className="flex items-center gap-3 mb-6">
        <Link to="/" className="text-sm text-gray-400 hover:text-gray-600">Applications</Link>
        <span className="text-gray-300">/</span>
        <Link to={`/applications/${id}`} className="text-sm text-gray-400 hover:text-gray-600">
          {application.business_name}
        </Link>
        <span className="text-gray-300">/</span>
        <span className="text-sm text-gray-700">Results</span>
      </div>

      <div className="mb-6">
        <h1 className="text-2xl font-semibold text-gray-900">Underwriting Results</h1>
        <p className="text-sm text-gray-500 mt-1">
          {application.business_name} — ${application.loan_amount.toLocaleString()} for {application.loan_term_months} months
        </p>
      </div>

      <div className="flex gap-4 mb-8">
        <div className="bg-green-50 border border-green-200 rounded-lg px-5 py-3 text-center">
          <div className="text-2xl font-bold text-green-700">{eligible.length}</div>
          <div className="text-xs text-green-600">Eligible Lenders</div>
        </div>
        <div className="bg-red-50 border border-red-200 rounded-lg px-5 py-3 text-center">
          <div className="text-2xl font-bold text-red-600">{ineligible.length}</div>
          <div className="text-xs text-red-500">Not Eligible</div>
        </div>
      </div>

      {eligible.length > 0 && (
        <section className="mb-8">
          <h2 className="text-lg font-semibold text-gray-900 mb-3">Eligible Lenders</h2>
          <div className="space-y-3">
            {eligible.map(match => (
              <MatchCard key={match.id} match={match} expanded={expanded === match.id} onToggle={() => setExpanded(expanded === match.id ? null : match.id)} />
            ))}
          </div>
        </section>
      )}

      {ineligible.length > 0 && (
        <section>
          <h2 className="text-lg font-semibold text-gray-900 mb-3">Not Eligible</h2>
          <div className="space-y-3">
            {ineligible.map(match => (
              <MatchCard key={match.id} match={match} expanded={expanded === match.id} onToggle={() => setExpanded(expanded === match.id ? null : match.id)} />
            ))}
          </div>
        </section>
      )}
    </div>
  )
}

function MatchCard({ match, expanded, onToggle }: { match: MatchResult; expanded: boolean; onToggle: () => void }) {
  const criteria = match.criterion_results ?? []
  const failed = criteria.filter(c => !c.passed && c.is_hard_reject)

  return (
    <div className={`bg-white rounded-lg border ${match.is_eligible ? 'border-gray-200' : 'border-gray-200'} overflow-hidden`}>
      <div
        className="flex items-center justify-between px-5 py-4 cursor-pointer hover:bg-gray-50"
        onClick={onToggle}
      >
        <div className="flex items-center gap-4">
          <div>
            <div className="font-medium text-gray-900">{match.lender.name}</div>
            {match.is_eligible ? (
              <div className="text-xs text-gray-400 mt-0.5">Program: {match.matched_program_name}</div>
            ) : (
              <div className="text-xs text-red-500 mt-0.5">
                {failed.length > 0 ? `${failed.length} criterion${failed.length > 1 ? 'ia' : ''} failed` : 'No applicable program'}
              </div>
            )}
          </div>
        </div>
        <div className="flex items-center gap-4">
          <ScoreBadge score={match.fit_score} eligible={match.is_eligible} />
          <span className="text-gray-400 text-sm">{expanded ? 'Hide' : 'Details'}</span>
        </div>
      </div>

      {expanded && (
        <div className="border-t border-gray-100">
          {!match.is_eligible && match.rejection_reasons && match.rejection_reasons.length > 0 && (
            <div className="px-5 py-3 bg-red-50 border-b border-red-100">
              <p className="text-xs font-semibold text-red-700 mb-1">Rejection reasons from best applicable program:</p>
              <ul className="text-xs text-red-600 space-y-0.5">
                {match.rejection_reasons.map((r, i) => <li key={i}>{r}</li>)}
              </ul>
            </div>
          )}

          {criteria.length > 0 ? (
            <div className="overflow-x-auto">
              <table className="min-w-full text-sm">
                <thead className="bg-gray-50 border-b border-gray-200">
                  <tr>
                    <th className="px-4 py-2 text-left text-xs text-gray-400 w-8" />
                    <th className="px-4 py-2 text-left text-xs text-gray-400">Criterion</th>
                    <th className="px-4 py-2 text-left text-xs text-gray-400">Actual</th>
                    <th className="px-4 py-2 text-left text-xs text-gray-400">Required</th>
                    <th className="px-4 py-2 text-left text-xs text-gray-400">Detail</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100">
                  {criteria.map((cr, i) => <CriterionRow key={i} result={cr} />)}
                </tbody>
              </table>
            </div>
          ) : (
            <p className="px-5 py-4 text-sm text-gray-400">No criteria details available.</p>
          )}
        </div>
      )}
    </div>
  )
}
