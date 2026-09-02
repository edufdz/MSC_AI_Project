# Phase C (Execute) — Detailed Explanation

> **What this document is:** a self-contained, in-depth explanation of Phase C of the
> Agent-Testing Platform (`debugger-platforn/`): what it does, how it works
> internally, how it connects to the other phases, how pass/fail is decided, what it
> outputs, its known limitations, and how it has actually been used against the live
> TechRepair/Pulpoo agent. Companion docs: `PHASE_B_AND_C_EXPLAINED.md` (B→C handoff),
> `PHASES_A_TO_C.md` (field-level reference), `phase-c-enhancements/CONTEXT.md`
> (gap analysis + sprint plan), `FULL_CONTEXT.md` (project state).

---

## 1. What Phase C is, in one paragraph

Phase C is the **execution engine** of the pipeline. Phase A analyzes an agent's
source code and produces a machine-readable description of it (`agent_map.json`);
Phase B turns that description into a test suite of persona × scenario pairings
(`test_suite.json`). Phase C takes those two artifacts and **actually runs every
test as a live multi-turn conversation against the agent under test** — a real
HTTP-connected agent or a local mock — playing the *user* side with a simulated
persona, optionally injecting chaos (timeouts, corrupted responses, contradictory
data), deciding pass/fail for each conversation, and emitting an evidence-based
report: `test_run_report.json`, `failure_inbox.json`, `conversations.json`, and a
full per-test trace directory. Phase B answers *"what should we test?"*; Phase C
answers *"does the agent actually pass?"*.

```
Phase A (Analyze)         Phase B (Generate)            Phase C (Execute)              Phase D / Certify
agent source              agent_map.json                test_suite.json + agent map    failure_inbox.json
   │                          │                             │                              │
   ▼                          ▼                             ▼                              ▼
agent_map.json  ────►  test_suite.json  ────►  live conversations vs agent  ────►  diagnosis, fixes,
                       personas, scenarios     verdicts, traces, reports           certification tier
```

---

## 2. Inputs

Phase C reads exactly two artifacts. Each test case in `test_suite.json` is
**self-contained** — it embeds the full persona and scenario objects, so Phase C
never needs `persona_library.json` or `scenario_catalog.json` at runtime.

| Artifact | From | What Phase C uses it for |
|---|---|---|
| `test_suite.json` | Phase B | Test cases: persona (traits, style, edge behaviours), scenario (goal, success/failure conditions, chaos config), execution config (max turns, timeout), coverage goal, difficulty, and serialised oracles |
| `agent_map.json` | Phase A | `api_endpoint` (where the agent lives), `terminal_outcomes` (**what success means**), `tool_chains`, `confirmation_phrases`, tool schemas (for the mock connector), conversation language |

Because the agent map *directly configures the verdict logic at runtime*, the
quality of Phase A's outcome extraction bounds the validity of every Phase C
verdict. This has a critical operational consequence in this project:

> **The two-maps gotcha.** `tech_repair_whatsapp_map.json` is the pristine research
> map — it has **no terminal outcomes**, so every execute run against it scores 0
> vacuously. `tech_repair_whatsapp_map_live.json` is the execution map (terminal
> outcomes `order_status_provided` / `escalated_to_human`, Spanish confirmation
> phrases, `api_endpoint`, `runtime_tools`). **Always execute with the live map.**
> The web route auto-merges the live map's execution fields into session maps via
> `agent_endpoints.json` → `src/endpoints_config.py::apply_execution_overlay`.

---

## 3. Entry points

| Entry | Role |
|---|---|
| `execute_tests.py` | Standalone Phase C CLI (~40 options: `--mock`, `--ai-personas`, `--gan`, `--workers`, `--count`, `--language`, multi-provider LLM config, retry/backoff, live dashboards). Chains into Phase D with `--diagnose` and into D+E with `--improve`. |
| `run_pipeline.py` | Full A→B→C→D→E orchestrator; `--agent-map`/`--test-suite` skip A/B; `--stop-after c` halts after execution. |
| `run_experiments.py --mode execute` | Research path: executes each experimental arm's suite, diagnoses with offline Phase D, projects root causes onto the frozen 16-category taxonomy, scores against production ground truth. (Default `--mode static` **never runs Phase C** — it derives failures from what tests are *designed* to detect.) |
| Web UI | FastAPI backend (`web/api`) + React frontend. Endpoint field pre-fills from `agent_endpoints.json`; streams live progress over WebSocket; Conversations/Report/Failures download buttons on the completed view. |

A typical live run (agent on `:3098` in another terminal):

```bash
cd debugger-platforn && ./venv/bin/python execute_tests.py --persona-context \
  generated_tech_repair/test_suite.json tech_repair_whatsapp_map_live.json \
  --count 40 --workers 4 --ai-personas -o results_new --no-monitor
```

(`--persona-context` loads the pre-made Valeria context from
`config/persona_context_default.txt` — the setting every recorded run used. Pass
`--no-persona-context` to run without it; omitting both on a non-interactive
terminal is an error, so the choice can never be defaulted silently.)

---

## 4. Core architecture (`src/execution/`, ~4,200 LOC)

```
TestExecutionEngine (runner.py)
  │  async; bounded by a max_workers semaphore; 0.5s staggered starts
  │  per-test wall-clock timeout: restarts × max_turns × 6s + 60s
  │  MIN_TURNS_FOR_FAILURE = 6 → very short "Agent error" conversations are
  │  classified ERROR (infrastructure), not FAILED (real agent defect)
  │
  ├── ConversationSimulator (conversation_simulator.py)  ← plays the USER
  ├── GANConversationSimulator + CriticAgent             ← optional realism gate
  ├── AgentConnector (Mock / API / Victoria)             ← the wire to the agent
  ├── RealTimeMonitor (monitor.py)                       ← live progress
  ├── ResultsAggregator (aggregator.py)                  ← reports + inbox
  └── ConversationValidator (src/validation/)            ← optional AI triage
```

### 4.1 The conversation loop

`ConversationSimulator` drives each test as a realistic conversation, one turn at
a time, until a terminal outcome fires, the persona abandons, or `max_turns`
(default 40) is exhausted:

1. **Generate the persona's message.** Two modes:
   - **AI personas** (`--ai-personas`): an LLM role-plays the persona, respecting
     its 10 numeric traits (patience, clarity, tech savviness, politeness,
     verbosity, emotional volatility, trust, detail orientation, decision speed,
     language proficiency), communication style (tone, formality, typo rate,
     emoji), and edge behaviours (rage-quits, changes mind, incomplete info,
     off-topic, boundary-testing). Multi-provider via `llm_config.py`
     (Anthropic, Groq, Together, Fireworks, OpenAI, custom).
   - **Offline mode**: deterministic template messages by persona archetype —
     free, no API calls, used for CI and pipeline smoke tests.
   User-supplied **persona context** (`persona_context.py`) grounds the persona
   in real business data — in this project, the fake customer Valeria Mendoza
   García and her two TechRepair repair orders.
2. **Maybe inject chaos** (`_maybe_inject_chaos`, per-turn rolls when the test's
   `chaos_injection` config enables them): `timeout` (15%/turn — agent call
   skipped entirely), `malformed_response` (10% — response corrupted before the
   persona sees it), `data_conflict` (10% — contradictory info injected).
3. **Send the message to the agent** via the connector; receive the response and
   any reported tool calls.
4. **Record the turn** — message, response, tool calls with arguments/results,
   timing, chaos events — into the trace.
5. **Check the outcome** (`_check_outcome`, see §5).
6. **Update the persona's mood state**: frustration rises without progress, trust
   drops after errors, patience drains (faster for impatient personas). When
   frustration exceeds patience → **user_abandoned**.
7. Repeat.

### 4.2 Agent connectors — three ways to reach the agent

| Connector | When | How |
|---|---|---|
| **MockAgentConnector** | `--mock` / no endpoint | Fully local simulated agent: canned EN/ES responses, configurable fail rate (5%), tool-call rate (40%), simulated latency, tool-chain progression driven by the agent map. Good for pipeline tests; its failures are *random noise*, never research findings. |
| **APIAgentConnector** | Real agent over HTTP | `POST {endpoint}` with `{"message", "session_id"}`; expects `{response, tool_calls}`; 120s timeout. This is how the live TechRepair agent on `:3098` is exercised. |
| **VictoriaConnector** | Victoria-framework agents | Session cookies, 3-concurrent-request semaphore, exponential-backoff retries. |

### 4.3 GAN mode (optional adversarial quality loop)

`GANConversationSimulator` + `CriticAgent`: a critic scores conversation quality
(0–10) every N agent turns. Below the quality threshold it injects coaching or
restarts the conversation (up to 2 restarts). This gates **realism** — it filters
nonsensical exchanges that would create false failures — but it does *not* judge
verdict correctness and cannot compensate for the oracle gap (§7).

### 4.4 Monitoring

`RealTimeMonitor` consumes the engine's event queue and renders a live Rich
terminal dashboard: progress bar with ETA, pass/fail/error/timeout counters,
difficulty breakdown, recent results, tool-coverage tracker. The web API streams
the same events over WebSocket to the frontend.

---

## 5. How pass/fail is decided — the oracle that exists today

`ConversationSimulator._check_outcome()` is the **only** verdict mechanism,
evaluated after every agent turn. All three tiers are **tool-call-evidence based**
(a tool counts only if it was called AND returned `status == "ok"`):

1. **Terminal outcomes** (agent map, Phase A): an outcome fires when all its
   required tools are in the successful-tools set, optionally gated by
   confirmation phrases; each outcome carries `is_success`.
2. **Tool chains** (agent map): a chain completing with all tools successful → success.
3. **Legacy scenario `success_conditions`** (Phase B): required tool lists must
   be a subset of the successful tools.

Verdicts outside `_check_outcome`:
- **user_abandoned** — mood state degraded past patience.
- **max_turns exhausted** without a success → FAILED (generic, uncategorised).
- **ERROR vs FAILED**: conversations shorter than `MIN_TURNS_FOR_FAILURE = 6`
  that die with "Agent error" become ERROR (infrastructure), not FAILED. (Side
  effect: a genuine first-turn crash of a real agent is masked as ERROR.)

> **The key structural fact:** a conversation where the agent calls the right
> tools but *hallucinates the answer, loops, misunderstands the user, or never
> resolves the issue* is **invisible** to this oracle. This is the documented
> "oracle gap" (§7) and why live-agent runs report 94–100% pass rates even when
> the transcripts contain semantic failures.

**Oracles that exist but are never evaluated:** Phase B's Sprint E4 built
`src/oracles/` — 8 deterministic oracle types (postcondition, guardrail
compliance/violation, taint flow, tool sequence, state check, metamorphic, side
effect) — and serialises them onto every test case as `test_case.oracles`.
**Nothing in `src/execution/` reads them.** Oracle *generation* was delivered;
oracle *evaluation* (sprint X1) was not.

---

## 6. Outputs and downstream consumption

Everything lands in the run's output directory (`pipeline_output/{session}/results/`
for web runs, `-o <dir>` for CLI):

| Output | Contents |
|---|---|
| `test_run_report.json` | Pass rate, passed/failed/errors/timeouts, tool coverage (invocations per tool — using the live map's `runtime_tools`, not the 55 static-analysis names), breakdowns by difficulty and coverage goal, duration and cost totals |
| `failure_inbox.json` | One entry per failure: test id, scenario title, persona name, failure reason, tool-call sequence, chaos events, pointer to the trace file |
| `conversations.json` | **Every** dialogue (all statuses) with full turns + tool calls — added 2026-07-24; this is the artifact the real-vs-sim comparison consumes |
| `traces/trace_NNNN_ID.json` | Complete per-test record: turn-by-turn conversation, every tool call with arguments and results, timing, chaos events |
| `validated_failure_inbox.json` + `validation_report.json` | Only with `--validate`: an AI pass triages each failure as genuine / persona incompetence / chaos-induced / false success, filtering spurious results |

Downstream consumers:

- **Phase D (Diagnose)** clusters the failure inbox, identifies root causes,
  generates minimal repros and fix proposals → `diagnosis_report.json`.
- **Certification** scores the agent 0–100 across Safety & Trust (30%),
  Reliability (25%), Tool Competency (20%), Conversation Quality (15%),
  Efficiency (10%) and assigns Platinum/Gold/Silver tiers with hard blockers.
- **Research layer** (execute mode): diagnosis clusters are projected onto the
  frozen 16-category taxonomy and scored (precision/recall) against the 376
  production ground-truth failures. Failures not attributable to a specific test
  are pooled under `__unattributed__` and appended after the budget-ordered list
  (a known distortion for recall-vs-budget curves, sprint X5).
- **⚠ Web re-run gotcha:** re-running Phase C from the web UI **overwrites** the
  session's `results/` folder. This has already destroyed a 200-run's JSON
  exports once; recovered copy at
  `investigation/02_data/simulated/run_200tests_recovered.json`.

---

## 7. Known limitations (the honest part)

These are analysed in depth in `phase-c-enhancements/CONTEXT.md`; summarised here
because they shape how Phase C results must be read.

1. **The oracle gap.** The verdict logic sees only tool-call signatures. The
   production failure taxonomy is dominated by *semantic* categories —
   resolution, comprehension, data-gap, delivery, loops, hallucination — none of
   which leaves a tool-call signature. A synthetic conversation today cannot
   FAIL because of hallucinated content, a repetition loop, non-comprehension,
   non-resolution (it just times out into a generic max-turns failure), a
   guardrail violation, or PII leakage — even though oracles for the last two
   exist, unevaluated. **Threat to validity:** part of any measured coverage gap
   may be a measurement artifact of the oracle rather than a generation
   shortfall. (This is exactly why the real-vs-sim investigation bypasses the
   oracles entirely and applies the production rule-based scorer to
   `conversations.json` directly — see §8.)
2. **Static-mode headline numbers never run Phase C.** RQ1 recall 0.068 and RQ3
   0.112→0.312 are static-mode: derived from what tests are *designed* to
   detect, execution bypassed.
3. **Sandbox bridge v1 cannot intercept upstream tool execution.**
   `src/sandbox/bridge.py` exposes the `/chat` contract in three modes (echo /
   http / callable); in http mode it forwards messages and only overlays mock
   results on tool calls the upstream agent *reports back* — so
   backend-dependent failure modes (data_gap, delivery) cannot be provoked in a
   controlled way. `replay.py` computes an LLM-free fidelity score
   (0.5×response similarity + 0.3×tool-sequence Jaccard + 0.2×escalation
   agreement); echo baseline = 0.36.
4. **Chaos rates are hard-coded** (15/10/10% per turn), not calibrated against
   production stressor frequencies; mock-connector failures are random — never
   report mock execute-mode results as findings.

**Enhancement sprint plan** (from `phase-c-enhancements/CONTEXT.md`):

| Sprint | What | Status |
|---|---|---|
| X1 | Oracle evaluation engine — wire `test_case.oracles` into the simulator | planned |
| X2 | Taxonomy-aligned behavioural detectors (loop, non-resolution, comprehension, escalation) mirroring the production signal extractors | planned |
| **X3** | **Real-agent execute mode** — run the verbatim production agent locally and execute against it | **DONE** (see §8) |
| X4 | Bridge v2: true tool-execution interception; seed failure modes from production patterns | deferred |
| X5 | Measurement fixes: `__unattributed__` distribution, chaos calibration, mock-result guard | backlog |

---

## 8. Phase C in practice — the live TechRepair agent runs

Sprint X3 is done: `tech_repair-live-agent/` is a **verbatim copy of the production
Pulpoo WhatsApp agent** running against an in-memory fake Supabase (`bun run api`
→ `:3098`), wired to Phase C via `agent_endpoints.json` and the
`APIAgentConnector`. Every simulation converses with the fake customer **Valeria
Mendoza García** (two repair orders, one behind a disclosure gate the agent must
not reveal — verified working in every run).

All execute-mode runs to date:

| Run | N | Result |
|---|---|---|
| v1 (research map — the trap) | 10 | 0/10 vacuous (no terminal outcomes) |
| v2 (live map) | 10 | 9/10 |
| v3 (persona context on) | 10 | 10/10 |
| v4 (full suite) | 40 | 40/40, 100% tool coverage |
| 200-run (tiled suite, CLI) | 200 | 197/200 — 3 real repetition-loop failures |
| User web runs | 10, 150 | 141/150 (94%) |
| Scale study | 7 batches, 2,560 total | 21–30% failure rate under the production scorer |

The high oracle pass-rates (94–100%) are the oracle gap in action. The
dissertation's behavioural result therefore comes from applying the **identical
production rule-based scorer** to Phase C's `conversations.json` exports:
simulation reproduces **5/7 reachable real failure categories**, saturating at
N≈50 and flat through N=1000; the two misses (comprehension, data_gap) are
structural — over-cooperative personas and too-perfect fixtures — not
budget-limited. Full study in `investigation/` (report:
`investigation/05_report/report.pdf`).

---

## 9. Key file reference

| Concern | File |
|---|---|
| Engine, timeouts, ERROR/FAILED guard | `src/execution/runner.py` |
| Conversation loop, verdicts, chaos | `src/execution/conversation_simulator.py` (`_check_outcome` ~1144, `_maybe_inject_chaos` ~1390) |
| GAN mode | `src/execution/gan_simulator.py`, `src/execution/critic_agent.py` |
| Connectors | `src/execution/agent_connector.py` |
| Aggregation + conversations export | `src/execution/aggregator.py` |
| Persona LLM providers / business context | `src/execution/llm_config.py`, `src/execution/persona_context.py` |
| Post-execution AI triage | `src/validation/conversation_validator.py` |
| Static vs execute derivation, attribution | `src/experiments/runner.py` |
| Oracles (generated, unevaluated) | `src/oracles/`, attached in `src/scenarios/library.py` |
| Sandbox bridge + fidelity | `src/sandbox/bridge.py`, `src/sandbox/replay.py` |
| Execution-map overlay (web) | `src/endpoints_config.py` |
| Live agent | `tech_repair-live-agent/` (`:3098`) |
