import { useState } from 'react'
import { useStore } from '../../store'
import ConversationView from './ConversationView'
import StatusBadge from '../shared/StatusBadge'

export default function SimulationCards() {
  const activeTests = useStore((s) => s.activeTests)
  const [selectedTestId, setSelectedTestId] = useState<string | null>(null)
  const [tab, setTab] = useState<'active' | 'conversations'>('active')

  const tests = Array.from(activeTests.values())
  const runningTests = tests.filter((t) => t.status === 'running')
  const completedTestsList = tests.filter((t) => t.status !== 'running')

  if (selectedTestId) {
    const test = activeTests.get(selectedTestId)
    if (test) {
      return (
        <div>
          <button
            onClick={() => setSelectedTestId(null)}
            className="text-sm text-smoke hover:text-pearl transition-colors mb-3"
          >
            &larr; Back to simulations
          </button>
          <ConversationView test={test} />
        </div>
      )
    }
  }

  return (
    <div className="space-y-4">
      {/* Tabs */}
      <div className="flex gap-1 border-b border-border">
        <button
          onClick={() => setTab('active')}
          className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors ${
            tab === 'active' ? 'border-platinum text-pearl' : 'border-transparent text-text-muted hover:text-smoke'
          }`}
        >
          Active Simulations ({runningTests.length})
        </button>
        <button
          onClick={() => setTab('conversations')}
          className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors ${
            tab === 'conversations' ? 'border-platinum text-pearl' : 'border-transparent text-text-muted hover:text-smoke'
          }`}
        >
          Conversations ({completedTestsList.length})
        </button>
      </div>

      {/* Active simulations */}
      {tab === 'active' && (
        <div className="grid grid-cols-2 gap-3">
          {runningTests.length === 0 && (
            <div className="col-span-2 text-center py-8 text-text-muted text-sm">
              No active simulations
            </div>
          )}
          {runningTests.map((test) => (
            <div
              key={test.test_id}
              onClick={() => setSelectedTestId(test.test_id)}
              className="bg-bg-card border border-border-light rounded-lg p-3 cursor-pointer hover:border-platinum/30 transition-all duration-200"
            >
              <div className="flex items-center justify-between mb-2">
                <span className="text-xs font-mono text-smoke">{test.test_id}</span>
                <StatusBadge status="running" />
              </div>
              <div className="text-sm text-pearl truncate">{test.scenario}</div>
              <div className="text-xs text-text-muted mt-1">{test.persona}</div>
              {/* Last messages */}
              <div className="mt-2 space-y-1">
                {test.turns.slice(-2).map((turn, i) => (
                  <div key={i} className={`text-[11px] px-2 py-1 rounded ${
                    turn.role === 'user' ? 'bg-graphite/80 text-smoke' : 'bg-bg-surface text-text-muted'
                  }`}>
                    <span className="font-bold">{turn.role}: </span>
                    <span className="truncate">{turn.message.slice(0, 60)}</span>
                  </div>
                ))}
              </div>
              {/* Tool call pills */}
              {test.tool_calls.length > 0 && (
                <div className="flex flex-wrap gap-1 mt-2">
                  {test.tool_calls.slice(-3).map((tc, i) => (
                    <span
                      key={i}
                      className={`text-[10px] px-1.5 py-0.5 rounded font-mono ${
                        tc.status === 'success' ? 'bg-pearl/10 text-smoke' : 'bg-text-muted/10 text-text-muted'
                      }`}
                    >
                      {tc.tool_name}
                    </span>
                  ))}
                </div>
              )}
            </div>
          ))}
        </div>
      )}

      {/* Conversations list */}
      {tab === 'conversations' && (
        <div className="space-y-1">
          {completedTestsList.length === 0 && (
            <div className="text-center py-8 text-text-muted text-sm">
              No completed conversations yet
            </div>
          )}
          {completedTestsList.map((test) => (
            <button
              key={test.test_id}
              onClick={() => setSelectedTestId(test.test_id)}
              className="w-full flex items-center gap-3 px-3 py-2 bg-bg-card border border-border rounded-lg hover:border-border-light transition-all duration-200"
            >
              <span className="text-xs font-mono text-text-muted w-16">{test.test_id}</span>
              <span className="text-sm text-pearl flex-1 truncate text-left">{test.scenario}</span>
              <span className="text-xs text-text-muted">{test.turns.length} turns</span>
              <StatusBadge status={test.status} />
            </button>
          ))}
        </div>
      )}
    </div>
  )
}
