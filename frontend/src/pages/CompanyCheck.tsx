import { useState } from 'react'
import { api, ApiError } from '../lib/api'
import type { CompanyVerification } from '../types'
import clsx from 'clsx'
import { pct } from '../lib/format'

export function CompanyCheck() {
  const [name, setName] = useState('')
  const [domain, setDomain] = useState('')
  const [busy, setBusy] = useState(false)
  const [result, setResult] = useState<CompanyVerification | null>(null)
  const [error, setError] = useState<string | null>(null)

  async function submit() {
    setBusy(true); setError(null)
    try {
      const r = await api.verifyCompany(name, domain || undefined)
      setResult(r)
    } catch (e) {
      setError(e instanceof ApiError ? e.body : 'Lookup failed')
    } finally { setBusy(false) }
  }

  const legit = result && result.legitimacy_score >= 0.6

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
      <section className="card">
        <h1 className="text-xl font-bold">Verify a company</h1>
        <p className="text-sm text-slate-600 mt-1">
          Cross-checks the name against Google Custom Search + WHOIS to estimate legitimacy.
        </p>
        <div className="mt-4 space-y-3">
          <label className="block">
            <span className="label">Company name *</span>
            <input className="input" value={name} onChange={(e) => setName(e.target.value)} placeholder="Acme Corporation" />
          </label>
          <label className="block">
            <span className="label">Domain (optional)</span>
            <input className="input" value={domain} onChange={(e) => setDomain(e.target.value)} placeholder="acme.com" />
          </label>
          <button className="btn-primary" disabled={busy || !name.trim()} onClick={submit}>
            {busy ? 'Verifying…' : 'Verify'}
          </button>
          {error && <p className="text-sm text-red-600 mt-1">{error}</p>}
        </div>
      </section>

      {result && (
        <section className="card space-y-4">
          <div>
            <div className={clsx(
              'text-2xl font-bold',
              legit ? 'text-emerald-700' : result.legitimacy_score >= 0.4 ? 'text-amber-700' : 'text-red-700',
            )}>
              {pct(result.legitimacy_score, 0)} legitimacy
              {result.from_cache && <span className="ml-2 text-xs font-normal text-slate-500">(cached)</span>}
            </div>
            <div className="h-2 mt-2 rounded-full bg-slate-100 overflow-hidden">
              <div
                className={clsx('h-full', legit ? 'bg-emerald-500' : result.legitimacy_score >= 0.4 ? 'bg-amber-500' : 'bg-red-500')}
                style={{ width: `${Math.round(result.legitimacy_score * 100)}%` }}
              />
            </div>
          </div>

          {result.whois && (
            <div>
              <h3 className="font-semibold text-sm mb-1">WHOIS signals</h3>
              <pre className="text-xs bg-slate-50 p-2 rounded overflow-x-auto">{JSON.stringify(result.whois, null, 2)}</pre>
            </div>
          )}

          {result.search_results && result.search_results.length > 0 && (
            <div>
              <h3 className="font-semibold text-sm mb-1">Top search hits</h3>
              <ul className="space-y-2">
                {result.search_results.slice(0, 5).map((r) => (
                  <li key={r.url} className="text-sm">
                    <a className="text-brand-700 underline truncate block" href={r.url} target="_blank" rel="noreferrer">{r.title}</a>
                    <span className="text-xs text-slate-500">{r.display_link}</span>
                    <p className="text-xs text-slate-600 mt-0.5 line-clamp-2">{r.snippet}</p>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {result.signals && (
            <div>
              <h3 className="font-semibold text-sm mb-1">Signals</h3>
              <pre className="text-xs bg-slate-50 p-2 rounded overflow-x-auto">{JSON.stringify(result.signals, null, 2)}</pre>
            </div>
          )}

          <p className="text-xs text-slate-500">
            Provider: {result.provider}.{' '}
            {result.provider === 'fallback' && 'Add GOOGLE_CSE_API_KEY + GOOGLE_CSE_ENGINE_ID for richer results.'}
          </p>
        </section>
      )}
    </div>
  )
}
