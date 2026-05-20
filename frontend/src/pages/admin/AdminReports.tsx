import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useState } from 'react'
import { api } from '../../lib/api'
import { timeAgo } from '../../lib/format'
import clsx from 'clsx'
import type { ScamReport } from '../../types'

const STATUSES: ScamReport['status'][] = ['open', 'reviewed', 'confirmed', 'dismissed']

export function AdminReports() {
  const [status, setStatus] = useState<string | null>(null)
  const qc = useQueryClient()
  const { data } = useQuery({
    queryKey: ['admin-reports', status],
    queryFn: () => api.adminReports(status ?? undefined),
  })

  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-bold">All scam reports</h1>
      <div className="flex gap-2 flex-wrap">
        <button className={clsx('btn-secondary', !status && '!bg-brand-600 !text-white !border-brand-600')} onClick={() => setStatus(null)}>All</button>
        {STATUSES.map((s) => (
          <button
            key={s}
            className={clsx('btn-secondary', status === s && '!bg-brand-600 !text-white !border-brand-600')}
            onClick={() => setStatus(s)}
          >
            {s}
          </button>
        ))}
      </div>

      <ul className="space-y-3">
        {(data ?? []).map((r) => (
          <ReportRow key={r.id} r={r} onUpdated={() => qc.invalidateQueries({ queryKey: ['admin-reports'] })} />
        ))}
        {data && data.length === 0 && (
          <li className="card text-sm text-slate-500">No reports for this filter.</li>
        )}
      </ul>
    </div>
  )
}

function ReportRow({ r, onUpdated }: { r: ScamReport; onUpdated: () => void }) {
  const [notes, setNotes] = useState(r.admin_notes ?? '')
  const [status, setStatus] = useState<ScamReport['status']>(r.status)
  const mut = useMutation({
    mutationFn: () => api.adminUpdateReport(r.id, { status, admin_notes: notes }),
    onSuccess: onUpdated,
  })

  return (
    <li className="card">
      <div className="flex items-center justify-between gap-3">
        <div className="min-w-0">
          <div className="font-semibold">{r.title}</div>
          <div className="text-xs text-slate-500">
            {timeAgo(r.created_at)} · user {r.user_id.slice(0, 8)}
          </div>
        </div>
        <span className={clsx(
          'pill',
          r.status === 'confirmed' ? 'bg-red-100 text-red-700' :
          r.status === 'dismissed' ? 'bg-slate-100 text-slate-700' :
          r.status === 'reviewed' ? 'bg-amber-100 text-amber-700' :
          'bg-blue-100 text-blue-700',
        )}>{r.status}</span>
      </div>
      <p className="mt-2 text-sm text-slate-700 whitespace-pre-wrap">{r.description}</p>
      {(r.company || r.url) && (
        <p className="mt-2 text-xs text-slate-500">
          {r.company && <>Company: <strong>{r.company}</strong>&nbsp;</>}
          {r.url && <a className="text-brand-700 underline" href={r.url} target="_blank" rel="noreferrer">{r.url}</a>}
        </p>
      )}
      <div className="mt-3 border-t border-slate-100 pt-3 grid grid-cols-1 md:grid-cols-2 gap-3 items-end">
        <label>
          <span className="label">Admin notes</span>
          <textarea className="input" value={notes} onChange={(e) => setNotes(e.target.value)} />
        </label>
        <div className="flex flex-wrap gap-2">
          {STATUSES.map((s) => (
            <button
              key={s}
              className={clsx('btn-secondary', status === s && '!bg-brand-600 !text-white !border-brand-600')}
              onClick={() => setStatus(s)}
            >
              {s}
            </button>
          ))}
          <button className="btn-primary" onClick={() => mut.mutate()} disabled={mut.isPending}>
            {mut.isPending ? 'Saving…' : 'Save'}
          </button>
        </div>
      </div>
    </li>
  )
}
