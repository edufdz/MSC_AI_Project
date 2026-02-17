// TypeScript types mirroring backend Pydantic models

export interface Session {
  session_id: string
  output_dir: string
  created_at: string
  phases_completed: string[]
}

export interface PhaseStatus {
  session_id: string
  phase: string
  status: 'idle' | 'running' | 'completed' | 'error'
  progress_pct: number
  message: string
  result: Record<string, unknown> | null
  error: string | null
}

// Phase A
export interface PhaseARequest {
  session_id: string
  repo_path: string
  skip_ai: boolean
  language: string | null
  prompt_encoding: string
}

export interface PhaseAResult {
  framework: string
  framework_confidence: number
  tools_count: number
  prompts_count: number
  risks_count: number
  files_scanned: number
  language: string
  agent_map_path: string
  graph_path: string | null
  tools: Array<{ name: string; description: string; risk_level: string }>
  risks: Array<{ tool: string; risk_type: string; severity: string; description: string }>
}

// Phase B
export interface PhaseBRequest {
  session_id: string
  skip_ai: boolean
  count: number
  persona_count: number
  scenario_count: number
  variants: number
  seed: number | null
  language: string | null
  use_tlahuac: boolean
  tlahuac_dir: string | null
}

export interface PhaseBResult {
  test_suite_path: string
  total_tests: number
  persona_count: number
  scenario_count: number
  personas: Array<{ name: string; agent_type: string; source: string }>
  scenarios: Array<{ title: string; difficulty: string; required_tools: string[] }>
  tokens_used?: number
  cost_usd?: number
}

// Phase C
export interface PhaseCRequest {
  session_id: string
  mock: boolean
  workers: number
  count: number
  ai_personas: boolean
  traces: boolean
  fail_rate: number
  seed: number | null
  language: string | null
  persona_context: string | null
}

export interface PhaseCResult {
  total_tests: number
  passed: number
  failed: number
  errors: number
  timeouts: number
  pass_rate: number
  total_duration_sec: number
  total_cost_usd: number
  tool_coverage_pct: number
  tools_not_covered: string[]
  by_difficulty: Record<string, Record<string, number>>
}

// Filesystem browser
export interface FileEntry {
  name: string
  type: 'file' | 'directory'
  path: string
  size: number | null
}

export interface FileBrowseResponse {
  current_path: string
  parent_path: string | null
  entries: FileEntry[]
}

// WebSocket events
export interface WSEvent {
  type: string
  phase?: string
  session_id?: string
  step?: string
  message?: string
  progress_pct?: number
  timestamp?: number
  // Phase C execution events
  test_id?: string
  test_number?: number
  scenario?: string
  persona?: string
  difficulty?: string
  status?: string
  failure_reason?: string
  turn?: number
  role?: string
  tool_name?: string
  tools_called?: string[]
  pass_rate?: number
  cost_usd?: number
  duration_sec?: number
  _totals?: {
    passed: number
    failed: number
    errors: number
    timeouts: number
    completed: number
    total_tests: number
    total_cost_usd: number
    pass_rate: number
    tools_covered: number
    tools_total: number
  }
  result?: Record<string, unknown>
  error?: string
}
