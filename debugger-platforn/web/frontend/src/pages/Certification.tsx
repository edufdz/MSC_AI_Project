import { useState, useEffect } from 'react'
import { useStore } from '../store'
import { usePhaseRunner } from '../hooks/usePhaseRunner'
import { getCertificationStatus, resetPhase as apiResetPhase } from '../api/client'
import PhaseProgress from '../components/shared/PhaseProgress'
import type { CertificationReport, CertificationCategoryScore } from '../api/types'

const CERT_STEPS = [
  { key: 'loading_data', label: 'Loading data...', pctThreshold: 5 },
  { key: 'scoring', label: 'Scoring categories...', pctThreshold: 50 },
  { key: 'saving', label: 'Saving certification report...', pctThreshold: 90 },
  { key: 'complete', label: 'Certification complete', pctThreshold: 95 },
]

const TIER_STYLES: Record<string, { bg: string; text: string; label: string }> = {
  platinum: { bg: 'bg-blue-600', text: 'text-white', label: 'PLATINUM' },
  gold: { bg: 'bg-yellow-500', text: 'text-black', label: 'GOLD' },
  silver: { bg: 'bg-gray-300', text: 'text-black', label: 'SILVER' },
  not_certified: { bg: 'bg-red-600', text: 'text-white', label: 'NOT CERTIFIED' },
}

function ScoreBar({ score, label }: { score: number; label: string }) {
  const pct = Math.max(0, Math.min(100, score))
  const color = pct >= 85 ? 'bg-green-500' : pct >= 70 ? 'bg-yellow-500' : pct >= 50 ? 'bg-orange-500' : 'bg-red-500'
  return (
    <div className="flex items-center gap-3">
      <span className="text-sm text-text-dim w-44 shrink-0">{label}</span>
      <div className="flex-1 h-3 bg-bg-card rounded-full overflow-hidden">
        <div className={`h-full ${color} rounded-full transition-all duration-500`} style={{ width: `${pct}%` }} />
      </div>
      <span className="text-sm font-mono text-pearl w-16 text-right">{score.toFixed(1)}</span>
    </div>
  )
}

function CategoryDetail({ cs }: { cs: CertificationCategoryScore }) {
  const [open, setOpen] = useState(false)
  return (
    <div className="border border-border rounded-lg p-3">
      <button onClick={() => setOpen(!open)} className="w-full text-left">
        <ScoreBar score={cs.score} label={`${cs.category} (${(cs.weight * 100).toFixed(0)}%)`} />
      </button>
      {open && (
        <div className="mt-3 pl-4 space-y-1 text-sm text-text-dim">
          {Object.entries(cs.breakdown).map(([k, v]) => (
            <div key={k} className="flex justify-between">
              <span>{k.replace(/_/g, ' ')}</span>
              <span className="font-mono">{typeof v === 'number' ? v.toFixed(2) : v}</span>
            </div>
          ))}
          {cs.notes.map((n, i) => (
            <div key={i} className="text-text-muted italic">- {n}</div>
          ))}
        </div>
      )}
    </div>
  )
}

export default function Certification() {
  const sessionId = useStore((s) => s.sessionId)
  const phaseStatus = useStore((s) => s.certStatus)
  const progress = useStore((s) => s.certProgress)
  const certResult = useStore((s) => s.certResult)
  const setCertResult = useStore((s) => s.setCertResult)
  const setPhaseStatus = useStore((s) => s.setPhaseStatus)
  const phaseDCompleted = useStore((s) => s.phaseD) === 'completed'
  const phaseCCompleted = useStore((s) => s.phaseC) === 'completed'
  const storeResetPhase = useStore((s) => s.resetPhase)
  const { runCertification } = usePhaseRunner()

  const [error, setError] = useState('')

  // Hydrate from server on mount
  useEffect(() => {
    if (sessionId && !certResult && phaseStatus !== 'running') {
      getCertificationStatus(sessionId).then((s) => {
        if (s.status === 'completed' && s.result) {
          setPhaseStatus('cert', 'completed')
          setCertResult(s.result as unknown as CertificationReport)
        }
      }).catch(() => {})
    }
  }, [sessionId, certResult, phaseStatus, setPhaseStatus, setCertResult])

  const handleRerun = async () => {
    if (!sessionId) return
    try {
      await apiResetPhase(sessionId, 'cert')
      storeResetPhase('cert')
    } catch (e) {
      setError(String(e))
    }
  }

  const handleRun = async () => {
    setError('')
    if (!sessionId) { setError('No active session'); return }
    try {
      await runCertification({ session_id: sessionId })
    } catch (e) {
      setError(String(e))
    }
  }

  const canRun = phaseDCompleted || phaseCCompleted

  // Running state
  if (phaseStatus === 'running') {
    return (
      <div className="p-6 max-w-3xl mx-auto space-y-6">
        <h2 className="text-2xl font-semibold text-pearl">Certification</h2>
        <PhaseProgress steps={CERT_STEPS} currentPct={progress.pct} currentMessage={progress.message} />
      </div>
    )
  }

  // Completed state
  if (phaseStatus === 'completed' && certResult) {
    const tier = TIER_STYLES[certResult.tier] || TIER_STYLES.not_certified
    return (
      <div className="p-6 max-w-4xl mx-auto space-y-6">
        <div className="flex items-center justify-between">
          <h2 className="text-2xl font-semibold text-pearl">Certification Report</h2>
          <button onClick={handleRerun} className="px-4 py-2 text-sm border border-border rounded-lg hover:bg-bg-card text-text-dim">
            Re-run
          </button>
        </div>

        {/* Tier + Score */}
        <div className="flex items-center gap-6 p-6 bg-bg-surface border border-border rounded-xl">
          <span className={`px-4 py-2 rounded-lg font-bold text-lg ${tier.bg} ${tier.text}`}>
            {tier.label}
          </span>
          <div>
            <div className="text-4xl font-bold text-pearl">{certResult.overall_score.toFixed(1)}</div>
            <div className="text-sm text-text-muted">Overall Score / 100</div>
          </div>
          <div className="ml-auto text-right text-sm text-text-dim">
            <div>ID: {certResult.certification_id}</div>
            {certResult.issued_at && <div>Issued: {new Date(certResult.issued_at).toLocaleDateString()}</div>}
            {certResult.expires_at && <div>Expires: {new Date(certResult.expires_at).toLocaleDateString()}</div>}
          </div>
        </div>

        {/* Category Scores */}
        <div className="space-y-3">
          <h3 className="text-lg font-medium text-pearl">Category Scores</h3>
          {certResult.category_scores.map((cs) => (
            <CategoryDetail key={cs.category} cs={cs} />
          ))}
        </div>

        {/* Hard Blockers */}
        {certResult.hard_blockers.length > 0 && (
          <div className="space-y-2">
            <h3 className="text-lg font-medium text-red-600">Hard Blockers</h3>
            {certResult.hard_blockers.map((b, i) => (
              <div key={i} className="p-3 bg-red-50 border border-red-200 rounded-lg text-sm">
                <div className="font-medium text-red-700">{b.condition}</div>
                {b.evidence && <div className="text-red-600/70 mt-1">Evidence: {b.evidence}</div>}
                <div className="text-red-500 mt-1">Blocks: {b.tier_blocked.replace('_', ' ')}</div>
              </div>
            ))}
          </div>
        )}

        {/* Strengths & Improvements */}
        <div className="grid grid-cols-2 gap-4">
          {certResult.strengths.length > 0 && (
            <div className="space-y-2">
              <h3 className="text-lg font-medium text-green-600">Strengths</h3>
              {certResult.strengths.map((s, i) => (
                <div key={i} className="text-sm text-text-dim pl-3 border-l-2 border-green-600">{s}</div>
              ))}
            </div>
          )}
          {certResult.improvements.length > 0 && (
            <div className="space-y-2">
              <h3 className="text-lg font-medium text-yellow-600">Improvements</h3>
              {certResult.improvements.map((s, i) => (
                <div key={i} className="text-sm text-text-dim pl-3 border-l-2 border-yellow-600">{s}</div>
              ))}
            </div>
          )}
        </div>

        {/* Confidence */}
        <div className="p-4 bg-bg-surface border border-border rounded-lg text-sm text-text-dim">
          <h3 className="text-base font-medium text-pearl mb-2">Confidence Metrics</h3>
          <div className="grid grid-cols-2 gap-2">
            <div>Simulations: {certResult.confidence.total_simulations}</div>
            <div>Confidence: {certResult.confidence.confidence_level.toFixed(1)}%</div>
            <div>Margin of Error: +/-{certResult.confidence.margin_of_error.toFixed(1)}%</div>
            <div>Sample Sufficient: {certResult.confidence.sample_sufficient ? 'Yes' : 'No'}</div>
          </div>
        </div>
      </div>
    )
  }

  // Idle / pre-run state
  return (
    <div className="p-6 max-w-3xl mx-auto space-y-6">
      <h2 className="text-2xl font-semibold text-pearl">Certification</h2>
      <p className="text-text-dim">
        Score the agent across 5 categories (Safety, Reliability, Tool Competency, Conversation Quality, Efficiency)
        and assign a certification tier.
      </p>

      {!canRun && (
        <div className="p-3 bg-yellow-50 border border-yellow-200 rounded-lg text-sm text-yellow-700">
          Phase C or D must be completed before running certification.
        </div>
      )}

      {error && (
        <div className="p-3 bg-red-50 border border-red-200 rounded-lg text-sm text-red-700">{error}</div>
      )}

      <button
        onClick={handleRun}
        disabled={!canRun}
        className="px-6 py-3 bg-accent text-bg font-medium rounded-lg hover:bg-accent/90 disabled:opacity-40 disabled:cursor-not-allowed transition-all"
      >
        Run Certification
      </button>
    </div>
  )
}
