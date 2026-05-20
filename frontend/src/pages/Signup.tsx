import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { api, ApiError } from '../lib/api'
import { useAuth } from '../store/auth'

export function Signup() {
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
    if (password.length < 8) {
      setError('Password must be at least 8 characters.')
      return
    }
    setBusy(true)
    try {
      const t = await api.signup(email, password)
      setTokens(t.access_token, t.refresh_token)
      const me = await api.me()
      setUser(me)
      nav('/dashboard')
    } catch (e) {
      if (e instanceof ApiError) {
        if (e.status === 409) setError('That email is already registered.')
        else setError(safe(e.body))
      } else setError('Sign up failed')
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="max-w-sm mx-auto">
      <h1 className="text-2xl font-bold mb-4">Create account</h1>
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
          <span className="label">Password (min 8 chars)</span>
          <input
            className="input"
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
            minLength={8}
            autoComplete="new-password"
          />
        </label>
        {error && <p className="text-sm text-red-600">{error}</p>}
        <button className="btn-primary w-full" disabled={busy}>
          {busy ? 'Creating…' : 'Sign up'}
        </button>
        <p className="text-xs text-slate-500 text-center">
          Already have an account?{' '}
          <Link to="/login" className="text-brand-700 underline">
            Sign in
          </Link>
        </p>
      </form>
    </div>
  )
}

function safe(s: string): string {
  try {
    return JSON.parse(s).detail ?? s
  } catch {
    return s
  }
}
