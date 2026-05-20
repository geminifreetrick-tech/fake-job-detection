import { Link } from 'react-router-dom'
import { motion } from 'framer-motion'
import { useAuth } from '../store/auth'

export function Landing() {
  const user = useAuth((s) => s.user)
  return (
    <div className="space-y-10">
      <section className="relative overflow-hidden rounded-xl bg-gradient-to-br from-brand-700 to-brand-900 text-white p-8 sm:p-12">
        <motion.h1
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          className="text-3xl sm:text-4xl font-bold leading-tight"
        >
          Detect fake job postings before they reach your inbox.
        </motion.h1>
        <p className="mt-4 max-w-2xl text-brand-100 leading-relaxed">
          The Fake-Job Detection &amp; Awareness System pairs an explainable ML
          fraud classifier with OCR support for PDFs/images, real-time alerts,
          and an awareness module so you learn the patterns scammers use.
        </p>
        <div className="mt-6 flex flex-wrap gap-3">
          <Link to={user ? '/analyze' : '/signup'} className="btn-primary bg-white !text-brand-700 hover:bg-brand-50">
            {user ? 'Analyze a posting' : 'Create a free account'}
          </Link>
          <Link to="/awareness" className="btn-secondary !bg-transparent !text-white !border-white/40 hover:!bg-white/10">
            Browse awareness module
          </Link>
        </div>
      </section>

      <section className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Feature
          title="Explainable ML"
          body="XGBoost + SHAP surfaces the top features that drove the verdict — salary anomalies, suspicious URLs, grammar drift."
        />
        <Feature
          title="OCR-aware"
          body="Upload PDFs or screenshots; PyMuPDF + Tesseract extracts text before classification."
        />
        <Feature
          title="Company verification"
          body="Cross-checks company name against Google Custom Search + WHOIS to score legitimacy."
        />
      </section>

      <section className="card">
        <h2 className="text-lg font-semibold">How it works</h2>
        <ol className="mt-3 space-y-2 text-sm text-slate-700 list-decimal list-inside">
          <li>Paste a job ad or upload the screenshot/PDF on the Analyze page.</li>
          <li>Our ML engine returns a fraud probability and the top 8 reasons behind it.</li>
          <li>If suspicious, you can verify the listed company against the public web and submit a scam report for the community.</li>
          <li>Take the Awareness quizzes to sharpen your instincts.</li>
        </ol>
      </section>
    </div>
  )
}

function Feature({ title, body }: { title: string; body: string }) {
  return (
    <motion.div whileHover={{ y: -2 }} className="card">
      <h3 className="font-semibold">{title}</h3>
      <p className="mt-2 text-sm text-slate-600 leading-6">{body}</p>
    </motion.div>
  )
}
