import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { api } from '../lib/api'
import { useAuth } from '../store/auth'
import { pct, timeAgo } from '../lib/format'
import { motion } from 'framer-motion'
import clsx from 'clsx'

export function Dashboard() {
  const user = useAuth((s) => s.user)
  const { data: history } = useQuery({ queryKey: ['my-jobs'], queryFn: () => api.myJobs() })
  const { data: reports } = useQuery({ queryKey: ['my-reports'], queryFn: () => api.myReports() })

  const stats = (() => {
    const items = history ?? []
    const fraud = items.filter((i) => i.prediction?.label === 'fraud').length
    const total = items.length
    return {
      total,
      fraud,
      legit: total - fraud,
      rate: total ? fraud / total : 0,
    }
  })()

  return (
    <div className="space-y-6">
      <div className="flex items-baseline justify-between">
        <h1 className="text-2xl font-bold">Welcome, {user?.email}</h1>
        <Link className="btn-primary" to="/analyze">Analyze a posting</Link>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        <Stat title="Analyses" value={stats.total} />
        <Stat title="Fraud flagged" value={stats.fraud} danger />
        <Stat title="Likely legit" value={stats.legit} />
        <Stat title="Fraud rate" value={pct(stats.rate)} />
      </div>

      <section className="card">
        <div className="flex items-baseline justify-between">
          <h2 className="font-semibold">Recent analyses</h2>
          <Link className="text-sm text-brand-700 underline" to="/history">
            View all
          </Link>
        </div>
        <ul className="mt-3 divide-y divide-slate-100">
          {(history ?? []).slice(0, 5).map(({ job, prediction }) => (
            <li key={job.id} className="py-3 flex items-center justify-between gap-3">
              <div className="min-w-0">
                <div className="truncate text-sm">
                  {(job.raw_text || '(no text)').slice(0, 120)}
                </div>
                <div className="text-xs text-slate-500 mt-0.5">
                  {timeAgo(job.created_at)} · {job.source_type}
                </div>
              </div>
              {prediction && (
                <span className={prediction.label === 'fraud' ? 'pill-fraud' : 'pill-legit'}>
                  {prediction.label} {pct(prediction.score, 0)}
                </span>
              )}
            </li>
          ))}
          {history && history.length === 0 && (
            <li className="py-6 text-sm text-slate-500">
              You haven&apos;t analysed any postings yet. <Link to="/analyze" className="text-brand-700 underline">Get started.</Link>
            </li>
          )}
        </ul>
      </section>

      <section className="card">
        <div className="flex items-baseline justify-between">
          <h2 className="font-semibold">My reports</h2>
          <Link className="text-sm text-brand-700 underline" to="/reports">
            Submit one
          </Link>
        </div>
        <ul className="mt-3 divide-y divide-slate-100">
          {(reports ?? []).slice(0, 5).map((r) => (
            <li key={r.id} className="py-3 flex items-center justify-between gap-3">
              <div className="min-w-0">
                <div className="truncate font-medium text-sm">{r.title}</div>
                <div className="text-xs text-slate-500">{timeAgo(r.created_at)}</div>
              </div>
              <span className={clsx(
                'pill',
                r.status === 'confirmed' ? 'bg-red-100 text-red-700' :
                r.status === 'dismissed' ? 'bg-slate-100 text-slate-700' :
                r.status === 'reviewed' ? 'bg-amber-100 text-amber-700' :
                'bg-blue-100 text-blue-700',
              )}>{r.status}</span>
            </li>
          ))}
          {reports && reports.length === 0 && (
            <li className="py-6 text-sm text-slate-500">No reports submitted yet.</li>
          )}
        </ul>
      </section>
    </div>
  )
}

function Stat({ title, value, danger }: { title: string; value: number | string; danger?: boolean }) {
  return (
    <motion.div whileHover={{ y: -2 }} className="card">
      <div className="text-xs uppercase tracking-wide text-slate-500">{title}</div>
      <div className={clsx('text-2xl font-bold mt-1', danger ? 'text-red-700' : 'text-slate-900')}>{value}</div>
    </motion.div>
  )
}
