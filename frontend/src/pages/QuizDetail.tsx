import { useState } from 'react'
import { useQuery, useMutation } from '@tanstack/react-query'
import { useParams, Link } from 'react-router-dom'
import { api, ApiError } from '../lib/api'
import type { QuizResult } from '../types'
import { motion } from 'framer-motion'
import clsx from 'clsx'
import { pct } from '../lib/format'

export function QuizDetail() {
  const { slug = '' } = useParams()
  const { data: quiz } = useQuery({
    queryKey: ['quiz', slug],
    queryFn: () => api.getQuiz(slug),
    enabled: !!slug,
  })
  const [answers, setAnswers] = useState<Record<number, number>>({})
  const [result, setResult] = useState<QuizResult | null>(null)
  const [error, setError] = useState<string | null>(null)
  const submit = useMutation({
    mutationFn: (payload: number[]) => api.submitQuiz(slug, payload),
    onSuccess: (r) => { setResult(r); setError(null) },
    onError: (e) => setError(e instanceof ApiError ? e.body : 'Submit failed'),
  })

  if (!quiz) return <p className="text-sm text-slate-500">Loading…</p>

  const total = quiz.questions.length

  function trySubmit() {
    if (!quiz) return
    if (Object.keys(answers).length !== total) {
      setError(`Answer all ${total} questions first.`)
      return
    }
    submit.mutate(quiz.questions.map((_, i) => answers[i]))
  }

  return (
    <article className="max-w-2xl mx-auto space-y-4">
      <Link to="/awareness" className="text-xs text-brand-700 underline">
        ← Awareness module
      </Link>
      <header className="card">
        <h1 className="text-2xl font-bold">{quiz.title}</h1>
        <p className="text-sm text-slate-600 mt-1">{quiz.description}</p>
      </header>

      {!result && (
        <ol className="space-y-3">
          {quiz.questions.map((q, i) => (
            <li key={q.id} className="card">
              <p className="font-medium">
                {i + 1}. {q.prompt}
              </p>
              <div className="mt-2 space-y-1">
                {q.choices.map((c, ci) => (
                  <label key={ci} className="flex items-center gap-2 text-sm cursor-pointer">
                    <input
                      type="radio"
                      name={`q-${i}`}
                      checked={answers[i] === ci}
                      onChange={() => setAnswers({ ...answers, [i]: ci })}
                    />
                    {c}
                  </label>
                ))}
              </div>
            </li>
          ))}
          {error && <p className="text-sm text-red-600">{error}</p>}
          <button className="btn-primary" onClick={trySubmit} disabled={submit.isPending}>
            {submit.isPending ? 'Submitting…' : 'Submit answers'}
          </button>
        </ol>
      )}

      {result && (
        <motion.section initial={{ opacity: 0, y: 6 }} animate={{ opacity: 1, y: 0 }} className="card">
          <h2 className="text-xl font-bold">
            {result.correct} / {result.total} correct ({pct(result.score, 0)})
          </h2>
          <ol className="mt-4 space-y-3">
            {result.breakdown.map((b, i) => {
              const q = quiz.questions[i]
              return (
                <li key={b.question_id} className={clsx('border-l-4 pl-3 py-1', b.is_correct ? 'border-emerald-500' : 'border-red-500')}>
                  <p className="font-medium text-sm">{q.prompt}</p>
                  <p className="text-xs text-slate-600 mt-1">
                    Your answer: <strong>{q.choices[b.user_answer]}</strong>
                    {!b.is_correct && (
                      <>
                        {' '}— correct: <strong>{q.choices[b.correct_index]}</strong>
                      </>
                    )}
                  </p>
                  {b.explanation && <p className="text-xs text-slate-500 mt-1 italic">{b.explanation}</p>}
                </li>
              )
            })}
          </ol>
          <div className="mt-4 flex gap-2">
            <button className="btn-secondary" onClick={() => { setResult(null); setAnswers({}) }}>
              Retake
            </button>
            <Link to="/awareness" className="btn-secondary">Back to awareness</Link>
          </div>
        </motion.section>
      )}
    </article>
  )
}
