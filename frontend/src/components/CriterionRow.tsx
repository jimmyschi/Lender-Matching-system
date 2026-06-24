import type { CriterionResult } from '../types'

interface Props {
  result: CriterionResult
}

export default function CriterionRow({ result }: Props) {
  const passIcon = result.passed
    ? <span className="text-green-500 font-bold">&#10003;</span>
    : <span className="text-red-500 font-bold">&#10007;</span>

  return (
    <tr className={result.passed ? '' : 'bg-red-50'}>
      <td className="px-4 py-3 text-sm w-8 text-center">{passIcon}</td>
      <td className="px-4 py-3 text-sm font-medium text-gray-800">
        {result.criterion_label}
        {result.is_hard_reject && (
          <span className="ml-1.5 text-xs text-gray-400">(required)</span>
        )}
      </td>
      <td className="px-4 py-3 text-sm text-gray-600">{result.actual_value}</td>
      <td className="px-4 py-3 text-sm text-gray-600">{result.required_value}</td>
      <td className="px-4 py-3 text-sm text-gray-500">{result.explanation}</td>
    </tr>
  )
}
