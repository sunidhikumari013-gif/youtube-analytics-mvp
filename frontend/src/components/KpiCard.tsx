interface KpiCardProps {
  label: string
  value: string | number
  unit?: string
}

export default function KpiCard({ label, value, unit }: KpiCardProps) {
  return (
    <div className="bg-white rounded-xl shadow p-6">
      <p className="text-sm text-gray-500 font-medium uppercase tracking-wide mb-1">{label}</p>
      <p className="text-3xl font-bold text-gray-800">
        {typeof value === 'number' ? value.toLocaleString() : value}
        {unit && <span className="text-base font-normal text-gray-500 ml-1">{unit}</span>}
      </p>
    </div>
  )
}
