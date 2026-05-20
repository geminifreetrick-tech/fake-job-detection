import { useQuery } from '@tanstack/react-query'
import { api } from '../lib/api'
import { pct, safeDateTime } from '../lib/format'
import clsx from 'clsx'
import { useState } from 'react'
import type { JobWithPrediction } from '../types'
import { ExplanationsTable } from '../components/ExplanationsTable'

export function History() {
  const { data, isLoading } = useQuery({ queryKey: ['my-jobs'], queryFn: () => api.myJobs() })
  const [open, setOpen] = useState<string | null>(null)

  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-bold">Analysis history</h1>
      {isLoading && <p className="text-sm text-slate-500">Loading…</p>}
      {!isLoading && data && data.length === 0 && (
        <p className="text-sm text-slate-500">No analyses yet. Try the Analyze page.</p>
      )}
      <ul className="space-y-3">
        {(data ?? []).map((row) => (
          <HistoryRow key={row.job.id} row={row} open={open === row.job.id} onToggle={() => setOpen(open === row.job.id ? null : row.job.id)} />
        ))}
      </ul>
    </div>
  )
}

function HistoryRow({ row, open, onToggle }: { row: JobWithPrediction; open: boolean; onToggle: () => void }) {
  const p = row.prediction
  const danger = p?.label === 'fraud'
  return (
    <li className="card">
      <div className="flex items-center justify-between gap-3">
        <div className="min-w-0">
          <div className="font-mono text-xs text-slate-500">
            {safeDateTime(row.job.created_at)} · {row.job.source_type}
            {row.job.source_uri ? ` · ${row.job.source_uri}` : ''}
          </div>
          <div className="mt-1 text-sm truncate">
            {(row.job.raw_text || '(no text extracted)').slice(0, 220)}
          </div>
        </div>
        <div className="flex items-center gap-3 shrink-0">
          {p ? (
            <span className={clsx(
              'pill text-sm px-2.5 py-1',
              danger ? 'bg-red-100 text-red-700 ring-1 ring-red-200' : 'bg-emerald-100 text-emerald-700 ring-1 ring-emerald-200',
            )}>
              {p.label} {pct(p.score, 1)}
            </span>
          ) : (
            <span className="pill-muted">no prediction</span>
          )}
          <button className="btn-secondary" onClick={onToggle}>{open ? 'Hide' : 'Details'}</button>
        </div>
      </div>
      {open && p && (
        <div className="mt-4 border-t border-slate-100 pt-3">
          <ExplanationsTable items={p.explanation?.explanations ?? []} />
        </div>
      )}
    </li>
  )
}
