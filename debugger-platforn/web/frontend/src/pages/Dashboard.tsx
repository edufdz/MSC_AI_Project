import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { createSession, listSessions } from '../api/client'
import { useStore } from '../store'
import ProgressStepper from '../components/shared/ProgressStepper'

export default function Dashboard() {
  const navigate = useNavigate()
  const setSessionId = useStore((s) => s.setSessionId)
  const sessionId = useStore((s) => s.sessionId)
  const [sessions, setSessions] = useState<Array<{ session_id: string; created_at: string; phases_completed: string[] }>>([])
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    listSessions().then((res) => setSessions(res.sessions)).catch(() => {})
  }, [])

  const handleNewSession = async () => {
    setLoading(true)
    try {
      const session = await createSession()
      setSessionId(session.session_id)
      navigate('/phase-a')
    } catch (err) {
      console.error('Failed to create session:', err)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="max-w-4xl mx-auto space-y-8">
      {/* Hero card */}
      <div className="bg-bg-card border border-border rounded-xl p-10 text-center">
        <h1 className="text-2xl font-semibold tracking-tight text-pearl mb-3">
          Agent Debugger Platform
        </h1>
        <p className="text-smoke mb-8 max-w-lg mx-auto text-sm leading-relaxed">
          Analyze agent codebases, generate comprehensive test suites, and execute
          them with live monitoring. Step-by-step wizard through Phases A, B, and C.
        </p>

        {sessionId ? (
          <div className="space-y-5">
            <ProgressStepper />
            <button
              onClick={() => navigate('/phase-a')}
              className="px-6 py-3 bg-platinum text-bg rounded-lg font-medium hover:bg-pearl transition-colors duration-200"
            >
              Continue Session
            </button>
          </div>
        ) : (
          <button
            onClick={handleNewSession}
            disabled={loading}
            className="px-8 py-3 bg-platinum text-bg rounded-lg font-medium hover:bg-pearl transition-colors duration-200 disabled:opacity-50"
          >
            {loading ? 'Creating...' : 'Start New Debugging Session'}
          </button>
        )}
      </div>

      {/* Previous sessions */}
      {sessions.length > 0 && (
        <div className="space-y-3">
          <h2 className="text-[11px] font-semibold text-text-muted uppercase tracking-widest">
            Previous Sessions
          </h2>
          <div className="grid gap-2">
            {sessions.map((s) => (
              <button
                key={s.session_id}
                onClick={() => {
                  setSessionId(s.session_id)
                  if (s.phases_completed.includes('c')) navigate('/phase-c')
                  else if (s.phases_completed.includes('b')) navigate('/phase-c')
                  else if (s.phases_completed.includes('a')) navigate('/phase-b')
                  else navigate('/phase-a')
                }}
                className="flex items-center justify-between px-4 py-3 bg-bg-card border border-border rounded-lg hover:border-border-light transition-all duration-200 text-left group"
              >
                <div>
                  <div className="text-sm font-mono text-pearl group-hover:text-pearl">{s.session_id}</div>
                  <div className="text-xs text-text-muted">
                    {new Date(s.created_at).toLocaleString()}
                  </div>
                </div>
                <div className="flex gap-1.5">
                  {['a', 'b', 'c'].map((phase) => (
                    <span
                      key={phase}
                      className={`w-6 h-6 rounded-full flex items-center justify-center text-[10px] font-bold transition-colors ${
                        s.phases_completed.includes(phase)
                          ? 'bg-pearl text-bg'
                          : 'bg-graphite text-text-muted'
                      }`}
                    >
                      {phase.toUpperCase()}
                    </span>
                  ))}
                </div>
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
