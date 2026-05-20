import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { api, ApiError } from '../lib/api'
import { useAuth } from '../store/auth'

export function Login() {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)
  const setTokens = useAuth((s) => s.setTokens)
  const setUser = useAuth((s) => s.setUser)
  const nav = useNavigate()

  async function submit(e: React.FormEvent) {
    e.preventDefault()
    setError(null)
    setBusy(true)
    try {
      const t = await api.login(email, password)
      setTokens(t.access_token, t.refresh_token)
      const me = await api.me()
      setUser(me)
      nav(me.role === 'admin' ? '/admin' : '/dashboard')
    } catch (e) {
      setError(e instanceof ApiError ? readableError(e) : 'Login failed')
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="max-w-sm mx-auto">
      <h1 className="text-2xl font-bold mb-4">Sign in</h1>
      <form onSubmit={submit} className="card space-y-3">
        <label className="block">
          <span className="label">Email</span>
          <input
            className="input"
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
            autoComplete="email"
          />
        </label>
        <label className="block">
          <span className="label">Password</span>
          <input
            className="input"
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
            autoComplete="current-password"
          />
        </label>
        {error && <p className="text-sm text-red-600">{error}</p>}
        <button className="btn-primary w-full" disabled={busy}>
          {busy ? 'Signing in…' : 'Sign in'}
        </button>
        <p className="text-xs text-slate-500 text-center">
          No account?{' '}
          <Link to="/signup" className="text-brand-700 underline">
            Create one
          </Link>
        </p>
      </form>
    </div>
  )
}

function readableError(e: ApiError): string {
  if (e.status === 401) return 'Invalid email or password.'
  try {
    const j = JSON.parse(e.body)
    return j.detail ?? e.message
  } catch {
    return e.body || e.message
  }
}
