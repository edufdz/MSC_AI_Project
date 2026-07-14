# Phase B & Phase C — How Test Generation Feeds Test Execution

> This document explains what Phase B produces, what Phase C does with it, and how the two phases connect through shared artifacts. For low-level implementation details of every field and function, see `PHASES_A_TO_C.md`.

---

## High-Level Picture

```
Phase A (Analyze)          Phase B (Generate Tests)        Phase C (Execute Tests)
─────────────────          ────────────────────────        ──────────────────────────
Scans agent source    →    Reads agent_map.json       →    Reads test_suite.json
Produces agent_map.json    Produces test_suite.json        + agent_map.json
                           + persona_library.json          Runs conversations against agent
                           + scenario_catalog.json         Produces test_run_report.json
                           + test_configuration.json       + failure_inbox.json + traces/
```

Phase B's job is to answer: **"What should we test, and how?"**
Phase C's job is to answer: **"Does the agent actually pass?"**

---

## Phase B: Generate Tests

### Goal

Transform a static description of an agent (the Agent Map) into a complete, executable test suite. The test suite must guarantee coverage of every tool, exercise edge cases, inject chaos, and use realistic user personas — all without requiring a human to write a single test by hand.

### What Phase B Reads from Phase A

Phase B loads `agent_map.json` and extracts:

| Field | Used for |
|-------|----------|
| `components.tools[].name` | Coverage targets — every tool must be exercised |
| `components.tools[].risk_level` | Determines how many times each tool is tested (critical: 25×, high: 15×, medium: 10×, low: 5×) |
| `components.tools[].read_only` | Shapes persona behavior — write tools get "changes mind" personas |
| `components.tools[].handles_sensitive_data` | Adds "tests boundaries" behavior to attacking personas |
| `components.tools[].parameters` | Parameter complexity drives tool-attack persona difficulty |
| `metadata.type` | Selects domain-appropriate persona and scenario templates (support, sales, scheduling, etc.) |
| `metadata.purpose` | Seeds AI persona generation prompts |
| `metadata.conversation_language` | Filters templates by language (Spanish, English, Portuguese) |
| `risk_flags.pii_handling` | Enables PII detection in sandbox config |
| `risk_flags.critical_actions` | Critical tools require confirmation gates in sandbox |
| `tool_chains[].sequence` | Creates flow-attack personas that stress multi-step tool sequences |
| `success_criteria.max_turns` | Sets safety limits in sandbox configuration |
| `success_criteria.max_cost_per_conversation` | Sets cost limits per test episode |

### The Four Sub-Steps

#### B1: Coverage Configuration (`src/coverage/calculator.py`)

Answers: *"How many tests of each type do we need?"*

- Calculates **minimum invocations per tool** based on risk level
- Generates **tool combination pairs** for high/critical-risk tools
- Scales **edge-case counts** (ambiguous requests, incomplete info, mind-changing, contradictions) by the agent's overall risk profile
- Scales **stressor counts** (timeouts, malformed responses, data conflicts) by tool count
- Produces **sandbox configuration**: mock/real mode per tool, cost limits, safety limits, PII detection

Output: `test_configuration.json`

#### B2: Persona Library (`src/personas/builder.py`)

Answers: *"Who is talking to the agent?"*

Each persona is a synthetic user with 10 numeric traits (patience, clarity, tech savviness, politeness, verbosity, emotional volatility, trust level, detail orientation, decision speed, language proficiency), a communication style (tone, formality, typo rate, emoji use), and edge behaviors (rage quits, changes mind, provides incomplete info, asks off-topic, tests boundaries).

**Five persona sources:**

| Source | What it creates | When used |
|--------|----------------|-----------|
| **Templates** | 20+ pre-built personas per domain | Always (offline, free) |
| **AI-generated** | Claude creates diverse personas filling trait gaps | When `skip_ai=False` |
| **Tool-attack** | One adversarial persona per tool, designed to stress that specific tool | Always |
| **Flow-attack** | One persona per tool chain, designed to stress multi-step sequences | When tool chains exist |
| **External (Tlahuac)** | Custom persona packs from external providers | When `use_tlahuac=True` |

Personas are deduplicated by cosine similarity on traits (threshold 0.85) to ensure diversity.

Output: `persona_library.json`

#### B3: Scenario Catalog (`src/scenarios/library.py`)

Answers: *"What situations should the agent face?"*

Each scenario defines a user goal, required/optional/forbidden tools, success conditions (which tools must be called, what info must be provided), failure conditions (hallucination, wrong tool, PII leak), chaos injection probabilities, and estimated conversation length.

**Four scenario sources:**

| Source | What it creates |
|--------|----------------|
| **Templates** | 50+ built-in scenarios across domains |
| **AI-generated** | Claude creates scenarios tailored to the agent's specific tools |
| **Variants (AI)** | 7 variant dimensions per base scenario: ambiguity, missing info, interruption, constraint, error, multi-step, adversarial |
| **Variants (offline)** | 5 deterministic variants when AI is skipped |

Output: `scenario_catalog.json`

#### B4: Test Suite Assembly (`src/generator/test_suite.py`)

Answers: *"Which persona talks in which scenario?"*

The generator fills `target_count` test slots (default 150) using a priority-based 4-phase allocation:

```
Phase 1: Tool Coverage Tests
   For each tool, generate enough tests to meet minimum invocation count.
   Prefer tool-attack personas + scenarios that require that tool.
       ↓
Phase 2: Edge-Case Tests
   Allocate tests for ambiguity, missing info, mind-changing, contradictions.
   Prefer error_path scenarios with matching variant types.
       ↓
Phase 3: Stressor Tests
   Generate chaos injection tests (forced timeouts, corrupted responses, data conflicts).
   Override chaos_config with high injection probabilities.
       ↓
Phase 4: Scenario Fill
   Pad remaining slots with random persona × scenario pairs
   to reach target_count.
```

Each test case bundles: a full scenario object, a full persona object, an execution config (max turns, timeout, chaos settings, PII detection), a coverage goal label, and a difficulty rating.

Output: `test_suite.json` — the primary artifact consumed by Phase C.

### Test Suite Summary

The test suite includes a `summary` section with:
- Total tests, breakdown by difficulty (easy/medium/hard)
- Breakdown by coverage goal (tool_coverage, edge_case, stressor, scenario_fill)
- Expected tool invocation counts per tool
- Estimated duration in minutes
- Estimated cost in USD (turns × $0.002)

---

## What Phase B Passes to Phase C

Phase C reads two artifacts:

| Artifact | Source | Contains |
|----------|--------|----------|
| `test_suite.json` | Phase B | All test cases with embedded scenarios, personas, and execution configs |
| `agent_map.json` | Phase A | Agent metadata, tools, API endpoint, confirmation phrases, terminal outcomes |

Each test case in `test_suite.json` is self-contained — it carries the full persona and scenario objects, not references. Phase C does not need `persona_library.json` or `scenario_catalog.json` at runtime.

### What Phase C needs from the Agent Map

| Field | Used for |
|-------|----------|
| `metadata.api_endpoint` | Where to send HTTP requests to the agent |
| `metadata.conversation_language` | Language for persona message generation |
| `metadata.http_timeout_sec` | Timeout for agent API calls |
| `components.tools` | Tool schema for mock connector simulation |
| `terminal_outcomes` | Goal-driven success detection during conversations |
| `tool_chains` | Mock connector simulates tool chain progression |
| `confirmation_phrases` | Detect when agent asks for confirmation |

---

## Phase C: Execute Tests

### Goal

Run every test case against the actual agent (or a mock) and produce an evidence-based report of what passed, what failed, and why. Phase C is the empirical counterpart to Phase B's theoretical coverage plan.

### The Execution Pipeline

```
Load test_suite.json + agent_map.json
         ↓
Create Agent Connector (Mock / API / Victoria)
         ↓
TestExecutionEngine.run_all()
    │
    ├── For each test case (parallel, up to 10 workers):
    │       │
    │       ├── ConversationSimulator.run()
    │       │       │
    │       │       ├── Generate opener message (from scenario starters or AI)
    │       │       │
    │       │       ├── LOOP (up to max_turns):
    │       │       │   ├── Maybe inject chaos (timeout / malformed / conflict)
    │       │       │   ├── Send persona message → Agent
    │       │       │   ├── Receive agent response + tool calls
    │       │       │   ├── Record conversation turn
    │       │       │   ├── Update mood state (frustration, trust, patience)
    │       │       │   ├── Check success conditions (tools called? goal met?)
    │       │       │   ├── Check failure conditions (hallucination? PII leak?)
    │       │       │   └── Generate next persona message
    │       │       │
    │       │       └── Return conversation result
    │       │
    │       └── Record TestResult (status, turns, tools, duration, cost)
    │
    ├── ResultsAggregator.save_report()
    │       └── test_run_report.json
    │
    ├── Generate failure_inbox.json
    │
    └── [Optional] ConversationValidator.validate_results()
            └── validated_failure_inbox.json + validation_report.json
```

### Agent Connectors

Phase C supports three ways to connect to the agent under test:

| Connector | When used | How it works |
|-----------|-----------|-------------|
| **MockAgentConnector** | `mock=True` or no real endpoint | Simulates agent responses locally with configurable failure rate (5%), tool call rate (40%), and latency (50-300ms). Simulates tool chain progression. |
| **APIAgentConnector** | Real agent with HTTP endpoint | Sends `POST {endpoint}` with `{"message": str, "session_id": str}`. 120s timeout. Parses tool calls from response. |
| **VictoriaConnector** | Victoria-framework agents | Specialized protocol with session cookies, 3-concurrent-request semaphore, and exponential backoff retry. |

### Conversation Simulator

The simulator (`src/execution/conversation_simulator.py`) drives realistic multi-turn conversations:

**Persona message generation:**
- **AI mode** (`ai_personas=True`): Claude role-plays the persona, respecting all traits, mood drift, and edge behaviors. Produces natural, varied dialogue.
- **Offline mode** (`ai_personas=False`): Template-based messages selected by persona archetype. Deterministic and free — no API calls.

**Mood drift model:**
The simulator tracks how the persona's emotional state evolves during the conversation. Frustration increases when the agent fails to make progress. Trust decreases after errors. Patience drains over time, faster for impatient personas. When frustration exceeds patience, adversarial personas may rage-quit.

**Chaos injection:**
On each turn, the simulator rolls against the test's chaos probabilities:
- **Timeout**: Agent call is skipped entirely — tests whether the agent/system handles timeouts gracefully
- **Malformed response**: Agent response is corrupted before the persona sees it — tests error handling
- **Data conflict**: Contradictory information is injected — tests how the agent handles inconsistency

### GAN Mode (Adversarial Quality Loop)

An optional adversarial mode (`src/execution/gan_simulator.py`) adds a Critic Agent that evaluates conversation quality every N turns:

```
Generator (persona + agent conversation)
         ↕
Critic Agent (scores quality 0-10)
         │
         ├── Score ≥ 3.0 → Continue or Accept
         └── Score < 3.0 → Restart conversation (up to 2 restarts)
```

This ensures test conversations are realistic enough to produce meaningful results, filtering out nonsensical exchanges that would create false failures.

### Real-Time Monitoring

During execution, a `RealTimeMonitor` (`src/execution/monitor.py`) consumes events from the execution queue and displays:
- Live progress bar with ETA
- Pass/fail/error/timeout counters
- Difficulty-level breakdown
- Recent failures and passes
- Tool coverage tracker

The web API streams these same events over WebSocket to the frontend.

### Results Aggregation

The `ResultsAggregator` (`src/execution/aggregator.py`) compiles all test results into:

**test_run_report.json:**
- Pass rate, total tests, passed/failed/errors/timeouts
- Tool coverage: invocations per tool, tools not covered, coverage percentage
- Breakdowns by difficulty and coverage goal
- Duration and cost totals

**failure_inbox.json:**
Each failed test includes: scenario title, persona name, failure reason, tools called sequence, chaos events that occurred, and a pointer to the full conversation trace file.

**traces/ directory:**
One JSON file per test (`trace_NNNN_ID.json`) containing the complete turn-by-turn conversation, every tool call with arguments and results, timing data, and chaos events.

### Optional: AI-Powered Failure Validation

When `validate=True`, a `ConversationValidator` (`src/validation/conversation_validator.py`) uses AI to triage failures:

| Classification | Meaning | Action |
|----------------|---------|--------|
| **Genuine failure** | Agent truly failed the scenario | Kept in failure inbox |
| **Persona incompetence** | Unrealistic user behavior caused the failure | Filtered out |
| **Chaos-induced** | Failure was caused by injected chaos, not agent fault | Filtered out |
| **False success** | Agent appeared to pass but hallucinated the outcome | Moved to failures |

This produces a `validated_failure_inbox.json` with only genuine failures and a `validation_report.json` summarizing what was filtered.

---

## What Happens After Phase C

Phase C's outputs feed into two downstream stages:

### Phase D: Diagnosis (`src/diagnosis/engine.py`)

Reads the failure inbox and clusters failures into groups of similar issues. For each cluster:
- Identifies the root cause (wrong tool selection, missing guardrail, hallucination pattern, etc.)
- Generates a minimal reproduction scenario
- Proposes concrete fixes (prompt patches, code changes, validation rules, config changes)
- Ranks clusters by priority (severity × frequency)

Output: `diagnosis_report.json`

### Certification (`src/certification/certifier.py`)

Reads the test run report + diagnosis report and scores the agent across five categories:

| Category | Weight | What it measures |
|----------|--------|-----------------|
| **Safety & Trust** | 30% | Hallucination rate, guardrail gaps, validation coverage |
| **Reliability** | 25% | Pass rate, timeout rate, error handling |
| **Tool Competency** | 20% | Tool coverage, selection accuracy, schema compliance |
| **Conversation Quality** | 15% | Pass rate adjusted by difficulty, response time |
| **Efficiency** | 10% | Cost per test, response latency |

The overall score (0-100) maps to a certification tier:

| Tier | Score | Requirements |
|------|-------|-------------|
| **Platinum** | ≥ 90 | ≥ 100 simulations, ≤ 1% hallucination, no critical blockers |
| **Gold** | ≥ 75 | ≥ 50 simulations, ≤ 3% hallucination, no guardrail blockers |
| **Silver** | ≥ 60 | ≥ 20 simulations, ≤ 8% hallucination |
| **Not Certified** | < 60 | Below thresholds or critical failures present |

Hard blockers (critical hallucinations, missing guardrails on high-risk tools, pass rate < 70%) can prevent tier assignment regardless of score. Confidence is measured using a Wilson score interval at 95% confidence level.

Output: `certification_report.json` with tier, scores, strengths, improvements, and radar chart data for visualization.

---

## Complete Artifact Flow

```
repo_path
    │
    ▼
 PHASE A ──► agent_map.json
                 │
                 ▼
 PHASE B ──► test_suite.json  +  persona_library.json
                 │                scenario_catalog.json
                 │                test_configuration.json
                 ▼
 PHASE C ──► test_run_report.json  +  failure_inbox.json  +  traces/
                 │
                 ▼
 PHASE D ──► diagnosis_report.json
                 │
                 ▼
 CERTIFY ──► certification_report.json  (tier + score + radar chart)
```

Every artifact is JSON. Every phase is independently re-runnable. Session state persists in `pipeline_output/{session_id}/`.
