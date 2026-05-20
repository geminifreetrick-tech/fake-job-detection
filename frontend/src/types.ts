export type Role = 'user' | 'admin'

export interface User {
  id: string
  email: string
  role: Role
  created_at: string
}

export interface Explanation {
  feature: string
  label: string
  value: number
  contribution: number
  direction: 'fraud' | 'legit' | 'neutral'
}

export interface OcrMeta {
  pages: number
  used_ocr: boolean
}

export interface AnalysisResponse {
  job_id: string
  prediction_id: string
  label: 'fraud' | 'legit'
  score: number
  explanations: Explanation[]
  features: Record<string, number>
  model_version: string
  source_type: 'text' | 'pdf' | 'image'
  ocr?: OcrMeta
}

export interface JobOut {
  id: string
  user_id: string
  raw_text: string
  source_type: 'text' | 'pdf' | 'image'
  source_uri?: string | null
  sha256: string
  created_at: string
}

export interface PredictionOut {
  id: string
  job_id: string
  label: 'fraud' | 'legit'
  score: number
  explanation: { explanations?: Explanation[]; features?: Record<string, number> }
  model_version: string
  created_at: string
}

export interface JobWithPrediction {
  job: JobOut
  prediction: PredictionOut | null
}

export interface Article {
  id: string
  slug: string
  title: string
  summary: string
  body_md: string
  tags: string[]
  published: boolean
  created_at: string
}

export interface QuizQuestionPublic {
  id: string
  prompt: string
  choices: string[]
}

export interface QuizPublic {
  id: string
  slug: string
  title: string
  description: string
  questions: QuizQuestionPublic[]
  created_at: string
}

export interface QuizBreakdown {
  question_id: string
  user_answer: number
  correct_index: number
  is_correct: boolean
  explanation: string
}

export interface QuizResult {
  quiz_slug: string
  score: number
  total: number
  correct: number
  breakdown: QuizBreakdown[]
  attempt_id?: string | null
}

export interface ScamReport {
  id: string
  user_id: string
  job_id: string | null
  title: string
  description: string
  company: string | null
  url: string | null
  status: 'open' | 'reviewed' | 'dismissed' | 'confirmed'
  admin_notes: string | null
  created_at: string
  updated_at: string
}

export interface CompanyVerification {
  name: string
  domain: string | null
  legitimacy_score: number
  signals: Record<string, number>
  whois: Record<string, unknown> | null
  search_results: { title: string; snippet: string; url: string; display_link: string }[]
  provider: string
  from_cache?: boolean
}

export interface AdminDashboard {
  summary: {
    total_jobs: number
    total_fraud: number
    total_legit: number
    fraud_rate: number
    users: number
    reports_open: number
    avg_fraud_score: number
  }
  fraud_over_time: {
    fraud: { bucket: string; count: number }[]
    legit: { bucket: string; count: number }[]
  }
  top_features: { feature: string; count: number }[]
}
