# Dissertation ↔ Repository Audit

Every factual claim about the deployed system, checked against the code and the
data. Paths are relative to the repository root. `WA/` abbreviates
`tech_repair-live-agent/server-mirror/services/agents/whatsapp/`.

Verdicts: **CONFIRMED** · **PARTLY** · **WRONG** · **NOT FOUND**

---

## Priority list — fix these first

| # | Claim | Verdict | Where |
|---|---|---|---|
| 1 | "guardrails are written in English" while conversations are Spanish | **WRONG** — a bug in the extractor | §5.3, §6.3.3 |
| 2 | Langfuse "records structured traces" of the deployed agent | **WRONG** — Langfuse is in the platform, not the agent, and is disabled | §3.1 |
| 3 | "376 conversations contain a customer repeating themselves verbatim" | **WRONG** — units error; the real figure is 163 | §3.2 |
| 4 | The behavioural feedback experiment is "future work" | **WRONG** — it was run, and it returned a null result | §6.4.1, §10.4 |
| 5 | Designed recall is "against the 376 production ground truth failures" | **WRONG** — the denominator is 725 signals (RQ1) / 215 (RQ3) | §6.4.1 |
| 6 | "55 tools" describing the agent | **PARTLY** — the map says 55; the agent has 1 real tool | §5.3, Fig 5.3 |
| 7 | "the same prompts byte for byte" | **PARTLY** — brand rename plus one substantive guardrail drift | §7.5 |
| 8 | "per-batch database resets" | **WRONG** — nothing calls `/reset` | §7.5 |
| 9 | "219 explicit customer request for a human" | **WRONG** — 221 | §3.2 |
| 10 | "over fifty test cases" in the anonymiser suite | **PARTLY** — exactly 50 (now 51) | §4.4 |

---

## 1. The deployed agent (§3.1, §7.5)

### 1.1 LangGraph — CONFIRMED
Genuine `@langchain/langgraph` `StateGraph`, version 1.3.0.

- `WA/graph/builder.ts:8` — `import { END, START, StateGraph, MemorySaver } from "@langchain/langgraph"`
- `WA/graph/builder.ts:142` — `new StateGraph(WhatsAppState)`, compiled at `:186`
- `WA/graph/state.ts:7,35` — `Annotation.Root({...})`
- `tech_repair-live-agent/package.json:12-16`

**Caveat.** It is *not* an LLM tool-calling loop. There is no `bindTools`, no
`DynamicStructuredTool`, no `@langchain/core/tools` import anywhere. Nodes call
plain async functions. "A graph of nodes around a large language model core" is
fair; "an LLM core with a tool catalogue it can call" is not.

### 1.2 The actual state machine — 12 nodes, 21 edges
Rendered from source by `tools/render_langgraph.py` →
`figures/langgraph-state-machine.png`. Extraction is also dumped to
`figures/langgraph-state-machine.json`.

Nodes (`builder.ts:144-157`): `event_detector`, `router`, `status`, `support`,
`contact_info`, `delivery_logistics`, `warranty_answer`, `pricing_answer`,
`memory_extraction`, `escalation`, `human_taken_over`, `response`.

Entry `START → event_detector` (`:160`). Terminal `response → END` (`:184`) —
`response` is the only node with an edge to `END`.

Two conditional routers:
- `routeByIntent` (`builder.ts:56-117`), 8 targets. Order: `humanTakenOver`
  guard → explicit-escalation guard → `switch (state.intent)`.
- `routeAfterSupport` (`builder.ts:123-127`), 2 targets: `GOODBYE →
  memory_extraction`, otherwise `response`.

**`human_taken_over` is unreachable in this build.** `state.humanTakenOver` is
only ever set true by the node itself (`WA/graph/nodes/response.ts:266`), while
every invocation seeds it false (`WA/graph/state.ts:217`; `WA/agent.ts:271-277`
spreads `initialState` into `graph.invoke`). The figure marks it dashed/grey.

**Do not render from the file header.** `builder.ts:5` and `:221-224` still
describe the pre-D5/D6/D7 graph and omit six nodes.

### 1.3 The seven intent branches — PARTLY
All seven named branches exist, but there is an eighth target
(`human_taken_over`) the sentence omits.

**The routing decision is not in `lane-selector.ts`.** That file selects the
*model tier* only — Lane 1 Haiku, Lane 2 Sonnet, one-way upgrade
(`WA/lane-selector.ts:6-11,94`). Intent classification is in
`WA/graph/nodes/router.ts`: regex fast path (`:171-172,309-329`), keyword map
(`:86-164,210`), LLM structured-output fallback (`:241`).

### 1.4 Supabase — CONFIRMED as the client; "catalogue of tools" WRONG
`@supabase/supabase-js ^2.49.0`, injected not constructed
(`server-mirror/shared/supabase.ts:29-56`, header: *"Core NEVER creates database
connections"*). 30 tables reached via `.from(...)`.

But there is exactly **one** tool: `lookupOrder` (`WA/tools/order-lookup.ts:72`),
emitted as `"order_lookup"` (`WA/graph/nodes/status.ts:74,82,108`). A second,
`escalate_to_human`, is fabricated *by the test harness*
(`tech_repair-live-agent/server.ts:70`), not by the agent.

### 1.5 External manufacturer system — PARTLY (present, never called)
GSPN. Constants and endpoint catalogue at
`server-mirror/services/gspn/constants.ts:9-31`; config surface at
`WA/config.ts:30-33`. **No HTTP client for it exists in the mirror** — no
`fetch` to any GSPN endpoint. Data reaches the agent through the
`service_orders` table, populated in production by an out-of-band poller.
`bootstrap.ts:34-36` blanks the credentials. `README.md:147`: "GSPN | never
called at runtime".

### 1.6 Langfuse — WRONG
`grep -rniE "langfuse"` over the whole agent tree returns **zero matches**. No
package, no callback handler, no tracer, dead or otherwise.

The agent's observability is Supabase-backed:
`server-mirror/shared/supabase-logger.ts` (`logAgentThought` → `agent_thoughts`,
`logToolInvocation` → `tool_invocations`), plus `WA/rocket-metrics.ts` and
`shared/llm-tracker.ts` → `rocket_metrics`, `llm_usage`.

Langfuse exists only on the **research platform**, as a read-only *ingester* of
traces:
- `debugger-platforn/src/traces/langfuse_client.py:21,37`
- `debugger-platforn/src/traces/trace_parser.py:189`
- callers: `web/api/routes/phase_a.py:65-74`, `analyze.py:230-243`
- `requirements.txt:24`

It is **env-gated and fails silent**: constructed only if
`LANGFUSE_PUBLIC_KEY`/`LANGFUSE_SECRET_KEY` are set, else logs "trace ingestion
disabled" and `fetch_traces` returns `[]` (`langfuse_client.py:30-49,66-67`). No
`.env` in the repo sets them.

> **Rewrite.** Delete the Langfuse clause from §3.1. If you want to keep it,
> move it to Chapter 5 as a platform capability: *"Phase A can ingest Langfuse
> traces where a deployment provides them; for this agent no trace credentials
> were available, so the behavioural channel was not exercised."* That is also
> consistent with §5.4.3, which already says the trace channel could not be
> exercised.

### 1.7 Guardrail prompts and escalation — CONFIRMED
- `WA/prompts/support.ts:7-98` — 30 numbered rules
- `WA/prompts/status.ts:5-26` — 13 numbered rules
- `WA/post-processors/style-guide.ts` — post-hoc enforcement

Two guardrails are enforced **in code**, which is stronger than the dissertation
implies and worth claiming: the disclosure gate
(`WA/tools/order-lookup.ts:159-211`, strips 12 status fields before the LLM sees
them) and the warranty-contradiction gate (`:252-275`, `delete
result.warranty_type`).

Escalation: `escalationNode` (`WA/graph/nodes/response.ts:215-257`), threshold
`shouldEscalate(state, 3)` (`WA/graph/state.ts:176-181`), marker `[ESCALATE:X]`
(`WA/graph/nodes/support.ts:269,283`). Separately, flag-only escalation
(`WA/events/escalate-event.ts:53,100`) files a task **without** flipping the
conversation.

### 1.8 WhatsApp channel — stubbed in the sandbox
No provider client. No Meta Cloud API call, no `graph.facebook.com`, no
Twilio/360dialog SDK. What survives is Meta webhook **type definitions only**
(`server-mirror/data/types.ts:388-467`) and session-window semantics
(`WA/models.ts:74-84`). The channel is replaced by an HTTP harness
(`tech_repair-live-agent/server.ts:88-129`).

This is *consistent* with §8.1.4's pre-registered "delivery failures are
unreachable" — but §3.1 should say the sandbox has no transport layer, so the
reader meets the fact before Chapter 8 relies on it.

### 1.9 Port :3098 — CONFIRMED
`tech_repair-live-agent/server.ts:23,89`; `debugger-platforn/agent_endpoints.json`.

### 1.10 "Only live dependency is its own LLM calls" — PARTLY
**Two** providers, not one:
- Anthropic primary (`WA/llm-factory.ts:23,34-46`): Haiku lane 1, Sonnet lane 2
  (`WA/config.ts:17-18`)
- OpenAI in two roles: provider failover (`llm-factory.ts:31,52-78`, `gpt-5.2`)
  **and** independent always-on calls — `WA/events/verify.ts:82-85` (header:
  "Always runs (no flag)"), `services/analysis/unified-extraction.ts:223-226`,
  `interaction-grader.ts:258-261`

No other reachable network I/O: the only non-LLM `fetch`
(`services/notifications/push-bridge.ts:95`) is aimed at the unroutable
`http://127.0.0.1:9` by `bootstrap.ts:32`.

### 1.11 "Byte for byte" prompts — PARTLY
Diffed against the production tree. Two kinds of divergence:

1. **Anonymisation rename** — every prompt file carries the brand substitution
   from the 2026-07-29 sweep. Byte-for-byte is definitionally false for the
   published artefact.
2. **Substantive guardrail drift** — the mirror is missing production commit
   `67af5ec49` (2026-07-22, *"la IA nunca afirma cobertura de garantía"*).
   `status.ts` rule 7 and `support.ts` rule 16 differ in content, and
   `WA/agent.ts` lacks the whole warranty-flag fallback block (−54/+4).

The mirror is a snapshot **behind** production on precisely the warranty
guardrail — which is also the guardrail the seed data is built to exercise.

> **Rewrite.** "…the same prompts modulo the anonymisation rename, and the same
> LangGraph structure and guardrails as of the snapshot date; the sandbox
> predates one later production revision of the warranty guardrail."

Also: `tech_repair-live-agent/README.md:62` asserts "Prompts are byte-identical
to production" — stale, update alongside.

### 1.12 Seed data — CONFIRMED in full
`fake-db/seed.ts`: Valeria Mendoza García (`:22-31`); exactly two orders
(`:52-126`) — `4151234567` d2d `warranty_type "O"`, `4149876543` carry_in
`warranty_type "I"`; disclosure gate at `:204`
(`proactive_status_disclosure: false`), enforced at
`WA/tools/order-lookup.ts:159-166,174-185`.

### 1.13 "Per test session isolation and per-batch database resets" — HALF WRONG
Session isolation **CONFIRMED**: `src/execution/agent_connector.py:273-274`
(fresh UUID per conversation), consumed at
`src/execution/conversation_simulator.py:118`; server keeps a per-session map
(`server.ts:25-35`) used as the LangGraph `thread_id`.

Per-batch reset **NOT IMPLEMENTED**. `POST /reset` exists
(`server.ts:120-125`) but **nothing in the platform ever calls it**. The
project's own docs concede it: `docs/TECH_REPAIR_LIVE_SIMULATION.md:225-227` —
*"Fake-DB state accumulates across tests within a run… per-test isolation would
need a reset hook in the connector (future work)."*

> **Rewrite.** "Per-session isolation, with a manual database reset between
> batches. Fake-database writes accumulate across tests within a batch, which is
> a limitation: the escalation deduplication is keyed on conversation id, so
> accumulation can affect downstream behaviour."

---

## 2. The "lang fields" question — the English-guardrail finding is a bug

You asked specifically whether the language fields make sense. **They do not, and
I fixed the cause.**

The shipped map contradicts itself, 40 lines apart, in
`pipeline_output/session-636fc721/agent_map.json`:

| field | value |
|---|---|
| `guardrails.guardrail_language` | `"English"` |
| `guardrails.guardrail_language_matches_conversation` | `false` |
| `metadata.language.guardrail_language` | `"Spanish"` |
| `metadata.language.language_mismatch` | `false` |

**The code ground truth is Spanish.** `WA/prompts/support.ts:7-98` (30 rules)
and `WA/prompts/status.ts:5-26` (13 rules) are entirely Spanish. Only
`WA/prompts/router.ts:5-27` and `WA/context-summarizer.ts:11` are English, and
neither is a guardrail — one is a classifier, the other a one-line utility.

**Root cause** — `src/patterns/rule_extractor.py:201-204` (before fix):

```python
def _detect_rule_language(text: str) -> str:
    spanish_hits = sum(1 for kw in _SPANISH_INDICATORS if kw in lower)
    return "Spanish" if spanish_hits >= 2 else "English"
```

It required **two** hits from a twelve-word list inside a *single short rule*.
`"NUNCA determines garantía por tu cuenta"` scores one and falls through to the
English default. Measured on the real map: **40 of 79 rules misclassified**, and
the majority vote inverted.

**Fixed.** The detector now scores Spanish against English symmetrically, adds
the shared `config/framework_signatures` word lists, and weights Spanish-only
orthography (`¿¡ñáéíóú`), which is decisive for short rules.

| | Spanish | English | misclassified |
|---|---|---|---|
| ground truth | 57 | 22 | — |
| before | 17 | 62 | **40 / 79** |
| after | 63 | 16 | **6 / 79** |

Majority verdict flips **English → Spanish**, matching the code.

Regression tests: `tests/phase_a/unit/test_rule_extractor.py::TestRuleLanguageDetection`.

> **What to change in the writing.** The claim that the agent has *"English
> guardrails governing Spanish conversations, a mismatch Phase B later exploits
> on purpose"* (§5.3) must go, and with it the §6.3.3 sentence about generating
> code-switched provocations against that mismatch.
>
> **You do not lose the paragraph — you gain a better one.** The metamorphic
> language-invariance machinery still exists and is still justified (§6.3.3,
> [26,49]); it simply is not motivated by a detected mismatch. And the episode
> is a genuine Phase A finding worth reporting: *two independent language
> detectors in the same artefact disagreed, and the one that fed the headline
> claim was wrong. The map is configuration, not documentation — §5.5 already
> makes exactly this argument about terminal outcomes, and this is a second,
> independent instance of it.*
>
> A stronger replacement finding is available in the same prompt file: the
> runtime-appended `MEMORY_RULES` block (`WA/prompts/support.ts:101-111`,
> appended at `:146-149`, enabled by `fake-db/seed.ts:227`) **renumbers from 26
> and collides with existing rules 26–32** in the base prompt. Two different
> rule 26s, 27s, 28s, 29s and 30s reach the model in the same system prompt.
> That is a real prompt-engineering defect that Phase A's extractor missed
> entirely, and it is a much better illustration of why a structural map of an
> agent's guardrails is worth building.

---

## 3. Chapter 3 numbers — re-derived from the corpus

Recomputed with the project's own scorer
(`src/production/scoring.py`, `ground_truth.build_ground_truth(min_score=3.0)`)
against `investigation/02_data/real/tech_repair-conversations-anonymized.json`.
Regenerate with `tools/render_chapter3_figures.py`.

### §3.4 — reproduces perfectly. All nine numbers, exactly.

| claim | actual | |
|---|---|---|
| 376 failures / 1,299 (28.9%) | 376 / 1,299 (28.94%) | ✅ |
| loop_stall 256 (68.1%) | 256 (68.09%) | ✅ |
| resolution 221 (58.8%) | 221 (58.78%) | ✅ |
| comprehension 153 (40.7%) | 153 (40.69%) | ✅ |
| data_gap 48 (12.8%) | 48 (12.77%) | ✅ |
| delivery_infra 14 (3.7%) | 14 (3.72%) | ✅ |
| hallucination 13 (3.5%) | 13 (3.46%) | ✅ |
| missed_escalation 11 (2.9%) | 11 (2.93%) | ✅ |
| silent_abandonment 9 (2.4%) | 9 (2.39%) | ✅ |

### §3.2 — two errors

| claim | actual | |
|---|---|---|
| 1,299 conversations | 1,299 | ✅ |
| 24,537 messages | 24,537 | ✅ |
| 291 escalated (22.4%) | 291 (22.40%) | ✅ |
| **219 explicit request for a human** | **221** | ❌ |
| 297 unknown-intent | 297 | ✅ |
| 287 past forty messages | 287 | ✅ (see caveat) |
| 239 failed deliveries | 239 messages, over 114 conversations | ✅ |
| **376 conversations repeating verbatim** | **163** | ❌ |

**219 → 221.** The scorer's `requested_human` signal (`scoring.py:131-137`) is a
two-stage OR: `escalation_reason` match (218) plus customer-text match (+3) =
**221**. This is definitionally the same set as §3.4's `resolution` count of 221
(`resolution` fires iff `requested_human`, `scoring.py:219`), so as written §3.2
and §3.4 disagree about one set. 219 is not producible by any variant; it is
inherited from `docs/Agent_Failure_Plan.md:52`, a 2026-06-28 live-DB snapshot
that drifted by 2 relative to the export.

**The 376 repeaters is a units error — and it dissolves the "coincidence".**
`docs/Agent_Failure_Plan.md:52` reads `| Customer repeated themselves | 376
times |` and `:89` `- Customer repeats the same message (376 occurrences)`. That
is an **occurrence** count from a live-DB query. §3.2 reinterpreted "376 times"
as "376 conversations."

The conversation count under the scorer's own definition
(`scoring.py:157-162`, adjacent customer messages identical after
lowercase/accent-strip) is **163**. I swept 16 alternative definitions; none
yields 376. The closest is "any duplicate customer text anywhere" = 369, but
that is not the signal the scorer consumes.

Set relationship (R = 163 repeaters, F = 376 failures) — plotted in
`figures/failure-signal-overlap.png`:

| | |
|---|---|
| R ∩ F | 116 |
| R \ F | 47 |
| F \ R | 260 |
| **Jaccard** | **0.274** |

> **Rewrite.** Replace the bullet with *"163 conversations contain a customer
> repeating themselves verbatim, the scorer's reachable comprehension signal."*
> Then **delete the whole parenthetical about the numerical coincidence** — there
> is no second 376 to coincide with, so the hedge now creates a problem instead
> of defusing one.
>
> This strengthens §9.2. Your argument there is that production shows verbatim
> repetition routinely while simulation produced zero in 2,950 conversations.
> 163/1,299 = 12.6% against 0/2,950 is still decisive, and it no longer rests on
> a number that collides with the failure count.

**Caveat worth a footnote.** `>40 messages` reads `conv["message_count"]`, a
database counter, not `len(conv["messages"])`. They disagree: 36,207 vs 24,537
summed. Under the counter, 287 (as claimed); under the exported transcript, 167.
Say "conversations whose stored `message_count` exceeds forty". A viva examiner
will find this.

**Also qualify §9.2's opening.** *"The scorer's reachable comprehension signal is
verbatim customer self-repetition"* reads as a claim about the scorer in general,
which the data contradicts: `comprehension` fires on an OR of three conditions
(`scoring.py:206-210`), and only 52 of 153 comprehension failures involve
repetition at all. Suggested: *"The only comprehension signal reachable in
simulation is verbatim customer self-repetition; the other two triggers
(unknown-intent telemetry, sub-0.5 confidence) are production-only fields that
simulated runs never populate."*

---

## 4. The production feedback path (§6.4, §6.4.1, §10.4)

### 4.1 It exists, but it is not a loop
`src/feedback/loop.py` (283 lines):
`production_failure_to_seed` (`:89-130`), `build_feedback_corpus` (`:138-173`),
`generate_blind_suite` (`:192-209`), `generate_feedback_suite` (`:212-258`),
`verify_no_leakage` (`:266-282`). Seed→scenario at
`src/scenarios/seed_corpus.py:491`.

The only production caller is `src/experiments/runner.py:263,269`. The flow is a
single linear pass:

```
export → build_ground_truth → time_split → train failures
  → build_feedback_corpus → generate_feedback_suite
  → _static_failures_per_test (reads test design, no execution)
  → recall → STOP
```

Nothing reads execution outcomes back into generation. No iteration variable, no
round counter, no re-generation in `run_experiment` (`runner.py:197-427`).

The module docstring over-claims: `loop.py:1-8` says *"the generator is re-run
at the same budget"* — that is two independent invocations, not two iterations.

> **Rewrite.** Call it **feedback-seeded generation**, not a loop, throughout
> §6.4. The mechanism is real and the framing of §2.9 ("that gap is opened here
> rather than closed") is already honest — but the word "loop" in §6.4 and the
> figure of a cycle promise a closure the code does not implement.

### 4.2 It WAS executed — and the result was null
This is the most important correction in this document.

`experiments_output/anonymized_execute/`:
- `generated_at 2026-07-14T10:53:31`, `config.mode "execute"`,
  `connector http://localhost:8099` (the sandbox bridge), `budget 40`
- `work/blind/traces/` — 40 trace JSONs; `work/feedback/traces/` — 40
- `REPORT.md:79-88`:

```
| Arm      | Held-out recall | 95% CI      | Precision |
| blind    | 0.121           | 0.079–0.167 | 1.000     |
| feedback | 0.121           | 0.079–0.167 | 1.000     |

**feedback_vs_blind**: Δrecall = +0.000, p = 1.0000
(not significant; 0 discordant signals)
```

`n_discordant: 0` — when actually run, the two arms covered *exactly the same
set* of held-out signals.

> **This must be reported.** §6.4.1 says "The behavioural form of this
> comparison… is the future experiment of Chapter 10", and §10.4 item 3 costs it
> as unrun. A behavioural form *was* run, at budget 40 through the bridge, and it
> showed no lift.
>
> Reporting it costs you very little and protects you completely. The run used
> the superseded sandbox bridge (§7.6: "cannot intercept upstream tool
> execution", fidelity anchor 0.36), not the verbatim sandbox, and at budget 40
> against 215 held-out signals it is underpowered. So the honest sentence is:
> *"A pilot behavioural comparison was run at budget 40 through the earlier
> sandbox bridge and found no difference between the arms (Δ = 0.000, p = 1.0).
> The bridge's fidelity limits and the small budget make it uninformative rather
> than contradictory, which is precisely why the arm-and-context experiment is
> specified against the verbatim sandbox at N = 200 per cell."*
>
> Leaving it out is the version that damages you, because the artefacts are in
> the repository you are shipping.

### 4.3 The 0.112 → 0.312 delta is arithmetically forced
Values confirmed: `experiments_output/rq4_full/results.json` (and
`anonymized_static/`), `mode: "static"`, seed 42, budget 100, 2026-07-14.
`blind.recall 0.1116`, `feedback.recall 0.3116`.

But the metric reduces to a set-union over category labels. Every synthetic
signature has `tool_involved = None`, so `_matches`
(`src/evaluation/predictive_validity.py:56-64`) can only match signals whose
conversation logged no tools (67 of 215 holdout signals). Then:

- blind label set covers `{infinite_loop, hallucination, escalation_failure}`
  → 19+3+2 = **24 → 24/215 = 0.1116** ✅
- feedback adds `{resolution_failure, comprehension_failure, delivery_failure,
  data_gap}` → **67/215 = 0.3116** ✅

The feedback arm's label set is a **strict superset** of the blind arm's.
`n_discordant = 43` is exactly the 43 signals added by the four extra labels, so
the sign-flip permutation test cannot fail to return p ≈ 1/(n+1) = 0.0001. **The
significance test is vacuous** — it tests whether a superset covers at least as
much as its subset.

Related: 4 of the 10 rows in `sensitivity_main/sensitivity.json` vary only
`rng_seed` and are bit-identical, because the static metric is seed-invariant by
construction. "Robust in 10/10" rests on 6 distinct configurations.

> **Rewrite.** Report the delta as what it is: *"seeding adds four production
> failure categories to the suite's declared detection targets, raising designed
> recall from 0.112 to 0.312. Because the seeded arm's label set is a superset
> of the blind arm's, the direction of this result is guaranteed by
> construction; the informative content is the size of the addition and which
> categories it adds, not the accompanying significance test."* Then drop the
> p-value.

### 4.4 The denominator is wrong
§6.4.1 says recall is computed "against the 376 production ground truth
failures", and §1.4 describes it as "the share of production failure categories".
Neither is right. `to_production_signals`
(`src/production/ground_truth.py:163-195`) emits one signal per
(conversation, shared-category) pair → **725 signals**; RQ3 uses the 215 held-out
ones. (Check: 14+9+153+256+221+13+48+11 = 725.)

> **Rewrite.** "…computes recall against the 725 production failure signals —
> one per conversation-category pair across the 376 failures — of which 215 form
> the held-out split used for the arm comparison."

### 4.5 The 0.068 framing is wrong twice
1. Not "the first static campaign". The first is `smoke_static/`
   (`10:43:22`), on the **un-anonymised** export, recall **0.0689**. The 0.0676
   figure is from `anonymized_static/` five minutes later.
2. **0.068 and 0.112 are the same suite against different denominators**, not a
   progression: 49/725 (RQ1, all signals) vs 24/215 (RQ3, held-out). The blind
   arm is identical in both.

> **Rewrite.** Replace the §6.4.1 "two blind figures" paragraph: *"0.0676 and
> 0.112 are the same blind suite measured against different denominators — all
> 725 production signals, and the 215 held-out ones used for the arm comparison.
> They are not successive measurements, and only the second is comparable with
> the 0.312 feedback arm."*

### 4.6 "Ship in the investigation package" — FALSE
`investigation/` contains no `suite_blind.json`, no `suite_feedback.json`, no
`results.json`, no RQ3 per-category breakdown. It holds only the real-vs-sim and
scale-study material. The arm artefacts are at
`debugger-platforn/experiments_output/rq4_full/`. Either move them or correct the
sentence.

---

## 5. The split-half noise floor (§8.1.5) — CONFIRMED exactly

`compare_real_vs_sim.py:204-227`, `split_half_noise_floor(...)`.

| property | value |
|---|---|
| splits | **200** (`n_iter=200`, never overridden) |
| method | `rng.shuffle(pool)` then `pool[:half]` / `pool[half:]` — **disjoint partition, no replacement** (not a bootstrap) |
| unit | all **1,299 conversations**; only the ~188 failures per half contribute to the distributions |
| seed | **42**, local `random.Random(42)` (`:213`), global RNG untouched |
| support | same 7-category reachable support, literally the same list object (`:288-296`) |
| output | `mean 0.0050093809`, `p95 0.0107644` |

Independently reproduced bit-for-bit. **0.0050 / 0.0108 confirmed.**

Two harmless implementation notes: `half = 1299 // 2` gives 649/650; and
`p95 = samples[int(0.95*200)-1] = samples[189]` is the ~94.75th percentile.

**Bootstrap CI** (`:176-201`): 1,000 resamples, **whole conversation records with
replacement**, each corpus to its own size — the dissertation's "at the level of
whole conversations" is **correct**. Seed 42. Point estimate on original data.
Note `scale_curves.py:59` overrides to `n_iter=500` for the scale curves; §8.3
should say so.

**Uniform anchor 0.2014** (`:294-297`): confirmed, deterministic, no CI.

> **One thing to add, and it helps you.** The floor is computed on ~650-vs-650
> conversations, but the headline compares 1,299 real against 390 simulated. A
> size-matched floor is fairer. I recomputed:
>
> | variant | mean | p95 |
> |---|---|---|
> | as shipped | 0.0050 | 0.0108 |
> | conversation-size-matched (390 vs 909) | 0.0058 | 0.0121 |
> | failure-count-matched (82 vs 294) | 0.0081 | 0.0170 |
>
> The floor rises but stays an order of magnitude below 0.2392. State this in
> §8.1.5 — it converts an unexamined assumption into a robustness check.

**Not a correction, but fix the code comment.** `compare_real_vs_sim.py:332`
calls the uniform baseline an "upper anchor", which is backwards given the
measured 0.2392 > 0.2014. §8.2.4 handles this correctly and confronts it
head-on; the code note contradicts the dissertation and should be updated.

---

## 6. Phase A map numbers (§5.3, Fig 5.3)

All four reproduce from `pipeline_output/session-636fc721/agent_map.json`:
55 tools, 9 prompts, 54 files, 34 risks. **As map values they are CONFIRMED. As
descriptions of the agent they mislead.**

- **55 "tools" → 1 real tool.** The 55 are ordinary TypeScript functions
  harvested by static analysis: `routeByIntent`, `buildGraph`, `getCheckpointer`,
  `truncateResponse`, plus **test helpers and assertions** (`makeSO`, `baseState`,
  `assertNoHedgeWords`) — `analyzed_files` includes 12 `__tests__/` files. The
  project already documents the consequence:
  `docs/TECH_REPAIR_LIVE_SIMULATION.md:219-221` explains Phase C's "Tool coverage
  0%" this way.
- **9 prompts** counts one **deprecated** file
  (`WA/prompts/memory-extraction.ts:1-11`, marked "no longer used") and misses
  the runtime-appended `MEMORY_RULES` (`WA/prompts/support.ts:101-111`).
- **54 files** is the production tree including tests; the sandbox `WA/` tree has
  32 `.ts` files.

> **Rewrite.** Keep the numbers — they are the map's real output and Fig 5.3 is
> honest as "what Phase A extracted". Add one sentence: *"The catalogue is a
> static-analysis inventory of callable functions, not a runtime tool registry:
> the agent exposes a single backend tool, `order_lookup`, and the remaining
> entries are internal functions and test helpers. This is why Phase C reports
> zero tool coverage against the live agent, and it is the same map-is-not-
> documentation lesson as §5.5."* That turns a soft number into a finding.

---

## 7. Smaller items

| § | Claim | Verdict |
|---|---|---|
| §4.4 | "over fifty test cases" | Exactly **50**, now **51** with the regression test I added. Say "fifty-one". |
| §4.3 | spaCy "wrapped by Microsoft Presidio" | CONFIRMED — `presidio_analyzer` only; `presidio_anonymizer` is not used and not installed. |
| §4.3 | three-pass pipeline, shared `PlaceholderTracker` | CONFIRMED — `backend/pipeline.py`, `config.py:96-109`. Verified live: a phone repeated twice both became `[PHONE_1]`. |
| §7.2.2 | mock / API / partner connectors | CONFIRMED — `src/execution/agent_connector.py`. |
| §7.2.1 | "execution entry points make that choice explicit rather than defaulting silently" | Was **WRONG** for scripted runs (interactive `input()` only; EOF → silently "no"). **Fixed** — see §8 below. Now true. |
| §8.1.1 | 390 = 40 + 150 + 200 | CONFIRMED as a sum. |
| Fig 5.1/5.4/6.1/7.2 | UI screenshots | Not verifiable from code; the platform runs and reproduces these views. |

---

## 8. Defects found and fixed

| # | Defect | Fix | Test |
|---|---|---|---|
| 1 | ADDRESS regex used `\s`, matching newlines, so a line-final address swallowed the next `Agente:` turn label — violating §4.4's stated preservation guarantee | Horizontal whitespace only (`[^\S\n]`, `[ \t]`) | `test_regex_pass.py::test_address_does_not_cross_newline` |
| 2 | `_detect_rule_language` mislabelled 40/79 guardrails, inverting the map's language verdict | Symmetric Spanish-vs-English scoring + Spanish orthography weighting | `test_rule_extractor.py::TestRuleLanguageDetection` (10 cases) |
| 3 | `anonymize_export.py` silently degraded to regex-only redaction if the NER backend was missing — the ethical gate could fail open | Fail closed by default; `--allow-fallback` to opt out explicitly | verified manually |
| 4 | Phase C persona context was interactive-only; scripted runs hit EOF and silently ran without it, so the dissertation's configuration could not be reproduced from the CLI | `--persona-context`, `--persona-context-file PATH`, `--no-persona-context`; hard error on non-TTY with no choice | `test_pipeline.py` updated |
| 5 | Platform venv could not import the anonymisation backend, so `get_anonymiser()` returned `regex_fallback` | Installed `spacy`, `presidio-analyzer`, `es_core_news_lg` into the platform venv; now returns `full` | verified |

**Not fixed, flagged only** (they change shipped results, so they are yours to decide):
- Defect 1 also affected the corpus run, but only *within* message bodies —
  the export anonymises per field, so JSON turn structure was never at risk, and
  over-anonymisation is the documented preferred failure mode. The shipped corpus
  records `"anonymisation": {"pipeline": "full"}` with zero fallback markers, and
  contains `PERSON`/`LOCATION`/`BRAND` placeholders proving all three passes ran.
  **No re-anonymisation needed.**
- The `MEMORY_RULES` rule-number collision in `WA/prompts/support.ts` is a real
  defect in the agent under test. Fixing it would change agent behaviour and
  invalidate the comparison corpus. Report it; do not fix it.
