import clsx from 'clsx'
import type { Explanation } from '../types'

export function ExplanationsTable({ items }: { items: Explanation[] }) {
  if (!items.length) {
    return <p className="text-sm text-slate-500">No SHAP features were returned for this analysis.</p>
  }
  return (
    <div className="overflow-x-auto">
      <table className="min-w-full text-sm">
        <thead>
          <tr className="text-left text-slate-500 border-b border-slate-200">
            <th className="py-2 pr-3 font-medium">Feature</th>
            <th className="py-2 pr-3 font-medium">Value</th>
            <th className="py-2 pr-3 font-medium">Contribution</th>
            <th className="py-2 font-medium">Direction</th>
          </tr>
        </thead>
        <tbody>
          {items.map((e) => {
            const danger = e.direction === 'fraud'
            return (
              <tr key={e.feature} className="border-b border-slate-100 last:border-0">
                <td className="py-2 pr-3 font-medium">{e.label || e.feature}</td>
                <td className="py-2 pr-3 text-slate-700">{e.value.toFixed(3)}</td>
                <td
                  className={clsx(
                    'py-2 pr-3 font-semibold',
                    danger ? 'text-red-700' : 'text-emerald-700',
                  )}
                >
                  {e.contribution >= 0 ? '+' : ''}
                  {e.contribution.toFixed(3)}
                </td>
                <td className="py-2">
                  <span
                    className={clsx(
                      'pill',
                      danger
                        ? 'bg-red-100 text-red-700 ring-1 ring-red-200'
                        : e.direction === 'legit'
                          ? 'bg-emerald-100 text-emerald-700 ring-1 ring-emerald-200'
                          : 'bg-slate-100 text-slate-700 ring-1 ring-slate-200',
                    )}
                  >
                    {e.direction}
                  </span>
                </td>
              </tr>
            )
          })}
        </tbody>
      </table>
    </div>
  )
}
