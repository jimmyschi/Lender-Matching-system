interface Props {
  score: number
  eligible: boolean
}

export default function ScoreBadge({ score, eligible }: Props) {
  if (!eligible) {
    return (
      <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-red-100 text-red-700">
        Not Eligible
      </span>
    )
  }

  const color =
    score >= 80 ? 'bg-green-100 text-green-700' :
    score >= 60 ? 'bg-yellow-100 text-yellow-700' :
    'bg-orange-100 text-orange-700'

  return (
    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${color}`}>
      {score.toFixed(0)} / 100
    </span>
  )
}
