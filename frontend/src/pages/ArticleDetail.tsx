import { useQuery } from '@tanstack/react-query'
import { Link, useParams } from 'react-router-dom'
import { api } from '../lib/api'
import { Markdown } from '../lib/markdown'

export function ArticleDetail() {
  const { slug = '' } = useParams()
  const { data, isLoading, isError } = useQuery({
    queryKey: ['article', slug],
    queryFn: () => api.getArticle(slug),
    enabled: !!slug,
  })

  if (isLoading) return <p className="text-sm text-slate-500">Loading…</p>
  if (isError || !data) return <p className="text-sm text-red-600">Article not found.</p>

  return (
    <article className="max-w-3xl mx-auto card">
      <Link to="/awareness" className="text-xs text-brand-700 underline">
        ← Awareness module
      </Link>
      <h1 className="text-3xl font-bold mt-2">{data.title}</h1>
      <div className="flex flex-wrap gap-1 mt-2">
        {(data.tags ?? []).map((t) => (
          <span key={t} className="pill-muted">{t}</span>
        ))}
      </div>
      <p className="mt-4 text-slate-600 italic">{data.summary}</p>
      <div className="mt-6 border-t border-slate-200 pt-5">
        <Markdown source={data.body_md} />
      </div>
    </article>
  )
}
