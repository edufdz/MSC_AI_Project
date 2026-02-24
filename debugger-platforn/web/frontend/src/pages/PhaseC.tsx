import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useStore } from '../store'
import { usePhaseRunner } from '../hooks/usePhaseRunner'
import { getPhaseCStatus } from '../api/client'
import ExecutionControls from '../components/phase-c/ExecutionControls'
import PersonaContextInput from '../components/phase-c/PersonaContextInput'
import LiveMonitor from '../components/phase-c/LiveMonitor'
import type { PhaseCResult } from '../api/types'

export default function PhaseC() {
  const navigate = useNavigate()
  const sessionId = useStore((s) => s.sessionId)
  const phaseStatus = useStore((s) => s.phaseC)
  const progress = useStore((s) => s.phaseCProgress)
  const phaseResult = useStore((s) => s.phaseCResult)
  const setPhaseCResult = useStore((s) => s.setPhaseCResult)
  const setPhaseStatus = useStore((s) => s.setPhaseStatus)
  const phaseBCompleted = useStore((s) => s.phaseB) === 'completed'
  const completedTests = useStore((s) => s.completedTests)
  const { runPhaseC } = usePhaseRunner()

  // Form state
  const [mock, setMock] = useState(true)
  const [workers, setWorkers] = useState(10)
  const [count, setCount] = useState(0)
  const [aiPersonas, setAiPersonas] = useState(false)
  const [traces, setTraces] = useState(true)
  const [failRate, setFailRate] = useState(0.05)
  const [seed, setSeed] = useState<number | null>(null)
  const [language, setLanguage] = useState('')
  const [personaContext, setPersonaContext] = useState('')
  const [error, setError] = useState('')

  useEffect(() => {
    if (sessionId && !phaseResult && phaseStatus !== 'running') {
      getPhaseCStatus(sessionId).then((s) => {
        if (s.status === 'completed' && s.result) {
          setPhaseStatus('c', 'completed')
          setPhaseCResult(s.result as unknown as PhaseCResult)
        }
      }).catch(() => {})
    }
  }, [sessionId, phaseResult, phaseStatus, setPhaseStatus, setPhaseCResult])

  const handleRun = async () => {
    setError('')
    if (!sessionId) {
      setError('No active session')
      return
    }
    try {
      await runPhaseC({
        session_id: sessionId,
        mock,
        workers,
        count,
        ai_personas: aiPersonas,
        traces,
        fail_rate: failRate,
        seed,
        language: language || null,
        persona_context: personaContext || null,
      })
    } catch (e) {
      setError(String(e))
    }
  }

  if (!sessionId) {
    return (
      <div className="flex flex-col items-center justify-center h-64 space-y-4">
        <p className="text-smoke">No active session</p>
        <button onClick={() => navigate('/')} className="px-4 py-2 bg-platinum text-bg rounded-lg text-sm font-medium">
          Go to Dashboard
        </button>
      </div>
    )
  }

  const status: string = phaseStatus
  if (!phaseBCompleted && status === 'idle') {
    return (
      <div className="flex flex-col items-center justify-center h-64 space-y-4">
        <p className="text-smoke">Phase B must be completed first</p>
        <button onClick={() => navigate('/phase-b')} className="px-4 py-2 bg-platinum text-bg rounded-lg text-sm font-medium">
          Go to Phase B
        </button>
      </div>
    )
  }

  // Show live monitor when running or completed with events
  const showMonitor = status === 'running' || (status === 'completed' && completedTests > 0)

  if (showMonitor) {
    return (
      <div className="h-full">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h1 className="text-xl font-semibold tracking-tight text-pearl">Phase C: Live Monitor</h1>
            <p className="text-sm text-smoke mt-0.5">
              {status === 'running' ? 'Test execution in progress...' : 'Execution completed'}
            </p>
          </div>
          {status === 'completed' && phaseResult && (
            <div className="flex items-center gap-4">
              <div className="text-right">
                <div className={`text-2xl font-bold font-mono ${phaseResult.pass_rate >= 80 ? 'text-pearl' : 'text-smoke'}`}>
                  {phaseResult.pass_rate.toFixed(1)}%
                </div>
                <div className="text-[11px] text-text-muted uppercase tracking-wider">Final Pass Rate</div>
              </div>
            </div>
          )}
        </div>
        <LiveMonitor />
      </div>
    )
  }

  // Pre-run configuration
  return (
    <div className="space-y-6 max-w-3xl">
      <div>
        <h1 className="text-xl font-semibold tracking-tight text-pearl">Phase C: Execute Tests</h1>
        <p className="text-sm text-smoke mt-0.5">Run the test suite against the agent with live monitoring</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="space-y-6">
          <ExecutionControls
            mock={mock} onMockChange={setMock}
            workers={workers} onWorkersChange={setWorkers}
            count={count} onCountChange={setCount}
            aiPersonas={aiPersonas} onAiPersonasChange={setAiPersonas}
            traces={traces} onTracesChange={setTraces}
            failRate={failRate} onFailRateChange={setFailRate}
            seed={seed} onSeedChange={setSeed}
            language={language} onLanguageChange={setLanguage}
          />
        </div>

        <div className="space-y-6">
          <PersonaContextInput value={personaContext} onChange={setPersonaContext} />
        </div>
      </div>

      {error && (
        <div className="px-3 py-2 bg-graphite border border-border-light rounded-lg text-sm text-smoke">
          {error}
        </div>
      )}

      <button
        onClick={handleRun}
        disabled={status === 'running'}
        className="w-full px-4 py-3 bg-platinum text-bg rounded-lg font-medium hover:bg-pearl transition-colors duration-200 disabled:opacity-50"
      >
        {status === 'running' ? 'Executing...' : 'Run Phase C'}
      </button>

      {status === 'running' && (
        <div className="space-y-2">
          <div className="h-1 bg-border rounded-full overflow-hidden">
            <div className="h-full bg-platinum rounded-full transition-all duration-500" style={{ width: `${progress.pct}%` }} />
          </div>
          <div className="text-xs text-smoke">{progress.message || 'Starting execution...'}</div>
        </div>
      )}
    </div>
  )
}
