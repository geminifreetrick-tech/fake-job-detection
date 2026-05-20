import { useQuery } from '@tanstack/react-query'
import { api } from '../../lib/api'
import { pct } from '../../lib/format'
import {
  Bar,
  BarChart,
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import { Link } from 'react-router-dom'

export function AdminDashboard() {
  const { data, isLoading } = useQuery({
    queryKey: ['admin-dashboard'],
    queryFn: () => api.adminDashboard(),
    refetchInterval: 15_000,
  })

  if (isLoading || !data) return <p className="text-sm text-slate-500">Loading dashboard…</p>

  const fotData = mergeFraudOverTime(data.fraud_over_time)

  return (
    <div className="space-y-6">
      <div className="flex items-baseline justify-between">
        <h1 className="text-2xl font-bold">Admin dashboard</h1>
        <Link to="/admin/reports" className="btn-secondary">
          Review reports ({data.summary.reports_open})
        </Link>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        <Kpi title="Total analyses" value={data.summary.total_jobs} />
        <Kpi title="Fraud" value={data.summary.total_fraud} danger />
        <Kpi title="Legit" value={data.summary.total_legit} />
        <Kpi title="Fraud rate" value={pct(data.summary.fraud_rate)} />
        <Kpi title="Users" value={data.summary.users} />
        <Kpi title="Open reports" value={data.summary.reports_open} danger />
        <Kpi title="Avg fraud score" value={pct(data.summary.avg_fraud_score)} />
      </div>

      <section className="card">
        <h2 className="font-semibold mb-3">Daily detections (last 30 days)</h2>
        <div className="h-72">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={fotData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="day" />
              <YAxis allowDecimals={false} />
              <Tooltip />
              <Legend />
              <Line type="monotone" dataKey="fraud" stroke="#dc2626" strokeWidth={2} />
              <Line type="monotone" dataKey="legit" stroke="#059669" strokeWidth={2} />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </section>

      <section className="card">
        <h2 className="font-semibold mb-3">Top scam features</h2>
        <div className="h-72">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={data.top_features}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="feature" angle={-20} interval={0} height={50} textAnchor="end" />
              <YAxis allowDecimals={false} />
              <Tooltip />
              <Bar dataKey="count" fill="#2563eb" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </section>
    </div>
  )
}

function mergeFraudOverTime(fot: { fraud: { bucket: string; count: number }[]; legit: { bucket: string; count: number }[] }) {
  const idx = new Map<string, { day: string; fraud: number; legit: number }>()
  for (const r of fot.fraud ?? []) {
    const k = r.bucket.slice(0, 10)
    if (!idx.has(k)) idx.set(k, { day: k, fraud: 0, legit: 0 })
    idx.get(k)!.fraud += r.count
  }
  for (const r of fot.legit ?? []) {
    const k = r.bucket.slice(0, 10)
    if (!idx.has(k)) idx.set(k, { day: k, fraud: 0, legit: 0 })
    idx.get(k)!.legit += r.count
  }
  return [...idx.values()].sort((a, b) => (a.day < b.day ? -1 : 1))
}

function Kpi({ title, value, danger }: { title: string; value: number | string; danger?: boolean }) {
  return (
    <div className="card">
      <div className="text-xs uppercase tracking-wide text-slate-500">{title}</div>
      <div className={`text-2xl font-bold mt-1 ${danger ? 'text-red-700' : 'text-slate-900'}`}>{value}</div>
    </div>
  )
}
