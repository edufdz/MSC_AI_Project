import { useState } from 'react'
import type { FailureCluster, FixProposal } from '../../api/types'
import MinimalReproViewer from './MinimalReproViewer'

interface PriorityClusterListProps {
  clusters: FailureCluster[]
  fixProposals: FixProposal[]
  priorityRanking: string[]
}

const SEVERITY_COLORS: Record<string, string> = {
  critical: 'bg-pearl text-bg',
  high: 'bg-smoke text-bg',
  medium: 'bg-text-muted text-bg',
  low: 'bg-graphite text-smoke',
}

export default function PriorityClusterList({ clusters, fixProposals, priorityRanking }: PriorityClusterListProps) {
  const sorted = priorityRanking
    .map((id) => clusters.find((c) => c.cluster_id === id))
    .filter(Boolean) as FailureCluster[]

  // Include any clusters not in ranking
  const rankedIds = new Set(priorityRanking)
  const unranked = clusters.filter((c) => !rankedIds.has(c.cluster_id))
  const allClusters = [...sorted, ...unranked]

  if (allClusters.length === 0) return null

  return (
    <div className="space-y-3">
      <div className="text-[11px] font-semibold uppercase tracking-widest text-text-muted">
        Priority Clusters ({allClusters.length})
      </div>
      {allClusters.map((cluster, i) => (
        <ClusterCard
          key={cluster.cluster_id}
          cluster={cluster}
          rank={i + 1}
          fixes={fixProposals.filter((f) => f.cluster_id === cluster.cluster_id)}
        />
      ))}
    </div>
  )
}

function ClusterCard({
  cluster,
  rank,
  fixes,
}: {
  cluster: FailureCluster
  rank: number
  fixes: FixProposal[]
}) {
  const [expanded, setExpanded] = useState(false)
  const [activeTab, setActiveTab] = useState<'reproduction' | 'failures' | 'fixes'>('reproduction')
  const severityClass = SEVERITY_COLORS[cluster.severity] || SEVERITY_COLORS.medium

  return (
    <div className="bg-bg-card border border-border rounded-lg overflow-hidden">
      {/* Collapsed header */}
      <button
        onClick={() => setExpanded(!expanded)}
        className="w-full flex items-center gap-3 px-4 py-3 text-left hover:bg-graphite/20 transition-colors duration-150"
      >
        <span className="text-sm font-mono tabular-nums text-text-muted w-6">#{rank}</span>
        <span className={`text-[10px] font-semibold uppercase px-2 py-0.5 rounded ${severityClass}`}>
          {cluster.severity}
        </span>
        <span className="text-sm text-pearl font-medium flex-1 truncate">
          {cluster.root_cause_type.replace(/_/g, ' ')}
        </span>
        <span className="text-xs font-mono tabular-nums text-smoke">
          {cluster.failure_count} failures
        </span>
        <svg
          className={`w-4 h-4 text-text-muted transition-transform duration-200 ${expanded ? 'rotate-180' : ''}`}
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
        >
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
        </svg>
      </button>

      {/* Expanded content */}
      {expanded && (
        <div className="px-4 pb-4 space-y-3 border-t border-border">
          {/* Description & pattern */}
          <div className="pt-3 space-y-2">
            <p className="text-sm text-smoke">{cluster.root_cause_description}</p>
            {cluster.common_pattern && (
              <div className="text-xs text-text-muted">
                <span className="font-semibold">Pattern:</span> {cluster.common_pattern}
              </div>
            )}
          </div>

          {/* Key indicators */}
          {cluster.key_indicators.length > 0 && (
            <div className="flex flex-wrap gap-1.5">
              {cluster.key_indicators.map((ind, i) => (
                <span key={i} className="text-[11px] px-2 py-0.5 rounded bg-graphite text-smoke font-mono">
                  {ind}
                </span>
              ))}
            </div>
          )}

          {/* Affected scenarios & tools */}
          <div className="flex flex-wrap gap-3 text-[11px] text-text-muted">
            {cluster.affected_scenarios.length > 0 && (
              <span>{cluster.affected_scenarios.length} scenarios affected</span>
            )}
            {cluster.affected_tools.length > 0 && (
              <span>{cluster.affected_tools.length} tools affected</span>
            )}
          </div>

          {/* Tabs */}
          <div className="flex gap-4 border-b border-border">
            {(['reproduction', 'failures', 'fixes'] as const).map((tab) => (
              <button
                key={tab}
                onClick={() => setActiveTab(tab)}
                className={`pb-2 text-xs font-medium capitalize transition-colors duration-150 border-b-2 ${
                  activeTab === tab
                    ? 'border-platinum text-pearl'
                    : 'border-transparent text-text-muted hover:text-smoke'
                }`}
              >
                {tab === 'fixes' ? `Fixes (${fixes.length})` : tab === 'failures' ? `Failures (${cluster.failure_examples.length})` : 'Reproduction'}
              </button>
            ))}
          </div>

          {/* Tab content */}
          <div className="pt-1">
            {activeTab === 'reproduction' && (
              cluster.minimal_reproduction ? (
                <MinimalReproViewer reproduction={cluster.minimal_reproduction} />
              ) : (
                <div className="text-sm text-text-muted py-4 text-center">
                  No minimal reproduction available
                </div>
              )
            )}

            {activeTab === 'failures' && (
              <div className="space-y-2 max-h-64 overflow-y-auto">
                {cluster.failure_examples.map((ex) => (
                  <div key={ex.test_id} className="bg-bg-surface border border-border rounded-lg p-2.5">
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-mono text-smoke">{ex.test_id}</span>
                      <span className="text-[10px] text-text-muted">{ex.difficulty}</span>
                    </div>
                    <div className="text-xs text-text-muted mt-1 truncate">{ex.scenario}</div>
                    <div className="text-xs text-smoke mt-1">{ex.failure_reason}</div>
                  </div>
                ))}
              </div>
            )}

            {activeTab === 'fixes' && (
              fixes.length > 0 ? (
                <div className="space-y-2">
                  {fixes.map((fix) => (
                    <FixPreview key={fix.fix_id} fix={fix} />
                  ))}
                </div>
              ) : (
                <div className="text-sm text-text-muted py-4 text-center">
                  No fix proposals for this cluster
                </div>
              )
            )}
          </div>
        </div>
      )}
    </div>
  )
}

function FixPreview({ fix }: { fix: FixProposal }) {
  const effortColors: Record<string, string> = {
    low: 'bg-pearl/10 text-pearl',
    medium: 'bg-smoke/10 text-smoke',
    high: 'bg-text-muted/10 text-text-muted',
  }
  const riskColors: Record<string, string> = {
    low: 'text-pearl',
    medium: 'text-smoke',
    high: 'text-text-muted',
  }

  return (
    <div className="bg-bg-surface border border-border rounded-lg p-3 space-y-2">
      <div className="flex items-center gap-2 flex-wrap">
        <span className="text-[10px] font-mono uppercase px-1.5 py-0.5 rounded bg-graphite text-smoke">
          {fix.fix_type.replace(/_/g, ' ')}
        </span>
        <span className="text-xs font-mono tabular-nums text-pearl">
          {(fix.estimated_fix_rate * 100).toFixed(0)}% fix rate
        </span>
        <span className={`text-[10px] px-1.5 py-0.5 rounded ${effortColors[fix.estimated_effort] || ''}`}>
          {fix.estimated_effort} effort
        </span>
        <span className={`text-[10px] ${riskColors[fix.risk_level] || ''}`}>
          {fix.risk_level} risk
        </span>
      </div>
      <p className="text-sm text-smoke">{fix.description}</p>
    </div>
  )
}
