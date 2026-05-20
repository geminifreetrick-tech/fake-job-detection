import { Link, NavLink, Outlet, useNavigate } from 'react-router-dom'
import { useAuth } from '../store/auth'
import clsx from 'clsx'

const linkBase = 'px-3 py-2 text-sm rounded-md hover:bg-slate-100 transition'
const navItem = ({ isActive }: { isActive: boolean }) =>
  clsx(linkBase, isActive ? 'bg-slate-100 text-brand-700 font-semibold' : 'text-slate-700')

export function Layout() {
  const user = useAuth((s) => s.user)
  const logout = useAuth((s) => s.logout)
  const nav = useNavigate()

  return (
    <div className="min-h-screen flex flex-col">
      <header className="bg-white border-b border-slate-200 sticky top-0 z-10">
        <div className="max-w-6xl mx-auto px-4 py-3 flex items-center gap-2">
          <Link to="/" className="font-bold text-brand-700 mr-4">
            Fake-Job Detection
          </Link>
          <nav className="flex flex-1 items-center gap-1 overflow-x-auto">
            <NavLink to="/awareness" className={navItem}>Awareness</NavLink>
            {user && <NavLink to="/dashboard" className={navItem}>Dashboard</NavLink>}
            {user && <NavLink to="/analyze" className={navItem}>Analyze</NavLink>}
            {user && <NavLink to="/history" className={navItem}>History</NavLink>}
            {user && <NavLink to="/reports" className={navItem}>Reports</NavLink>}
            {user && <NavLink to="/company-check" className={navItem}>Company check</NavLink>}
            {user?.role === 'admin' && <NavLink to="/admin" className={navItem}>Admin</NavLink>}
          </nav>
          <div className="flex items-center gap-2">
            {user ? (
              <>
                <span className="text-xs text-slate-600 hidden sm:inline">{user.email}</span>
                <button
                  className="btn-secondary"
                  onClick={() => {
                    logout()
                    nav('/')
                  }}
                >
                  Sign out
                </button>
              </>
            ) : (
              <>
                <Link to="/login" className="btn-secondary">Sign in</Link>
                <Link to="/signup" className="btn-primary">Sign up</Link>
              </>
            )}
          </div>
        </div>
      </header>
      <main className="flex-1 max-w-6xl w-full mx-auto px-4 py-6">
        <Outlet />
      </main>
      <footer className="border-t border-slate-200 bg-white">
        <div className="max-w-6xl mx-auto px-4 py-4 text-xs text-slate-500 flex justify-between">
          <span>Fake-Job Detection &amp; Awareness System</span>
          <span>v0.2.0</span>
        </div>
      </footer>
    </div>
  )
}
