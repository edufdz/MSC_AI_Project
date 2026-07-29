# Agent-Testing Platform - Full Project Breakdown

## What Is This?

The **Agent-Testing Platform** is an AI-powered platform for testing, debugging, and certifying conversational AI agents. It ingests an agent's codebase, generates comprehensive test suites, executes them (against a mock or real agent), diagnoses failures, and certifies the agent's quality. The entire workflow is orchestrated through a **5-phase pipeline** (A through E) plus a final **Certification** step, all accessible via a polished web UI with real-time progress streaming.

---

## Tech Stack

| Layer | Technology |
|-------|------------|
| **Backend** | Python 3.10+, FastAPI, Anthropic SDK, scikit-learn, NetworkX, tree-sitter |
| **Frontend** | React 18, TypeScript, Vite, Tailwind CSS, React Router, Zustand |
| **Real-Time** | WebSocket (progress streaming during phase execution) |
| **Data** | JSON artifacts, Pydantic models |
| **ML/Analysis** | TF-IDF clustering, embeddings, statistical validation |
| **Testing** | pytest, asyncio |

---

## Directory Structure & File Paths

```
agent-debugger/
│
├── debugger-platforn/                              # Main platform directory
│   │
│   ├── ─── CLI Entry Points ───────────────────
│   ├── run_pipeline.py                             # Full A→B→C→D→E pipeline orchestrator
│   ├── analyze.py                                  # Phase A CLI entry point
│   ├── generate_tests.py                           # Phase B CLI entry point
│   ├── execute_tests.py                            # Phase C CLI entry point
│   ├── diagnose_failures.py                        # Phase D CLI entry point
│   ├── improve_agent.py                            # Phase E CLI entry point
│   ├── coverage_builder.py                         # Phase B1 (coverage goals) builder
│   ├── persona_builder.py                          # Phase B2 (personas) builder
│   ├── scenario_builder.py                         # Phase B3 (scenarios) builder
│   ├── testsuite_builder.py                        # Phase B4 (test assembly) builder
│   ├── live_viewer.py                              # Live monitoring dashboard (terminal)
│   ├── run_ai_validation.py                        # Offline vs AI comparison utility
│   ├── requirements.txt                            # Python dependencies
│   ├── pyproject.toml                              # Project metadata
│   ├── ARCHITECTURE.md                             # Architecture documentation
│   ├── README.md                                   # Setup & usage guide
│   ├── USAGE.md                                    # Detailed usage instructions
│   │
│   ├── ─── Core Python Library ────────────────
│   ├── src/
│   │   ├── ingestion/
│   │   │   └── ingestor.py                         # Codebase scanning, file filtering, language detection
│   │   │
│   │   ├── analysis/
│   │   │   └── static_analyzer.py                  # Tree-sitter AST parsing (extracts functions, classes, imports)
│   │   │
│   │   ├── patterns/
│   │   │   └── detector.py                         # Framework detection (LangChain, CrewAI, AutoGen, etc.)
│   │   │
│   │   ├── ai_analyzer/
│   │   │   ├── analyzer.py                         # Claude-powered semantic analysis of agent code
│   │   │   └── prompts.py                          # AI prompt templates for analysis
│   │   │
│   │   ├── risk/
│   │   │   └── analyzer.py                         # Risk identification (PII, unsafe ops, critical chains)
│   │   │
│   │   ├── graph/
│   │   │   ├── builder.py                          # Agent map graph generation (NetworkX)
│   │   │   └── visualizer.py                       # Graph visualization output
│   │   │
│   │   ├── personas/                               # Phase B - Persona management
│   │   │   ├── builder.py                          # Persona generation engine
│   │   │   ├── templates.py                        # Built-in persona templates
│   │   │   ├── models.py                           # Persona data models
│   │   │   ├── affinity.py                         # Persona-scenario affinity scoring
│   │   │   ├── metrics.py                          # Persona metrics & evaluation
│   │   │   └── tlahuac_adapter.py                  # Integration with Tlahuac simulator
│   │   │
│   │   ├── scenarios/                              # Phase B - Scenario management
│   │   │   ├── library.py                          # Scenario catalog & retrieval
│   │   │   ├── templates.py                        # Built-in scenario templates
│   │   │   └── models.py                           # Scenario data models
│   │   │
│   │   ├── coverage/                               # Phase B - Coverage goal definitions
│   │   │   └── (coverage analysis modules)
│   │   │
│   │   ├── generator/                              # Phase B - Test suite assembly
│   │   │   ├── test_suite.py                       # Combines personas × scenarios × coverage
│   │   │   └── models.py                           # Test suite data models
│   │   │
│   │   ├── execution/                              # Phase C - Test execution engine
│   │   │   ├── runner.py                           # Main async test executor (parallel workers)
│   │   │   ├── agent_connector.py                  # Agent connectors (Mock, API, Victoria)
│   │   │   ├── conversation_simulator.py           # Claude-powered persona conversation driver
│   │   │   ├── gan_simulator.py                    # GAN-mode adversarial testing (generator + critic)
│   │   │   ├── critic_agent.py                     # Critic agent for GAN quality evaluation
│   │   │   ├── monitor.py                          # Real-time monitoring & event streaming
│   │   │   ├── aggregator.py                       # Results aggregation & statistics
│   │   │   ├── llm_config.py                       # Multi-LLM provider configuration
│   │   │   ├── persona_context.py                  # Persona context analysis & injection
│   │   │   └── models.py                           # Execution data models
│   │   │
│   │   ├── diagnosis/                              # Phase D - Failure diagnosis
│   │   │   ├── engine.py                           # Main diagnosis orchestrator
│   │   │   ├── clustering.py                       # TF-IDF / embedding-based failure clustering
│   │   │   ├── root_cause_analyzer.py              # Root cause identification (hallucination, tool error, etc.)
│   │   │   ├── minimal_reproducer.py               # Minimal reproduction case generator
│   │   │   ├── fix_generator.py                    # AI-powered fix proposal generation
│   │   │   ├── priority_ranker.py                  # Impact-based priority ranking (severity × frequency)
│   │   │   ├── retry.py                            # Anthropic API retry logic with exponential backoff
│   │   │   └── models.py                           # Diagnosis data models
│   │   │
│   │   ├── improvement/                            # Phase E - Improvement & validation
│   │   │   ├── engine.py                           # Main improvement orchestrator
│   │   │   ├── fix_applicator.py                   # Fix application engine (applies code diffs)
│   │   │   ├── ab_testing.py                       # A/B testing framework (baseline vs fixed)
│   │   │   ├── validator.py                        # Statistical validation (p-values, significance)
│   │   │   ├── regression_generator.py             # Regression test generation from fixed failures
│   │   │   ├── deployment_packager.py              # Deployment package builder (changelog, rollback docs)
│   │   │   └── models.py                           # Improvement data models
│   │   │
│   │   ├── certification/                          # Certification scoring logic
│   │   │   └── (certification engine & validators)
│   │   │
│   │   ├── validation/                             # Artifact validation utilities
│   │   ├── monitor_ui/
│   │   │   └── server.py                           # Optional standalone monitoring UI server
│   │   └── endpoints_config.py                     # Endpoint configuration defaults
│   │
│   ├── ─── Web Application ────────────────────
│   ├── web/
│   │   ├── api/                                    # FastAPI Backend
│   │   │   ├── app.py                              # FastAPI app initialization, middleware, startup
│   │   │   ├── config.py                           # CORS settings, phase defaults, environment config
│   │   │   ├── ws.py                               # WebSocket connection manager
│   │   │   │
│   │   │   ├── models/
│   │   │   │   ├── requests.py                     # Pydantic request models for phases A-D
│   │   │   │   └── responses.py                    # Pydantic response models
│   │   │   │
│   │   │   ├── routes/                             # API route handlers
│   │   │   │   ├── sessions.py                     # Session CRUD (create, list, get, save, reset)
│   │   │   │   ├── filesystem.py                   # File browsing & directory resolution
│   │   │   │   ├── phase_a.py                      # POST /api/phase-a/run, GET /status
│   │   │   │   ├── phase_b.py                      # POST /api/phase-b/run, GET /status
│   │   │   │   ├── phase_c.py                      # POST /api/phase-c/run, GET /status, GET /traces
│   │   │   │   ├── phase_d.py                      # POST /api/phase-d/run, GET /status
│   │   │   │   ├── certification.py                # POST /api/certification/run, GET /status
│   │   │   │   └── artifacts.py                    # Artifact retrieval for any phase
│   │   │   │
│   │   │   └── services/
│   │   │       ├── session_manager.py              # Session state tracking, persistence, recovery
│   │   │       └── progress_emitter.py             # Progress tracking & WebSocket emission
│   │   │
│   │   └── frontend/                               # React Frontend
│   │       ├── index.html                          # HTML entry point
│   │       ├── vite.config.ts                      # Vite build config (proxy to API)
│   │       ├── tailwind.config.js                  # Tailwind CSS theme config
│   │       ├── tsconfig.json                       # TypeScript config
│   │       ├── package.json                        # Node dependencies
│   │       │
│   │       └── src/
│   │           ├── main.tsx                         # React entry point
│   │           ├── App.tsx                          # Router & top-level routes
│   │           │
│   │           ├── api/
│   │           │   ├── client.ts                    # REST API client (all endpoint methods)
│   │           │   ├── types.ts                     # TypeScript interfaces for all data
│   │           │   └── websocket.ts                 # WebSocket client for real-time updates
│   │           │
│   │           ├── pages/
│   │           │   ├── Dashboard.tsx                # Home page: session list, quick-start
│   │           │   ├── SessionOverview.tsx          # Summary of all phases in one view
│   │           │   ├── PhaseA.tsx                   # Analysis UI: repo selector, agent map viewer
│   │           │   ├── PhaseB.tsx                   # Test generation UI: controls, preview
│   │           │   ├── PhaseC.tsx                   # Execution UI: live monitor, failure inbox
│   │           │   ├── PhaseD.tsx                   # Diagnosis UI: clusters, root causes, fixes
│   │           │   └── Certification.tsx            # Cert UI: tier badge, radar chart, certificate
│   │           │
│   │           ├── components/
│   │           │   ├── layout/
│   │           │   │   ├── AppShell.tsx             # Main layout wrapper
│   │           │   │   └── Sidebar.tsx              # Navigation sidebar
│   │           │   │
│   │           │   ├── shared/
│   │           │   │   ├── ProgressStepper.tsx      # Phase progress indicator
│   │           │   │   ├── StatusBadge.tsx          # Status pill (idle/running/done/error)
│   │           │   │   ├── PhaseProgress.tsx        # Phase progress bar
│   │           │   │   ├── ControlPanel.tsx         # Reusable controls panel
│   │           │   │   ├── FileExplorer.tsx         # File browser component
│   │           │   │   └── JsonViewer.tsx           # JSON data viewer
│   │           │   │
│   │           │   ├── phase-a/
│   │           │   │   ├── RepoSelector.tsx         # Repository path selector
│   │           │   │   ├── AnalysisOptions.tsx      # Analysis configuration options
│   │           │   │   └── AgentMapViewer.tsx        # Agent map visualization
│   │           │   │
│   │           │   ├── phase-b/
│   │           │   │   ├── GenerationControls.tsx   # Test generation config controls
│   │           │   │   └── TestSuitePreview.tsx     # Test suite preview table
│   │           │   │
│   │           │   ├── phase-c/
│   │           │   │   ├── ExecutionControls.tsx    # Execution settings & start button
│   │           │   │   ├── LiveMonitor.tsx          # Real-time test execution monitor
│   │           │   │   ├── ConversationView.tsx     # Conversation trace viewer
│   │           │   │   ├── EventFeed.tsx            # Live event feed
│   │           │   │   ├── FailureInbox.tsx         # Failure list with details
│   │           │   │   ├── SimulationCards.tsx      # Active simulation status cards
│   │           │   │   └── PersonaContextInput.tsx  # Persona context configuration
│   │           │   │
│   │           │   ├── phase-d/
│   │           │   │   ├── DiagnosisDashboard.tsx   # Diagnosis overview dashboard
│   │           │   │   ├── PriorityClusterList.tsx  # Failure clusters ranked by priority
│   │           │   │   ├── RootCauseChart.tsx       # Root cause distribution chart
│   │           │   │   ├── ToolFailureHeatmap.tsx   # Tool × failure type heatmap
│   │           │   │   ├── FixRoadmap.tsx           # Fix proposal roadmap
│   │           │   │   ├── MinimalReproViewer.tsx   # Minimal reproduction viewer
│   │           │   │   ├── ImprovementProjection.tsx # Projected improvement metrics
│   │           │   │   └── TriageSummaryBar.tsx     # Triage summary statistics bar
│   │           │   │
│   │           │   └── certification/
│   │           │       ├── TierBadge.tsx            # Platinum/Gold/Silver/Not Certified badge
│   │           │       ├── CategoryRadarChart.tsx   # Radar chart of scoring categories
│   │           │       ├── ScoreBreakdown.tsx       # Detailed score breakdown
│   │           │       ├── ConfidenceMeter.tsx      # Certification confidence meter
│   │           │       └── PrintableCertificate.tsx # Printable/exportable certificate
│   │           │
│   │           ├── hooks/                           # Custom React hooks
│   │           │   └── (session, phase, websocket hooks)
│   │           │
│   │           └── store/                           # Zustand state management
│   │               └── (session store, phase stores)
│   │
│   └── tests/                                      # Python test suites
│       ├── test_diagnosis.py                       # Phase D unit tests
│       ├── test_improvement.py                     # Phase E validation tests
│       └── test_pipeline.py                        # Full pipeline integration tests
│
├── fake-car-dealership-agent/                      # Example: TypeScript car dealership agent
│   ├── agent.ts                                    # Agent logic
│   ├── server.ts                                   # HTTP server
│   ├── tools/                                      # Agent tools
│   ├── prompts/                                    # Agent prompts
│   └── mock-data.ts                                # Mock inventory data
│
├── tlahuac_simulator_agent/                        # Tlahuac persona simulator agent
│
└── docs/                                           # Additional documentation
```

---

## How Each Phase Works

### Phase A: Analyze (`analyze.py` / `POST /api/phase-a/run`)

**Purpose**: Scan an agent's codebase and produce a structured **Agent Map** (JSON) describing everything the agent does.

**Pipeline**:
1. **Ingestion** (`src/ingestion/ingestor.py`) - Traverses the target directory, filters relevant files by extension/size, detects programming languages.
2. **Static Analysis** (`src/analysis/static_analyzer.py`) - Uses tree-sitter to parse ASTs, extracting functions, classes, imports, and call relationships.
3. **Pattern Detection** (`src/patterns/detector.py`) - Identifies frameworks (LangChain, CrewAI, AutoGen, etc.), tools, prompts, memory systems, and state management patterns.
4. **Risk Analysis** (`src/risk/analyzer.py`) - Flags PII handling, unsafe operations, critical tool chains, missing guardrails.
5. **AI Semantic Analysis** (`src/ai_analyzer/analyzer.py`) - Optionally uses Claude to perform deeper semantic analysis of agent behavior, intent patterns, and edge cases.
6. **Graph Building** (`src/graph/builder.py`) - Generates a NetworkX graph of agent components and their relationships.

**Output Artifact**: `agent_map.json`
- Tools, prompts, risks, framework info, component graph, language breakdown

---

### Phase B: Generate Tests (`generate_tests.py` / `POST /api/phase-b/run`)

**Purpose**: Create a comprehensive test suite tailored to the analyzed agent.

**Sub-Phases**:
- **B1 - Coverage Goals** (`coverage_builder.py`) - Define what tools, paths, and edge cases must be tested.
- **B2 - Personas** (`persona_builder.py`, `src/personas/`) - Build a diverse library of user personas with different communication styles, technical levels, and edge behaviors.
- **B3 - Scenarios** (`scenario_builder.py`, `src/scenarios/`) - Create a catalog of testing scenarios with user goals, difficulty levels, and success/failure conditions.
- **B4 - Suite Assembly** (`testsuite_builder.py`, `src/generator/`) - Combine personas x scenarios x coverage goals into a final test suite.

**Output Artifacts**:
- `persona_library.json` - All generated personas
- `scenario_catalog.json` - All generated scenarios
- `test_suite.json` - Final assembled test cases
- `test_configuration.json` - Generation parameters

---

### Phase C: Execute Tests (`execute_tests.py` / `POST /api/phase-c/run`)

**Purpose**: Run the test suite against the agent and collect results.

**Key Components**:
- **Test Execution Engine** (`src/execution/runner.py`) - Async parallel executor with configurable worker count.
- **Agent Connectors** (`src/execution/agent_connector.py`):
  - `MockAgentConnector` - Simulates agent locally with configurable failure rates (no API needed).
  - `APIAgentConnector` - Sends requests to a real HTTP endpoint.
  - `VictoriaConnector` - Integrates with Victoria simulator.
- **Conversation Simulator** (`src/execution/conversation_simulator.py`) - Uses Claude to drive multi-turn conversations as the test persona.
- **GAN Simulator** (`src/execution/gan_simulator.py`) - Adversarial testing mode with a Generator (persona) and Critic (quality evaluator) in a GAN-like loop.
- **Real-Time Monitor** (`src/execution/monitor.py`) - Streams live events over WebSocket to the frontend.
- **Results Aggregator** (`src/execution/aggregator.py`) - Computes pass/fail rates, timing stats, and failure categorization.

**Execution Modes**:
| Mode | Description |
|------|-------------|
| **Mock** | Simulated agent with configurable fail rate (great for testing the platform itself) |
| **Live API** | Hits a real agent HTTP endpoint |
| **GAN** | Adversarial testing: generator creates challenging inputs, critic evaluates response quality |

**Output Artifacts**:
- `test_run_report.json` - Pass/fail rates, timing, metrics
- `failure_inbox.json` - Failed tests with full context and stack traces
- `traces/` directory - Full conversation logs for each test

---

### Phase D: Diagnose Failures (`diagnose_failures.py` / `POST /api/phase-d/run`)

**Purpose**: Analyze failures from Phase C, identify root causes, and propose fixes.

**Pipeline**:
1. **Failure Clustering** (`src/diagnosis/clustering.py`) - Groups similar failures using TF-IDF vectorization or embedding-based similarity.
2. **Root Cause Analysis** (`src/diagnosis/root_cause_analyzer.py`) - Identifies root cause patterns:
   - `hallucination` - Agent fabricated information
   - `tool_selection_error` - Wrong tool chosen
   - `missing_guardrail` - Safety check absent
   - `state_management` - Conversation state lost/corrupted
   - `prompt_injection` - Vulnerable to injection attacks
   - `timeout` - Agent took too long
3. **Minimal Reproduction** (`src/diagnosis/minimal_reproducer.py`) - Generates the shortest possible test case to reproduce each failure cluster.
4. **Fix Proposals** (`src/diagnosis/fix_generator.py`) - AI-powered code fix suggestions with before/after diffs.
5. **Priority Ranking** (`src/diagnosis/priority_ranker.py`) - Ranks issues by `severity x frequency` impact score.

**Output Artifact**: `diagnosis_report.json`
- Failure clusters, root causes, minimal repros, fix proposals, priority ranking

**Diagnosis Metrics**:
- Bug Discovery Rate (unique failures per test)
- Redundancy Rate (duplicate findings %)
- Severity-Weighted Score (critical=5, high=3, medium=2, low=1)

---

### Phase E: Improve Agent (`improve_agent.py`)

**Purpose**: Apply fixes, validate them, and prepare for deployment.

**Pipeline**:
1. **Fix Application** (`src/improvement/fix_applicator.py`) - Applies proposed code changes from Phase D.
2. **A/B Testing** (`src/improvement/ab_testing.py`) - Runs baseline vs. fixed version comparison with statistical significance testing.
3. **Validation** (`src/improvement/validator.py`) - Statistical validation with p-values and confidence intervals.
4. **Regression Testing** (`src/improvement/regression_generator.py`) - Auto-generates regression tests from fixed failures.
5. **Deployment Packaging** (`src/improvement/deployment_packager.py`) - Builds deployment package with changelog, rollback docs.

**Output Artifacts**:
- `applied_fixes.json` - Applied changes log
- `ab_test_results.json` - A/B comparison results
- `improvement_report.json` - Overall improvement metrics
- `regression_tests.json` - Generated regression tests
- `deployment/` - Ready-to-deploy package

---

### Certification (`POST /api/certification/run`)

**Purpose**: Assign a quality tier to the agent based on all collected data.

**Scoring Categories** (each 0-100):
| Category | What It Measures |
|----------|------------------|
| **Reliability** | Pass rate, consistency across runs |
| **Safety** | Risk flags, edge case handling, guardrails |
| **Functionality** | Tool coverage, feature completeness |
| **Robustness** | Error handling, timeout handling, graceful degradation |
| **Transparency** | Log quality, state tracking, explainability |

**Certification Tiers**:
| Tier | Requirement |
|------|-------------|
| **Platinum** | Exceptional across all categories |
| **Gold** | Strong performance, minor gaps |
| **Silver** | Acceptable, notable improvement areas |
| **Not Certified** | Below minimum thresholds |

**Output Artifact**: `certification_report.json`
- Tier, per-category scores, confidence level, improvement recommendations

---

## API Endpoints

### Session Management
| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/sessions` | Create a new debugging session |
| `GET` | `/api/sessions` | List all sessions |
| `GET` | `/api/sessions/{id}` | Get session details and status |
| `POST` | `/api/sessions/{id}/save` | Explicitly save session state |
| `POST` | `/api/sessions/{id}/reset-phase/{phase}` | Reset a phase for re-execution |

### Filesystem
| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/fs/browse` | Browse directories on the host |
| `POST` | `/api/fs/resolve-directory` | Smart directory path resolution |

### Phase Execution
| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/phase-a/run` | Start Phase A analysis |
| `GET` | `/api/phase-a/status/{id}` | Poll Phase A progress |
| `POST` | `/api/phase-b/run` | Start Phase B test generation |
| `GET` | `/api/phase-b/status/{id}` | Poll Phase B progress |
| `POST` | `/api/phase-c/run` | Start Phase C test execution |
| `GET` | `/api/phase-c/status/{id}` | Poll Phase C progress |
| `GET` | `/api/phase-c/traces/{id}` | Retrieve conversation traces |
| `POST` | `/api/phase-d/run` | Start Phase D diagnosis |
| `GET` | `/api/phase-d/status/{id}` | Poll Phase D progress |
| `POST` | `/api/certification/run` | Start certification |
| `GET` | `/api/certification/status/{id}` | Poll certification progress |

### Real-Time
| Protocol | Path | Description |
|----------|------|-------------|
| `WebSocket` | `/ws/{session_id}` | Real-time progress events during phase execution |

---

## Data Flow

```
┌─────────────────┐
│  Create Session  │
└────────┬────────┘
         ▼
┌─────────────────┐     ┌──────────────────┐
│   Phase A       │────▶│  agent_map.json   │
│   (Analyze)     │     └────────┬─────────┘
└─────────────────┘              ▼
┌─────────────────┐     ┌──────────────────┐
│   Phase B       │────▶│  test_suite.json  │
│   (Generate)    │     │  personas.json    │
└─────────────────┘     │  scenarios.json   │
                        └────────┬─────────┘
                                 ▼
┌─────────────────┐     ┌──────────────────┐
│   Phase C       │────▶│  run_report.json  │
│   (Execute)     │     │  failures.json    │
└─────────────────┘     │  traces/          │
                        └────────┬─────────┘
                                 ▼
┌─────────────────┐     ┌──────────────────┐
│   Phase D       │────▶│  diagnosis.json   │
│   (Diagnose)    │     └────────┬─────────┘
└─────────────────┘              ▼
┌─────────────────┐     ┌──────────────────┐
│   Phase E       │────▶│  improvement.json │
│   (Improve)     │     │  deployment/      │
└─────────────────┘     └────────┬─────────┘
                                 ▼
┌─────────────────┐     ┌──────────────────┐
│  Certification  │────▶│  cert_report.json │
└─────────────────┘     └──────────────────┘
```

All artifacts are stored under `pipeline_output/{session_id}/`.

---

## Frontend State Management

The frontend uses **Zustand** for state management, tracking:

- **Current session ID** - Which debugging session is active
- **Phase statuses** - `idle` | `running` | `completed` | `error` for each phase
- **Phase results** - Agent map, test suite, execution report, diagnosis, certification
- **Phase progress** - Current step, message, and percentage for running phases
- **WebSocket connection** - Real-time updates from the backend

---

## Configuration

### Environment Variables
| Variable | Purpose |
|----------|---------|
| `ANTHROPIC_API_KEY` | Claude API access for AI analysis |
| `OPENAI_API_KEY` | Alternative LLM providers |
| Custom base URLs | Groq, Together, Ollama, etc. |

### Phase Defaults (from `web/api/config.py`)
| Phase | Default Settings |
|-------|-----------------|
| **A** | `skip_ai=False`, `language=None`, `prompt_encoding="utf-8"` |
| **B** | `count=150` tests, `persona_count=8`, `scenario_count=10`, `variants=3` |
| **C** | `workers=10`, `count=10`, `ai_personas=True`, `traces=True`, `fail_rate=0.05` |

### Session Persistence
Sessions are saved to `pipeline_output/{session_id}/session_state.json` and auto-recovered on backend startup. Individual phases can be reset and re-run without losing other phase data.

---

## Multi-LLM Support

The platform supports multiple LLM providers via `src/execution/llm_config.py`:

| Provider | Notes |
|----------|-------|
| **Anthropic** (Claude) | Default provider for all AI operations |
| **OpenAI-compatible** | Any OpenAI-compatible API |
| **Groq** | Fast inference |
| **Together** | Open-source models |
| **Ollama** | Local models |

Each phase can be configured to use a different model/provider.

---

## Example Agents (for Testing)

### `fake-car-dealership-agent/`
A TypeScript agent simulating a car dealership assistant. Includes:
- `agent.ts` - Core agent logic
- `server.ts` - HTTP server (endpoint for Phase C to hit)
- `tools/` - Agent tools (search inventory, schedule test drive, etc.)
- `prompts/` - System prompts
- `mock-data.ts` - Fake car inventory

### `tlahuac_simulator_agent/`
A pre-built simulator agent for persona injection and testing integration with the Tlahuac adapter.

---

## Key Architectural Patterns

1. **Phase Independence** - Each phase can run independently as a CLI command or via the API. Phases consume the previous phase's JSON artifacts.
2. **Artifact-Based Communication** - Phases communicate through JSON files, not in-memory state. This enables session persistence and phase re-runs.
3. **Real-Time Streaming** - WebSocket connections push live progress events from long-running phases to the frontend.
4. **Connector Abstraction** - Agent connectors abstract away how the agent is accessed (mock, HTTP, simulator), making the execution engine target-agnostic.
5. **GAN Architecture** - The adversarial testing mode uses a generator/critic pattern inspired by Generative Adversarial Networks to improve test quality.
6. **Multi-Provider LLM** - The platform isn't locked to a single AI provider; any OpenAI-compatible API can be used.
