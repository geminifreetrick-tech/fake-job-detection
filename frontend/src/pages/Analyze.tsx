import { useState } from 'react'
import { api, ApiError } from '../lib/api'
import type { AnalysisResponse } from '../types'
import { ScoreMeter } from '../components/ScoreMeter'
import { ExplanationsTable } from '../components/ExplanationsTable'
import { useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'

const SAMPLE = `URGENT HIRING! Work-from-home data-entry. Earn $5000/week.
No experience required. Pay $99 onboarding fee. WhatsApp +1-555-0100.`

export function Analyze() {
  const [text, setText] = useState('')
  const [file, setFile] = useState<File | null>(null)
  const [busy, setBusy] = useState(false)
  const [result, setResult] = useState<AnalysisResponse | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [reportSha, setReportSha] = useState<string | null>(null)
  const nav = useNavigate()

  async function submitText() {
    if (!text.trim()) {
      setError('Paste a job posting first.')
      return
    }
    setBusy(true); setError(null); setReportSha(null)
    try {
      const r = await api.analyzeText(text)
      setResult(r)
    } catch (e) {
      setError(e instanceof ApiError ? safe(e.body) : 'Analysis failed')
    } finally { setBusy(false) }
  }

  async function submitFile() {
    if (!file) {
      setError('Choose a PDF or image first.')
      return
    }
    setBusy(true); setError(null); setReportSha(null)
    try {
      const r = await api.analyzeFile(file)
      setResult(r)
    } catch (e) {
      setError(e instanceof ApiError ? safe(e.body) : 'Analysis failed')
    } finally { setBusy(false) }
  }

  async function generatePdf() {
    if (!result) return
    try {
      const r = await api.generateReport(result.job_id)
      setReportSha(r.sha256)
    } catch (e) {
      setError(e instanceof ApiError ? safe(e.body) : 'Could not generate PDF')
    }
  }

  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
      <div className="lg:col-span-2 space-y-6">
        <section className="card">
          <h1 className="text-xl font-bold">Analyse a job posting</h1>
          <p className="text-sm text-slate-600 mt-1">
            Paste the text below, or upload a PDF/image (we&apos;ll OCR it before classifying).
          </p>

          <div className="mt-4">
            <label className="label">Job-posting text</label>
            <textarea
              className="input min-h-[180px] font-mono text-xs"
              placeholder={SAMPLE}
              value={text}
              onChange={(e) => setText(e.target.value)}
            />
            <div className="flex gap-2 mt-3">
              <button className="btn-primary" onClick={submitText} disabled={busy}>
                {busy ? 'Analysing…' : 'Analyse text'}
              </button>
              <button
                className="btn-secondary"
                onClick={() => setText(SAMPLE)}
                disabled={busy}
              >
                Try sample
              </button>
            </div>
          </div>

          <div className="mt-6 border-t border-slate-200 pt-4">
            <label className="label">Or upload a PDF / image</label>
            <input
              className="input"
              type="file"
              accept="application/pdf,image/*"
              onChange={(e) => setFile(e.target.files?.[0] ?? null)}
            />
            <button className="btn-primary mt-3" onClick={submitFile} disabled={busy || !file}>
              {busy ? 'Analysing…' : 'Analyse upload'}
            </button>
          </div>

          {error && <p className="mt-4 text-sm text-red-600">{error}</p>}
        </section>
      </div>

      <div className="space-y-6">
        {result && (
          <motion.div initial={{ opacity: 0, y: 6 }} animate={{ opacity: 1, y: 0 }} className="card space-y-4">
            <ScoreMeter score={result.score} label={result.label} />
            <div className="text-xs text-slate-500 flex gap-2 flex-wrap">
              <span>Model {result.model_version}</span>
              <span>·</span>
              <span>Source: {result.source_type}</span>
              {result.ocr && (
                <>
                  <span>·</span>
                  <span>OCR: {result.ocr.used_ocr ? 'used' : 'not used'} ({result.ocr.pages} pages)</span>
                </>
              )}
            </div>
            <div className="flex flex-wrap gap-2 pt-2 border-t border-slate-100">
              <button className="btn-secondary" onClick={generatePdf}>
                Generate PDF report
              </button>
              {reportSha && (
                <a className="btn-secondary" href={api.reportUrl(reportSha)} target="_blank" rel="noreferrer">
                  Download PDF
                </a>
              )}
              <button className="btn-secondary" onClick={() => nav('/reports')}>
                Report to admins
              </button>
            </div>
          </motion.div>
        )}

        {result && (
          <section className="card">
            <h2 className="font-semibold mb-2">Top features</h2>
            <ExplanationsTable items={result.explanations} />
          </section>
        )}
      </div>
    </div>
  )
}

function safe(s: string): string {
  try { return JSON.parse(s).detail ?? s } catch { return s }
}
