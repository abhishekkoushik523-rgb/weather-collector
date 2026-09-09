import { Check, X, Clock } from 'lucide-react'
import { updateReportStatus } from '../api/client'

const STATUS_STYLE = {
  verified: 'bg-verified/15 text-verified',
  pending: 'bg-warn/15 text-warn',
  rejected: 'bg-alert/15 text-alert',
}

export default function AdminTable({ reports, onUpdate }) {
  const handleAction = async (id, status) => {
    await updateReportStatus(id, status)
    onUpdate()
  }

  return (
    <div className="bg-panel-raised border border-storm rounded-xl overflow-hidden shadow-glow">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-storm text-left text-text-muted text-xs uppercase tracking-wide">
            <th className="px-4 py-3">Report</th>
            <th className="px-4 py-3">Event</th>
            <th className="px-4 py-3">Location</th>
            <th className="px-4 py-3">Credibility</th>
            <th className="px-4 py-3">Status</th>
            <th className="px-4 py-3 text-right">Actions</th>
          </tr>
        </thead>
        <tbody>
          {reports.slice(0, 50).map((r) => (
            <tr key={r.id} className="border-b border-storm/50 hover:bg-panel">
              <td className="px-4 py-3">
                <p className="text-text-primary text-xs max-w-xs truncate">{r.text}</p>
                <p className="text-[10px] text-text-muted font-mono">{r.id} · {r.source}</p>
              </td>
              <td className="px-4 py-3 text-xs capitalize text-text-muted">
                {r.event_type.replace('_', ' ')}
              </td>
              <td className="px-4 py-3 text-xs text-text-muted">{r.city}, {r.state}</td>
              <td className="px-4 py-3">
                <div className="w-16 h-1.5 bg-storm/40 rounded-full overflow-hidden">
                  <div
                    className="h-full bg-rain"
                    style={{ width: `${r.credibility_score}%` }}
                  />
                </div>
                <span className="text-[10px] text-text-muted font-mono">{r.credibility_score}%</span>
              </td>
              <td className="px-4 py-3">
                <div className="flex items-center gap-1.5">
                  <span className={`text-[10px] font-mono px-2 py-0.5 rounded ${STATUS_STYLE[r.verification_status]}`}>
                    {r.verification_status}
                  </span>
                  <span
                    className={`text-[9px] font-mono uppercase px-1.5 py-0.5 rounded border ${
                      r.verified_by === 'admin'
                        ? 'border-thunder/40 text-thunder'
                        : 'border-storm text-text-muted'
                    }`}
                    title={r.verified_by === 'admin' ? 'Manually overridden by an admin' : "Assessed by the ML model — hasn't been reviewed by a person"}
                  >
                    {r.verified_by === 'admin' ? 'Admin' : 'ML'}
                  </span>
                </div>
              </td>
              <td className="px-4 py-3">
                <div className="flex items-center justify-end gap-1.5">
                  <button
                    onClick={() => handleAction(r.id, 'verified')}
                    className="p-1.5 rounded-md bg-verified/10 text-verified hover:bg-verified/20"
                    title="Verify"
                  >
                    <Check size={14} />
                  </button>
                  <button
                    onClick={() => handleAction(r.id, 'pending')}
                    className="p-1.5 rounded-md bg-warn/10 text-warn hover:bg-warn/20"
                    title="Mark pending"
                  >
                    <Clock size={14} />
                  </button>
                  <button
                    onClick={() => handleAction(r.id, 'rejected')}
                    className="p-1.5 rounded-md bg-alert/10 text-alert hover:bg-alert/20"
                    title="Reject"
                  >
                    <X size={14} />
                  </button>
                </div>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
