import { motion } from 'framer-motion'
import clsx from 'clsx'
import { pct } from '../lib/format'

interface Props { score: number; label: 'fraud' | 'legit' }

export function ScoreMeter({ score, label }: Props) {
  const danger = label === 'fraud'
  const pctNum = Math.round(score * 100)
  return (
    <div className="space-y-2">
      <div className="flex items-baseline justify-between">
        <span className={clsx('text-2xl font-bold', danger ? 'text-red-700' : 'text-emerald-700')}>
          {danger ? 'FRAUD' : 'LIKELY LEGIT'}
        </span>
        <span className="text-sm text-slate-600">{pct(score, 2)} fraud probability</span>
      </div>
      <div className="h-2 w-full bg-slate-100 rounded-full overflow-hidden">
        <motion.div
          initial={{ width: 0 }}
          animate={{ width: `${pctNum}%` }}
          transition={{ duration: 0.5, ease: 'easeOut' }}
          className={clsx('h-full', danger ? 'bg-red-500' : 'bg-emerald-500')}
        />
      </div>
    </div>
  )
}
