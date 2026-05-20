import type {
  AdminDashboard,
  AnalysisResponse,
  Article,
  CompanyVerification,
  JobWithPrediction,
  QuizPublic,
  QuizResult,
  ScamReport,
  User,
} from '../types'
import { authStore } from '../store/auth'

export class ApiError extends Error {
  constructor(public status: number, public body: string) {
    super(`HTTP ${status}: ${body}`)
  }
}

const BASE = '/api/v1'

async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  const token = authStore.getState().accessToken
  const headers = new Headers(init.headers)
  if (token) headers.set('Authorization', `Bearer ${token}`)
  if (init.body && !(init.body instanceof FormData) && !headers.has('Content-Type')) {
    headers.set('Content-Type', 'application/json')
  }
  const res = await fetch(`${BASE}${path}`, { ...init, headers })
  if (res.status === 401) {
    authStore.getState().logout()
  }
  if (!res.ok) {
    const body = await res.text().catch(() => '')
    throw new ApiError(res.status, body)
  }
  const ct = res.headers.get('content-type') || ''
  if (ct.includes('application/json')) {
    return (await res.json()) as T
  }
  return (await res.text()) as unknown as T
}

// ---- Auth
export const api = {
  signup: (email: string, password: string) =>
    request<{ access_token: string; refresh_token: string }>('/auth/signup', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    }),
  login: (email: string, password: string) =>
    request<{ access_token: string; refresh_token: string }>('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    }),
  me: () => request<User>('/me'),

  // ---- Jobs
  analyzeText: (text: string) =>
    request<AnalysisResponse>('/jobs/analyze', {
      method: 'POST',
      body: JSON.stringify({ text }),
    }),
  analyzeFile: (file: File) => {
    const fd = new FormData()
    fd.append('file', file)
    return request<AnalysisResponse>('/jobs/analyze-file', { method: 'POST', body: fd })
  },
  myJobs: () => request<JobWithPrediction[]>('/me/jobs'),
  myContext: () => request<{ recent: unknown[]; similar_scams: unknown[] }>('/me/context'),

  // ---- Reports
  submitReport: (body: { title: string; description: string; company?: string; url?: string; job_id?: string }) =>
    request<ScamReport>('/reports', { method: 'POST', body: JSON.stringify(body) }),
  myReports: () => request<ScamReport[]>('/reports/mine'),

  // ---- Awareness
  listArticles: (tag?: string) =>
    request<Article[]>(`/awareness/articles${tag ? `?tag=${encodeURIComponent(tag)}` : ''}`),
  getArticle: (slug: string) => request<Article>(`/awareness/articles/${slug}`),
  listQuizzes: () => request<QuizPublic[]>('/awareness/quizzes'),
  getQuiz: (slug: string) => request<QuizPublic>(`/awareness/quizzes/${slug}`),
  submitQuiz: (quiz_slug: string, answers: number[]) =>
    request<QuizResult>('/awareness/quizzes/submit', {
      method: 'POST',
      body: JSON.stringify({ quiz_slug, answers }),
    }),

  // ---- Companies
  verifyCompany: (name: string, domain?: string) =>
    request<CompanyVerification>('/companies/verify', {
      method: 'POST',
      body: JSON.stringify({ name, domain }),
    }),

  // ---- Files
  generateReport: (job_id: string) =>
    request<{ sha256: string; size: number; content_type: string }>(
      `/files/reports/${job_id}`,
      { method: 'POST' },
    ),
  reportUrl: (sha: string) => `${BASE}/files/reports/${sha}`,

  // ---- Admin
  adminDashboard: () => request<AdminDashboard>('/admin/dashboard'),
  adminReports: (status?: string) =>
    request<ScamReport[]>(`/admin/reports${status ? `?status=${status}` : ''}`),
  adminUpdateReport: (
    id: string,
    body: { status?: ScamReport['status']; admin_notes?: string },
  ) =>
    request<ScamReport>(`/admin/reports/${id}`, {
      method: 'PATCH',
      body: JSON.stringify(body),
    }),
}
