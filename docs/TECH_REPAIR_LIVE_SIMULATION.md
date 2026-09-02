# TechRepair Live Simulation — What Was Built and Where Everything Lives

**Written 2026-07-24.** Companion to `PROJECT_STATUS.md` (overall project
state) and `phase-c-enhancements/CONTEXT.md` (the gap analysis that motivated
this work). This document covers the work of 2026-07-23/24: the **living
TechRepair agent simulation**, the **Phase B suite generated for it**, the
**first execute-mode Phase C runs**, and where every artifact is stored.

---

## 1. What was built, in one paragraph

The real TechRepair/Pulpoo WhatsApp agent was copied **verbatim** out of
`pulpoo-final` into a new self-contained project, `tech_repair-live-agent/`,
where it runs against a **fake in-memory database** seeded with one fully
specified fake customer — no connection whatsoever to TechRepair systems,
Supabase, GSPN, or Meta. Phase B then generated a 40-test Spanish suite from
the TechRepair agent map, and Phase C executed that suite against the living
agent over HTTP — producing the project's first **execute-mode** (not
static-mode) results, including a live demonstration of the oracle gap
documented in `phase-c-enhancements/CONTEXT.md` §4.2. This is sprint **X3**
("real-agent execute mode") of the Phase C enhancement programme.

Everything is committed on `main` (commits `78d7f29` → `80bd7ca`).

---

## 2. The living agent — `tech_repair-live-agent/`

### 2.1 Design principle

pulpoo-final's core never creates DB connections — the app *injects* a
Supabase client at bootstrap ("Core defines WHAT, App provides HOW"). The
simulation exploits exactly that seam: **the agent code is unchanged**
(prompts byte-identical, same LangGraph, same guardrails); only the injected
client is fake. The agent cannot tell it isn't in production. The only real
outbound traffic is the agent's own LLM calls (Anthropic Haiku/Sonnet lanes,
OpenAI escalation verifier), which is what makes it a *living* test target.

### 2.2 Layout

| Path | What it is |
|---|---|
| `tech_repair-live-agent/server.ts` | HTTP harness: `POST /chat` (Phase C contract), `GET /db` (inspect fake DB), `POST /reset` (fresh DB between runs), `GET /health` |
| `tech_repair-live-agent/index.ts` | Interactive CLI chat (`bun run cli`) |
| `tech_repair-live-agent/bootstrap.ts` | Plays pulpoo's "App" role: injects the fake Supabase client + app id, pins env so nothing reaches real infra |
| `tech_repair-live-agent/context-builder.ts` | Builds the `AssembledContext` the agent expects (the gateway's job in production), sourced from the fake DB |
| `tech_repair-live-agent/fake-db/fake-supabase.ts` | In-memory Supabase-compatible query builder (filters, `.or()`, JSON paths, upserts, 3 Postgres RPCs). Records every mutation in a `mutationLog` |
| `tech_repair-live-agent/fake-db/seed.ts` | All tables + THE fake customer (below) |
| `tech_repair-live-agent/server-mirror/` | Mirrors pulpoo's `server/` layout; tsconfig maps `@/*` here. Contains the **entire WhatsApp agent verbatim** (`services/agents/whatsapp/` — prompts, graph, 12 nodes, event detectors, order-lookup tool, style guide) plus ~46 support modules copied verbatim |
| `tech_repair-live-agent/README.md` | Full run instructions, fake-vs-real boundary table, verified behaviors |

Only **5 modules are fake shims** (each headed "FAKE SHIM"): semantic-memory
(mem0), survey-orchestrator, dynamic-config (LiveKit TTS trimmed), and two
type-only stubs (greeter-agent, context-assembler). Six `// [sim]`-marked
**type-only** patches fix pre-existing upstream tsc errors; zero behavior
changes. `bun run typecheck` is clean.

### 2.3 The fake customer

**Valeria Mendoza García** — phone `5215587654321`, customer `CUST-0084213`,
preferred name "Vale", 6 prior interactions, frustration index 2.4.

| Order | Device | Pipeline | Warranty | Status | Why it exists |
|---|---|---|---|---|---|
| `4151234567` | Galaxy S24 Ultra 256GB | D2D (home delivery) | Out of warranty (O) | ST030 awaiting parts, quote **$3,480 MXN** | status / pricing / delivery / payment flows; warranty-strip gate |
| `4149876543` | Galaxy Watch6 44mm | Carry-in (store) | In warranty (I) | ST040 → `ready_for_pickup` | **the disclosure gate** — production policy forbids revealing status (customer is at the store door) |

Also seeded: the verbatim production `service_status_policy` rows
(migrations 0057+0059), an active call-frequency escalation rule, interaction
history, CRM memory. Media turns (payment receipts) are simulated with the
same markers the production media pipeline uses: send `[COMPROBANTE] ...`
(or `"message_type": "image"`).

### 2.4 Running it

```bash
cd tech_repair-live-agent
bun install                 # once; versions pinned in bun.lock
bun run api                 # → http://localhost:3098  (.env needs ANTHROPIC_API_KEY + OPENAI_API_KEY)
bun run cli                 # interactive chat instead of HTTP
```

### 2.5 Verified behaviors (smoke-tested by hand)

Greeting personalization from CRM memory; `order_lookup` with real IQC-code
enrichment; **disclosure gate** stripping repair status on the carry-in order
(with `agent_thoughts` audit row); **warranty-contradiction gate** stripping
`warranty_type`; pricing disambiguation → the $3,480 quote;
`explicit_human_request` escalation; payment-receipt and address-change
detectors filing `escalated_tasks` rows; goodbye → memory extraction
persisting facts + CRM snapshot.

---

## 3. Phase B — the generated TechRepair suite

### 3.1 Where it is

**`debugger-platforn/generated_tech_repair/`** (committed; the platform's
blanket `*.json` gitignore means regenerated files need `git add -f`):

| File | Contents |
|---|---|
| `test_suite.json` | **40 executable test cases** (persona + scenario + oracles) — the input to Phase C |
| `persona_library.json` | AI-generated Spanish personas (MAP-Elites) |
| `scenario_catalog.json.gz` | Full catalog: 1,480 scenarios incl. variants + oracles. 95MB raw → stored gzipped (9.4MB); `gunzip -k` to restore |
| `test_configuration.json` | Phase B run configuration |
| `evaluation_report.json` | Suite-quality harness output |
| `README.md` | Provenance + exact regeneration command |

### 3.2 How it was produced

```bash
python generate_tests.py tech_repair_whatsapp_map.json -o generated_tech_repair \
    --count 40 --seed 42 -l Spanish --evaluate
```

Run stats: 863,010 tokens, ≈$2.68, ≈3h. (First attempt crashed on missing
`numpy` in the venv — now installed.)

### 3.3 Suite quality (evaluation harness)

APFD **0.9168** (weighted 0.9202) · 214 potential faults · overall diversity
0.3112 · tool-pair coverage 0.3279 · taxonomy coverage **0.6875** ·
194 mutants.

---

## 4. Phase C — executing the suite against the living agent

### 4.1 How the connection works

1. `tech_repair-live-agent` exposes `POST /chat` — the exact
   `APIAgentConnector` contract: `{message, session_id}` →
   `{response, tool_calls}`. Each test's `session_id` becomes the agent's
   LangGraph thread, so multi-turn state behaves like production.
2. `debugger-platforn/agent_endpoints.json` resolves the TechRepair map to
   `http://localhost:3098` automatically (and
   `tech_repair_whatsapp_map_live.json` also carries `api_endpoint` directly).
3. Run Phase C **without `--mock`**:

```bash
# terminal 1
cd tech_repair-live-agent && bun run api
# terminal 2
cd debugger-platforn && source venv/bin/activate
python execute_tests.py generated_tech_repair/test_suite.json \
    tech_repair_whatsapp_map_live.json --count 40 --workers 2 -o results \
    --persona-context
```

> **Always use `tech_repair_whatsapp_map_live.json` for execution.** The
> pristine research map (`tech_repair_whatsapp_map.json`) has zero terminal
> outcomes and static-analysis tool names — every run against it scores 0
> regardless of agent behavior. Keep it untouched for the research arms.

### 4.2 The two recorded runs — and what they prove

| Run | Map used | Result | Where |
|---|---|---|---|
| **v1** | `tech_repair_whatsapp_map.json` (research map) | **0/10, all vacuous** ("max turns" / "persona gave up"), 0% tool coverage, avg 82.6s/test | `debugger-platforn/results_tech_repair_live/` |
| **v2** | `tech_repair_whatsapp_map_live.json` | **9/10 pass**: 7× `order_status_provided`, 2× `escalated_to_human`, 1 genuine `user_abandoned` failure; avg 19.1s/test | `debugger-platforn/results_tech_repair_live_v2/` |

Each results folder contains `test_run_report.json`, `failure_inbox.json`,
`conversations.log`, and per-conversation `traces/*.json` (full Spanish
persona↔agent dialogues).

**Why v1 scored zero (the oracle-gap evidence).** Three stacked causes, all
now demonstrated rather than argued:

1. The research map has **0 terminal outcomes / 0 tool chains** (it predates
   the Phase A code-tree upgrade — PROJECT_STATUS §6.3), so verdict tiers
   1–2 could never fire.
2. The suite's `required_tools` are **static-analysis function names**
   (`routeByIntent`, `statusNode`, …) while the running agent reports its
   actual runtime tool (`order_lookup`) — tier 3 and tool coverage can never
   match.
3. Tool calls lacked the `result.status == "ok"` field the oracle reads, so
   even called-and-succeeded tools were invisible.

**Fixes (harness only — the verbatim agent was not touched):**

- `tech_repair-live-agent/server.ts` now mirrors each `tool_output` into
  `result: {status: "ok"|"error"}` and emits a synthetic
  `escalate_to_human` tool call when the agent escalates.
- `tech_repair_whatsapp_map_live.json` = copy of the research map + runtime
  terminal outcomes (`order_status_provided`, `escalated_to_human`),
  Spanish confirmation phrases, and the api_endpoint.

**Dissertation-ready observation from v2:** with tool-signature outcomes
only, 8/8 *hard* tests (including attack scenarios) "passed" because the
oracle cannot see semantic failures — verbosity, non-compliance, successful
manipulation. That is the concrete, quantified motivation for sprints X1
(oracle evaluation) and X2 (behavioral detectors), and belongs in the
threats-to-validity discussion alongside the v1/v2 contrast.

---

## 5. Quick file finder

| I want… | Look in |
|---|---|
| The living agent + how to run it | `tech_repair-live-agent/README.md` |
| The fake customer's data | `tech_repair-live-agent/fake-db/seed.ts` |
| The verbatim prompts | `tech_repair-live-agent/server-mirror/services/agents/whatsapp/prompts/` |
| Phase B suite + quality report | `debugger-platforn/generated_tech_repair/` |
| Execution map (use this one) | `debugger-platforn/tech_repair_whatsapp_map_live.json` |
| Research map (keep pristine) | `debugger-platforn/tech_repair_whatsapp_map.json` |
| Endpoint wiring | `debugger-platforn/agent_endpoints.json` |
| Oracle-gap evidence run (0/10) | `debugger-platforn/results_tech_repair_live/` |
| Working run (9/10) | `debugger-platforn/results_tech_repair_live_v2/` |
| Phase C gap analysis / sprint plan | `phase-c-enhancements/CONTEXT.md` |
| What a conversation did to the "backend" | `GET http://localhost:3098/db` while the agent is running |

## 6. Known caveats

- The interaction grader's OpenAI structured-output call warns about zod
  `.optional()` fields and fails safe (upstream behavior, non-fatal).
- Phase C's "Tool coverage 0%" against the live agent is expected for now:
  the metric counts the research map's 55 static-analysis tool names, which
  the runtime `/chat` contract never reports.
- `@langchain/core` is pinned to 1.2.3 (not pulpoo's 1.1.46) because
  langgraph under bun needs its `uuid.v6` export; all other deps match
  pulpoo's lockfile.
- Fake-DB state accumulates across tests within a run (sessions are
  isolated, the DB is shared). `POST /reset` between runs; per-test isolation
  would need a reset hook in the connector (future work).
