import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { api } from '../lib/api'
import { useAuth } from '../store/auth'

export function Awareness() {
  const { data: articles } = useQuery({ queryKey: ['articles'], queryFn: () => api.listArticles() })
  const { data: quizzes } = useQuery({ queryKey: ['quizzes'], queryFn: () => api.listQuizzes() })
  const user = useAuth((s) => s.user)

  return (
    <div className="space-y-8">
      <header>
        <h1 className="text-2xl font-bold">Awareness module</h1>
        <p className="text-sm text-slate-600 mt-1">
          Short, practical articles + quizzes covering how fake job postings work.
        </p>
      </header>

      <section>
        <h2 className="text-lg font-semibold mb-2">Articles</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          {(articles ?? []).map((a) => (
            <Link to={`/awareness/articles/${a.slug}`} key={a.slug} className="card hover:shadow-md transition">
              <div className="flex items-center justify-between">
                <h3 className="font-semibold">{a.title}</h3>
                <div className="flex flex-wrap gap-1">
                  {(a.tags ?? []).slice(0, 2).map((t) => (
                    <span key={t} className="pill-muted">{t}</span>
                  ))}
                </div>
              </div>
              <p className="text-sm text-slate-600 mt-2 line-clamp-2">{a.summary}</p>
              <p className="text-xs text-brand-700 mt-3 underline">Read article →</p>
            </Link>
          ))}
          {articles && articles.length === 0 && (
            <p className="text-sm text-slate-500">No articles yet.</p>
          )}
        </div>
      </section>

      <section>
        <h2 className="text-lg font-semibold mb-2">Quizzes</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          {(quizzes ?? []).map((q) => (
            <div key={q.slug} className="card">
              <h3 className="font-semibold">{q.title}</h3>
              <p className="text-sm text-slate-600 mt-1">{q.description}</p>
              <p className="text-xs text-slate-500 mt-2">{q.questions.length} questions</p>
              {user ? (
                <Link to={`/awareness/quizzes/${q.slug}`} className="btn-primary mt-3 w-max">
                  Start quiz
                </Link>
              ) : (
                <Link to="/signup" className="btn-secondary mt-3 w-max">
                  Sign up to take quiz
                </Link>
              )}
            </div>
          ))}
          {quizzes && quizzes.length === 0 && (
            <p className="text-sm text-slate-500">No quizzes yet.</p>
          )}
        </div>
      </section>
    </div>
  )
}
