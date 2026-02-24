// Hook for running phases and polling status

import { useCallback, useRef } from 'react'
import * as api from '../api/client'
import { useStore, type AppState } from '../store'
import type { PhaseARequest, PhaseBRequest, PhaseCRequest } from '../api/types'

export function usePhaseRunner() {
  const setPhaseStatus = useStore((s: AppState) => s.setPhaseStatus)
  const setPhaseProgress = useStore((s: AppState) => s.setPhaseProgress)
  const setPhaseAResult = useStore((s: AppState) => s.setPhaseAResult)
  const setPhaseBResult = useStore((s: AppState) => s.setPhaseBResult)
  const setPhaseCResult = useStore((s: AppState) => s.setPhaseCResult)
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null)

  const stopPolling = useCallback(() => {
    if (pollRef.current) {
      clearInterval(pollRef.current)
      pollRef.current = null
    }
  }, [])

  const pollStatus = useCallback(
    (phase: 'a' | 'b' | 'c', sessionId: string) => {
      stopPolling()
      const getter = phase === 'a' ? api.getPhaseAStatus : phase === 'b' ? api.getPhaseBStatus : api.getPhaseCStatus

      pollRef.current = setInterval(async () => {
        try {
          const status = await getter(sessionId)
          // Update progress from poll (backup for WS)
          if (status.status === 'running' && status.message) {
            setPhaseProgress(phase, '', status.message, status.progress_pct || 0)
          }
          if (status.status === 'completed') {
            stopPolling()
            setPhaseStatus(phase, 'completed')
            if (phase === 'a' && status.result) setPhaseAResult(status.result as never)
            if (phase === 'b' && status.result) setPhaseBResult(status.result as never)
            if (phase === 'c' && status.result) setPhaseCResult(status.result as never)
          } else if (status.status === 'error') {
            stopPolling()
            setPhaseStatus(phase, 'error')
          }
        } catch {
          // ignore polling errors
        }
      }, 1000)
    },
    [stopPolling, setPhaseStatus, setPhaseProgress, setPhaseAResult, setPhaseBResult, setPhaseCResult],
  )

  const runPhaseA = useCallback(
    async (params: PhaseARequest) => {
      setPhaseStatus('a', 'running')
      await api.runPhaseA(params)
      pollStatus('a', params.session_id)
    },
    [setPhaseStatus, pollStatus],
  )

  const runPhaseB = useCallback(
    async (params: PhaseBRequest) => {
      setPhaseStatus('b', 'running')
      await api.runPhaseB(params)
      pollStatus('b', params.session_id)
    },
    [setPhaseStatus, pollStatus],
  )

  const runPhaseC = useCallback(
    async (params: PhaseCRequest) => {
      setPhaseStatus('c', 'running')
      await api.runPhaseC(params)
      pollStatus('c', params.session_id)
    },
    [setPhaseStatus, pollStatus],
  )

  return { runPhaseA, runPhaseB, runPhaseC, stopPolling }
}
