# Phase C Enhancement Programme — Context

**Written: 2026-07-23.** Companion to `phase-a-enhancements/CONTEXT.md` and
`phase-b-enhancements/CONTEXT.md`. Read `docs/PROJECT_STATUS.md` first for
overall project state.

## What This Is

A detailed analysis of **Phase C (Execute)** of the Agent-Testing Platform
platform — its architecture, its interfaces with Phases A, B and D, its role
in the dissertation's central claim, and the evidence-based gaps that the
enhancement sprints must close.

## Why Phase C Is the Crux of the Dissertation

The dissertation ("Closing the Loop Between Synthetic Agent Testing and
Production Reality") asks: **could synthetic adversarial testing have
predicted the failures the real TechRepair/Pulpoo agent actually had?**

That question has two halves:

1. **Targeting** — do the generated tests *aim at* the right failure
   categories? (Phase B's job; measured today in "static" mode.)
2. **Behaviour** — do the executed tests *actually surface* those failures
   when run against an agent? (Phase C's job.)

The current headline results (RQ1 recall 0.068, RQ3 improvement
0.112 → 0.312) are **static-mode numbers: Phase C is never run to produce
them**. `run_experiments.py` derives each test's failures from what it is
*designed to detect* (`src/evaluation/harness.infer_detectable_failures`),
bypassing execution entirely (`src/experiments/runner.py:88-103`). Execute
mode exists and runs the full C → D → projection loop
(`src/experiments/runner.py:106-177`), but has only been demonstrated
against the echo stand-in agent, whose behavioural fidelity to production
is 0.36.

**Until Phase C can (a) run against a faithful agent and (b) detect the
production taxonomy's failure categories in synthetic conversations, the
dissertation's claim stays at "designed to detect", not "actually
detects".** Closing that gap is the purpose of this programme.

---

## 1. Architecture of Phase C

### 1.1 Entry points

| Entry | Role |
|---|---|
| `execute_tests.py` | Standalone Phase C CLI (Click). Chains into D with `--diagnose`, into D+E with `--improve` (`--apply-fixes` makes E real). ~40 options: `--mock`, `--ai-personas`, `--gan`, `--workers`, `--fail-rate`, `--language`, multi-provider persona/critic LLM config, retry/backoff, live dashboards (`--ui`, Rich monitor). |
| `run_pipeline.py` | Full A→B→C→D→E orchestrator; `--agent-map`/`--test-suite` skip A/B; `--stop-after c` halts after execution. |
| `run_experiments.py --mode execute` | Research path: executes each arm's suite, diagnoses with offline Phase D, projects root causes onto the shared 16-category taxonomy, and scores against production ground truth. |

### 1.2 Core runtime (`src/execution/`, ~4,200 LOC)

```
TestExecutionEngine (runner.py, 285 LOC)
  │  async, bounded by max_workers semaphore, 0.5s staggered starts
  │  per-test wall-clock timeout: restarts × max_turns × 6s + 60s
  │  MIN_TURNS_FOR_FAILURE = 6  → short conversations with "Agent error"
  │                               become ERROR (infra), not FAILED (real)
  │
  ├── ConversationSimulator (conversation_simulator.py, 1,480 LOC)
  │     plays the USER side of each conversation:
  │       1. generate persona message (LLM persona or offline scripted)
  │       2. maybe inject chaos           (_maybe_inject_chaos, line ~1390)
  │       3. send to agent via connector
  │       4. record turns / tool calls / tool results
  │       5. check terminal outcome        (_check_outcome, line ~1144)
  │       6. update persona mood state (frustration, trust, patience,
  │          turns_without_progress → user_abandoned)
  │       7. repeat until outcome, abandonment, or max_turns (default 40)
  │
  ├── GANConversationSimulator (gan_simulator.py, 341 LOC)
  │     + CriticAgent (critic_agent.py, 517 LOC)
  │     critic scores conversation quality every N agent turns;
  │     below quality_threshold → coaching injection or full restart
  │     (max_restarts, default 2)
  │
  ├── AgentConnector (agent_connector.py, 524 LOC)
  │     MockAgentConnector  — canned EN/ES responses, fail_rate,
  │                           tool_call_rate, simulated tool_chains
  │                           from the agent map, latency simulation
  │     APIAgentConnector   — POST {message, session_id} → {endpoint}/chat,
  │                           expects {response, tool_calls}
  │
  ├── RealTimeMonitor (monitor.py) — consumes engine event_queue;
  │     Rich terminal dashboard, live_viewer.py, web UI page
  │
  ├── ResultsAggregator (aggregator.py, 258 LOC)
  │     → test_run_report.json  (pass_rate, tool coverage %, breakdowns
  │        by difficulty / coverage goal, cost, durations)
  │     → failure_inbox.json    (per-failure: test_id, scenario, persona,
  │        failure_reason, trace_file, chaos events)
  │
  └── ConversationValidator (src/validation/conversation_validator.py)
        OPTIONAL post-execution pass: classifies results as genuine vs
        spurious (fake failures / fake successes), AI batch mode with
        heuristic fallback
```
 
Supporting modules: `llm_config.py` (352 LOC — multi-provider persona/critic
LLMs: Anthropic, Groq, Together, Fireworks, OpenAI, custom),
`persona_context.py` (user-supplied business context for personas),
`models.py` (TestResult, TestStatus, ConversationTurn, ChaosEvent).

### 1.3 How pass/fail is decided — the oracle that exists today

`ConversationSimulator._check_outcome()` (line ~1144) is the **only**
verdict mechanism, evaluated after every agent turn. Three tiers, all
tool-call-based:

1. **Terminal outcomes** from the agent map (Phase A): an outcome fires
   when its required tools are all in the set of *successfully-returned*
   tool calls (`_get_successful_tools()` — called AND `status == "ok"`),
   optionally gated by confirmation phrases. Each outcome carries
   `is_success`.
2. **Tool chains** from the agent map: a chain completing with all its
   tools successful → success.
3. **Legacy `success_conditions`** from the scenario (Phase B):
   `tool_called` / `all_of` tool lists must be a subset of successful tools.

Additional verdicts outside `_check_outcome`:
- **user_abandoned** — persona mood state degrades past its patience.
- **max_turns exhausted** without success → FAILED.
- **Chaos injection** (`_maybe_inject_chaos`): `timeout` (15%/turn),
  `malformed_response` (10%), `data_conflict` (10%) when enabled in the
  test's `chaos_injection` config.

> **Key structural fact:** a conversation in which the agent calls the
> right tools but hallucinates the answer, loops, misunderstands the user,
> or never actually resolves the issue is **invisible** to this oracle.
> See §4.2.

### 1.4 The sandbox bridge — Phase C's door to reality (`src/sandbox/`)

`bridge.py` (451 LOC) exposes exactly the `/chat` contract
`APIAgentConnector` expects, in three upstream modes:

- **echo** — fully offline keyword-routed stand-in agent (CI-safe).
- **http** — forwards to a wrapped real agent (the planned `pulpoo-final`
  local deployment). **v1 limitation (documented in the module docstring):
  the bridge does not intercept the upstream agent's tool execution
  mid-flight** — it forwards the message, passes through the response, and
  only overlays mock results for returned tool calls whose names are
  registered. True interception is planned v2.
- **callable** — in-process, for tests.

Every tool call routes through `MockToolRegistry` (deterministic failure
injection, never touches production tools); every conversation is captured
as a `SandboxTrace` JSONL for offline analysis.

`replay.py` (303 LOC) replays recorded production conversations against a
sandbox endpoint and computes an LLM-free **fidelity score**:
`0.5 × response similarity (difflib) + 0.3 × tool-sequence Jaccard +
0.2 × escalation agreement`. **Echo-mode baseline: 0.36** — the number any
real-agent deployment must beat.

### 1.5 Outputs and downstream consumption

```
TestResult[]  ──ResultsAggregator──►  test_run_report.json ─┐
              └────────────────────►  failure_inbox.json  ──┼──► Phase D
                                      traces/*.json  ───────┘   (cluster →
                                                                 root cause →
                                                                 fix proposals)
Research layer (execute mode):
  diagnosis_report.json ──projection.py──► shared 16-category taxonomy
                        ──measurement.py─► precision/recall vs production
                                           ground truth (376 real failures)
```

Per-test attribution in execute mode: each diagnosed cluster's failures are
attributed back to the test IDs in its `failure_examples`; failures with no
attributable test are pooled under `__unattributed__` and **appended after
the budget-ordered tests** (`src/experiments/runner.py:174-177`) — see
gap §4.4.

---

## 2. Connection to Phase A (Analyze)

Phase A's `agent_map.json` does not merely feed Phase B — it **directly
configures Phase C at runtime**:

| Agent-map field | Phase C consumer | Effect |
|---|---|---|
| `components.tools[]` | `MockAgentConnector.available_tools` | What the mock agent can "call" |
| `terminal_outcomes` | `_check_outcome()` tier 1 | **Defines what success means** |
| `tool_chains` | `_check_outcome()` tier 2 + mock chain simulation | Multi-turn goal completion |
| `confirmation_phrases` | outcome signal matching | Textual completion evidence |
| `mock_confirmation_messages` | mock connector | Chain-completion replies |
| `api_endpoint` | `APIAgentConnector` | Where the real agent lives |
| `metadata.conversation_language` | language auto-detection | ES/EN persona + mock responses |

Consequence: **the quality of Phase A's outcome extraction bounds the
validity of every Phase C verdict.** If Phase A misses a terminal outcome
or a tool chain, Phase C falls back to legacy scenario conditions or to
"some tool succeeded", and verdicts degrade silently. (Note:
`tech_repair_whatsapp_map.json` predates the Phase A code-tree feature and
should be regenerated — PROJECT_STATUS §6.3.)

## 3. Connection to Phase B (Generate)

Each `TestCase` in `test_suite.json` embeds everything Phase C needs:

| TestCase field | Phase C consumer | Effect |
|---|---|---|
| `persona` (traits, style, edge behaviours, messages) | LLM persona prompt + `MoodState` init | Drives the simulated user's behaviour, patience, abandonment |
| `scenario.success_conditions` / `failure_conditions` | `_check_outcome()` tier 3 | Legacy pass/fail |
| `scenario.chaos_config` → `execution_config.chaos_injection` | `_maybe_inject_chaos()` | Stress injection |
| `execution_config.max_turns` | loop bound + timeout budget | Conversation length |
| `test_case.oracles` (Sprint E4.5 serialisation) | **NOBODY — never evaluated** | see §4.2 |
| `coverage_goal`, `difficulty`, `target_tool` | reporting breakdowns | Aggregation only |

The Phase B Sprint E4 programme built `src/oracles/` — deterministic,
non-LLM oracles derived from Phase A data (8 types: postcondition,
guardrail compliance/violation, taint flow, tool sequence, state check,
metamorphic, side effect), attached to scenarios by
`src/scenarios/library.py` and serialised onto test cases via
`Oracle.to_test_case_dict()`. **Phase B delivered oracle *generation*;
oracle *evaluation* — Phase C's half of Sprint E4 — was never built.**
A grep across `src/execution/` finds zero references to oracles.

---

## 4. Gap Analysis (evidence-based)

### 4.1 The headline numbers never exercise Phase C

Static mode measures suite *targeting*, deterministically and offline —
by design, and correctly labelled. But it means the dissertation's core
numbers say nothing about whether executed conversations surface those
failures. Execute mode is implemented end-to-end
(`_executed_failures_per_test`: run engine → aggregate → offline Phase D →
project → attribute) but has only ever run against:
- **MockAgentConnector** — canned responses with a *random* 5% failure
  rate: its failures are noise uncorrelated with any real agent defect;
- **echo sandbox** — fidelity 0.36 vs production.

**Impact:** RQ1 in behavioural terms is unanswered. PROJECT_STATUS §4.3
already flags this as the highest-value optional work.

### 4.2 The oracle gap — Phase C cannot see the failures that matter

The verdict logic (§1.3) is exclusively tool-call-evidence-based. Compare
with what production ground truth says actually fails
(`src/production/`, human-process signals: escalations, human takeovers,
delivery failures, intent/confidence telemetry) and with the RQ2 gap
categories: **resolution, comprehension, data-gap, delivery, loops,
hallucination** — all semantic, conversational, or long-horizon. None of
them leaves a tool-call signature.

Concretely, a synthetic conversation today **cannot FAIL because of**:
- hallucinated content (no groundedness check against tool results),
- a repetition/loop (no turn-similarity detection),
- non-comprehension (no detection of the persona re-explaining),
- non-resolution (ending without terminal outcome just times out into a
  generic "max turns" failure with no category),
- a guardrail violation (oracles exist for this but are never evaluated),
- PII leakage (taint-flow oracles exist, never evaluated).

**Impact — threat to validity:** part of the measured RQ2 "coverage gap"
may be a *measurement artifact of Phase C's oracle*, not purely a
generation shortfall. Even a perfect Phase B suite executed against the
real agent would under-report exactly these categories. This must either
be fixed (preferred) or explicitly acknowledged in the dissertation's
threats-to-validity section.

**Symmetry argument (for the write-up):** production ground truth is built
from human-process signals. Phase C should detect the *analogous* signals
in synthetic conversations (agent escalation calls, loops, unresolved
endings, repeated intents), so that the projection onto the shared
taxonomy compares like with like on both sides.

### 4.3 Sandbox fidelity ceiling

Bridge v1 in http mode cannot intercept the real agent's internal tool
execution — so failure injection (`MockToolRegistry`) only touches tool
calls the upstream *reports back*, and backend-dependent failure modes
(data-gap, delivery — two of the RQ2 gap categories) cannot be provoked in
a controlled way. Fidelity 0.36 (echo) is the only measured point; no
real-agent fidelity number exists yet.

### 4.4 Execute-mode measurement mechanics

- The `__unattributed__` failure pool is appended *after* the
  budget-ordered per-test list, so unattributed failures only count at the
  final budget point — this can distort recall-vs-budget curves (RQ4) in
  execute mode.
- Chaos probabilities are hard-coded (15/10/10 % per turn) and not
  calibrated against production stressor frequencies (Phase B backlog
  E10's concern, but the injection site lives in Phase C).
- Mock failure rate (5%) and chaos are both *random*, so execute-mode
  results against mock are seed-sensitive noise; fine for pipeline tests,
  meaningless for research numbers — worth an explicit guard so mock
  execute-mode results are never reported as findings.

### 4.5 Minor robustness notes

- `MIN_TURNS_FOR_FAILURE = 6` is a sensible infra/real discriminator but
  will also mask *genuine* first-turn catastrophic failures of a real
  agent (e.g. crash on greeting) as ERROR — acceptable, but document it.
- The GAN critic gates conversation *quality* (realism), not verdict
  correctness — it cannot compensate for the oracle gap.

---

## 5. Enhancement Sprint Plan

Ordered by dissertation payoff per unit effort. Naming continues the
Phase B convention (Execution sprints = "X").

| Sprint | Name | Effort | Pays into |
|---|---|---|---|
| **X1** | **Oracle evaluation engine** — wire `test_case.oracles` into `ConversationSimulator`: evaluate postcondition / tool-sequence / guardrail / taint / side-effect oracles per turn and at conversation end; verdicts carry `oracle_id` + severity into `failure_reason` and the trace; metamorphic relations evaluated pairwise post-run by the aggregator. Completes Phase B Sprint E4's missing half. | Medium | RQ1/RQ2 measurement validity |
| **X2** | **Taxonomy-aligned behavioural detectors** — deterministic, LLM-free detectors mirroring the production ground-truth signal extractors: loop detection (n-gram / difflib similarity across agent turns), non-resolution (terminal-outcome absence at end), comprehension failure (persona repeats/rephrases, intent re-statements), escalation signals (agent escalation tool or phrase), abandonment semantics. Each detector emits a shared-taxonomy category directly, making Phase C failures commensurable with production failures without relying on Phase D clustering. Optional LLM-judge groundedness check for hallucination, clearly flagged as such. | Medium | RQ2 (removes measurement artifact), RQ1 execute |
| **X3** | **Real-agent execute mode** — run `pulpoo-final` locally behind the sandbox bridge (http mode); measure replay fidelity vs the 0.36 echo baseline; re-run RQ1 and RQ3 with `--mode execute --connector http://localhost:8099`; report behavioural numbers alongside static ones. Requires X1/X2 to be meaningful (see §4.2). | Medium (ops-heavy) | The headline behavioural claim |
| **X4** | **Sandbox bridge v2** — upstream tool-execution interception (upstream delegates tool calls to the bridge); seed `MockToolRegistry` failure modes from production failure patterns (data-gap: empty/missing records; delivery: send-failure responses) so chaos can provoke the missed categories deliberately. | Large | RQ2 gap categories become testable |
| **X5** | **Execute-mode measurement fixes** — distribute `__unattributed__` failures across budget points defensibly (or attribute via trace test_ids); calibrate chaos rates from production stressor frequencies; hard guard preventing mock-connector execute results from entering research reports. | Small | RQ4 execute-mode integrity |
| **XT** | **Testing** — unit tests for every detector/oracle evaluation path with synthetic transcripts (known-failure fixtures per taxonomy category); regression fixture from a real anonymised conversation per category. | Small | Everything above |

### Recommended order

```
Week 1:   X1 (oracle evaluation) + XT fixtures    — cheapest, unblocks everything
Week 1-2: X2 (behavioural detectors)              — the scientific upgrade
Week 2:   X3 (real-agent execute run)             — the dissertation's behavioural numbers
Backlog:  X5 (measurement fixes) alongside X3
Defer:    X4 (bridge v2) — only if X3's fidelity score shows tool-level
          divergence is the binding constraint
```

### Decision thresholds

- If X3's real-agent fidelity ≤ echo baseline (0.36) → the local deployment
  is not faithful; report static numbers as primary and fidelity as the
  documented limitation, rather than publishing execute-mode numbers.
- If execute-mode recall after X1+X2 ≈ static recall → static mode was a
  good proxy; that is itself a reportable methodological finding.
- If X2 detectors fire heavily on categories the static gap analysis
  called "missed" → quantifies how much of RQ2 was measurement artifact
  vs generation shortfall — a headline dissertation result either way.

### What this buys the dissertation

Items X1–X3 upgrade the central claim from *"the suites were designed to
target the real failure categories"* to *"when executed, the system
detected N% of the real system's failure categories"* — with the
static-vs-execute delta and the fidelity score as honest, quantified
qualifiers. X2's symmetry with the production signal extractors also
strengthens the taxonomy-projection defence (both sides of the comparison
detect failures from the same class of observable signals).

---

## 6. Key file reference

| Concern | File | Lines of interest |
|---|---|---|
| Engine, timeout, ERROR/FAILED guard | `src/execution/runner.py` | 157–181 |
| Verdict logic | `src/execution/conversation_simulator.py` | `_check_outcome` ~1144, `_get_successful_tools` ~1226 |
| Chaos injection | `src/execution/conversation_simulator.py` | `_maybe_inject_chaos` ~1390 |
| Connectors | `src/execution/agent_connector.py` | Mock 75+, API ~350+ |
| Aggregation, post-validation hook | `src/execution/aggregator.py` | 30–110 |
| Static vs execute failure derivation | `src/experiments/runner.py` | 88–103 / 106–177 |
| Attribution tail | `src/experiments/runner.py` | 161–177 |
| Oracle models (generated, unevaluated) | `src/oracles/models.py` | all |
| Oracle attachment in Phase B | `src/scenarios/library.py` | 671+, 779+ |
| Bridge modes + v1 limitation | `src/sandbox/bridge.py` | module docstring |
| Fidelity score | `src/sandbox/replay.py` | 1–35 |
| Production ground-truth signals (the symmetry target) | `src/production/` | — |
| Post-execution genuine/spurious validation | `src/validation/conversation_validator.py` | — |
