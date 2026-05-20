import { Navigate, Route, Routes } from 'react-router-dom'
import { useEffect } from 'react'
import { Layout } from './components/Layout'
import { Login } from './pages/Login'
import { Signup } from './pages/Signup'
import { Dashboard } from './pages/Dashboard'
import { Analyze } from './pages/Analyze'
import { History } from './pages/History'
import { Reports } from './pages/Reports'
import { CompanyCheck } from './pages/CompanyCheck'
import { Awareness } from './pages/Awareness'
import { ArticleDetail } from './pages/ArticleDetail'
import { QuizDetail } from './pages/QuizDetail'
import { AdminDashboard } from './pages/admin/AdminDashboard'
import { AdminReports } from './pages/admin/AdminReports'
import { useAuth } from './store/auth'
import { api } from './lib/api'
import { Landing } from './pages/Landing'

function RequireAuth({ children, role }: { children: JSX.Element; role?: 'admin' }) {
  const token = useAuth((s) => s.accessToken)
  const user = useAuth((s) => s.user)
  if (!token) return <Navigate to="/login" replace />
  if (role && user?.role !== role) return <Navigate to="/dashboard" replace />
  return children
}

export function App() {
  const token = useAuth((s) => s.accessToken)
  const setUser = useAuth((s) => s.setUser)
  const logout = useAuth((s) => s.logout)

  useEffect(() => {
    if (!token) return
    api
      .me()
      .then((u) => setUser(u))
      .catch(() => logout())
  }, [token, setUser, logout])

  return (
    <Routes>
      <Route path="/" element={<Layout />}>
        <Route index element={<Landing />} />
        <Route path="login" element={<Login />} />
        <Route path="signup" element={<Signup />} />
        <Route path="dashboard" element={<RequireAuth><Dashboard /></RequireAuth>} />
        <Route path="analyze" element={<RequireAuth><Analyze /></RequireAuth>} />
        <Route path="history" element={<RequireAuth><History /></RequireAuth>} />
        <Route path="reports" element={<RequireAuth><Reports /></RequireAuth>} />
        <Route path="company-check" element={<RequireAuth><CompanyCheck /></RequireAuth>} />
        <Route path="awareness" element={<Awareness />} />
        <Route path="awareness/articles/:slug" element={<ArticleDetail />} />
        <Route path="awareness/quizzes/:slug" element={<RequireAuth><QuizDetail /></RequireAuth>} />
        <Route path="admin" element={<RequireAuth role="admin"><AdminDashboard /></RequireAuth>} />
        <Route path="admin/reports" element={<RequireAuth role="admin"><AdminReports /></RequireAuth>} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Route>
    </Routes>
  )
}
