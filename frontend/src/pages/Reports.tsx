import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { api, ApiError } from '../lib/api'
import { timeAgo } from '../lib/format'
import clsx from 'clsx'

export function Reports() {
  const qc = useQueryClient()
  const { data: reports } = useQuery({ queryKey: ['my-reports'], queryFn: () => api.myReports() })
  const [form, setForm] = useState({ title: '', description: '', company: '', url: '' })
  const [error, setError] = useState<string | null>(null)
  const submit = useMutation({
    mutationFn: () =>
      api.submitReport({
        title: form.title,
        description: form.description,
        company: form.company || undefined,
        url: form.url || undefined,
      }),
    onSuccess: () => {
      setForm({ title: '', description: '', company: '', url: '' })
      setError(null)
      qc.invalidateQueries({ queryKey: ['my-reports'] })
    },
    onError: (e) => setError(e instanceof ApiError ? e.body : 'Submit failed'),
  })

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
      <section className="card">
        <h1 className="text-xl font-bold">Report a suspicious posting</h1>
        <p className="text-sm text-slate-600 mt-1">
          Anything you submit is reviewed by admins and helps train the model.
        </p>
        <form
          className="mt-4 space-y-3"
          onSubmit={(e) => {
            e.preventDefault()
            submit.mutate()
          }}
        >
          <label className="block">
            <span className="label">Title *</span>
            <input
              className="input"
              required
              value={form.title}
              onChange={(e) => setForm({ ...form, title: e.target.value })}
            />
          </label>
          <label className="block">
            <span className="label">Description *</span>
            <textarea
              className="input min-h-[120px]"
              required
              value={form.description}
              onChange={(e) => setForm({ ...form, description: e.target.value })}
            />
          </label>
          <label className="block">
            <span className="label">Company (optional)</span>
            <input
              className="input"
              value={form.company}
              onChange={(e) => setForm({ ...form, company: e.target.value })}
            />
          </label>
          <label className="block">
            <span className="label">URL (optional)</span>
            <input
              className="input"
              type="url"
              value={form.url}
              onChange={(e) => setForm({ ...form, url: e.target.value })}
            />
          </label>
          {error && <p className="text-sm text-red-600">{error}</p>}
          <button className="btn-primary" disabled={submit.isPending}>
            {submit.isPending ? 'Submitting…' : 'Submit report'}
          </button>
        </form>
      </section>

      <section className="card">
        <h2 className="font-semibold">My reports</h2>
        <ul className="mt-3 divide-y divide-slate-100">
          {(reports ?? []).map((r) => (
            <li key={r.id} className="py-3">
              <div className="flex items-center justify-between gap-3">
                <span className="font-medium">{r.title}</span>
                <span className={clsx(
                  'pill',
                  r.status === 'confirmed' ? 'bg-red-100 text-red-700' :
                  r.status === 'dismissed' ? 'bg-slate-100 text-slate-700' :
                  r.status === 'reviewed' ? 'bg-amber-100 text-amber-700' :
                  'bg-blue-100 text-blue-700',
                )}>{r.status}</span>
              </div>
              <p className="text-sm text-slate-600 mt-1 line-clamp-2">{r.description}</p>
              <p className="text-xs text-slate-400 mt-1">{timeAgo(r.created_at)}</p>
              {r.admin_notes && (
                <p className="text-xs text-slate-500 mt-1">
                  <span className="font-medium">Admin: </span>{r.admin_notes}
                </p>
              )}
            </li>
          ))}
          {reports && reports.length === 0 && (
            <li className="py-6 text-sm text-slate-500">No reports yet.</li>
          )}
        </ul>
      </section>
    </div>
  )
}
