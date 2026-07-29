# FULL PROJECT CONTEXT — read this first

**Written 2026-07-24 (end of day). Supersedes `PROJECT_STATUS.md` (2026-07-14)
and `TECH_REPAIR_LIVE_SIMULATION.md` (2026-07-24 morning) as the single catch-up
document.** Give this file to any new working session (human or AI) — it says
what the project is, what exists, what the results are, every gotcha, and what
remains.

---

## 1. The project in four sentences

The dissertation (**"Closing the Loop Between Synthetic Agent Testing and
Production Reality"**, Eduardo Fernandez Salazar, Imperial MSc AI) asks whether
synthetic adversarial testing of a conversational agent predicts the failures
that occur in real production, and whether feeding production failures back
into test generation improves prediction. The testbed is (a) an agent-testing
platform (`debugger-platforn/`: Phases A–E + web UI), (b) 1,299 real anonymised
Spanish WhatsApp conversations from the deployed TechRepair/Pulpoo support agent,
and (c) a **verbatim copy of that production agent** running against a fake DB
(`tech_repair-live-agent/`). As of 2026-07-24 the loop is closed behaviourally:
simulated conversations against the live agent are compared to real failures
under an **identical rule-based scorer**, with a 7-batch scale study
(N=10…1000, 2,560 conversations). Headline: **simulation reproduces 5/7
reachable real failure categories, saturating at N≈50 — the misses are
structural (persona over-cooperativity, too-perfect fixtures), not
budget-limited.**

## 2. Repo map (`MSC_AI_Project/`)

| Path | What |
|---|---|
| `debugger-platforn/` | The platform. Phases: A analyze code→agent_map; B generate personas/scenarios/tests; C execute (this is "Fase C"); D diagnose; E improve. Web UI: FastAPI (`web/api`, system python3) + React (`web/frontend`, vite/bun). CLI entry points: `analyze.py`, `generate_tests.py`, `execute_tests.py`, `run_pipeline.py`, `diagnose_failures.py`. |
| `tech_repair-live-agent/` | Verbatim pulpoo WhatsApp agent + in-memory fake Supabase. `bun run api` → **:3098** (`POST /chat`, `GET /db`, `POST /reset`, `GET /health`). Needs `.env` with ANTHROPIC_API_KEY + OPENAI_API_KEY. Agent code untouched; 5 fake shims; 6 type-only `// [sim]` patches. |
| `docs/` | All docs + the real corpus. `tech_repair-conversations-export.json` = **RAW, contains PII, tracked in git history — never push public**. `tech_repair-conversations-anonymized.json` = the corpus every experiment uses. `docs/results/` = archived experiment outputs. |
| `investigation/` | **Self-contained package** of the real-vs-sim study: methodology, all data (real + every sim corpus), scripts, results, and the LaTeX report (`05_report/report.tex` → `report.pdf`, compile with `tectonic report.tex` — tectonic installed via brew 2026-07-24). |
| `phase-c-enhancements/CONTEXT.md` | Phase C gap analysis; sprint plan X1 (oracle evaluation), X2 (behavioural detectors), X3 (real-agent execute mode — DONE), etc. |

## 3. The fake customer (memorise — every simulation uses her)

**Valeria Mendoza García** ("Vale"), WhatsApp `5215587654321` (local
`5587654321`), customer `CUST-0084213`, Av. Insurgentes Sur 1425, CDMX.
Order `4151234567`: Galaxy S24 Ultra 256GB, D2D home pickup, out of warranty,
ST030 awaiting parts, quote **$3,480 MXN** unpaid. Order `4149876543`: Galaxy
Watch6 44mm, carry-in, in warranty, ST040 ready-for-pickup — **disclosure
gate**: the agent must NOT reveal this order's status (it strips it silently
while saying "you have two orders"; verified working in every run).

## 4. Critical operational gotchas (each one has bitten already)

1. **Two agent maps.** `tech_repair_whatsapp_map.json` = pristine research map
   (NO terminal outcomes → every execute run scores 0 vacuously — keep for
   research arms). `tech_repair_whatsapp_map_live.json` = execution map (terminal
   outcomes `order_status_provided`/`escalated_to_human`, Spanish confirmation
   phrases, `api_endpoint`, `runtime_tools: [order_lookup, escalate_to_human]`).
   **Always execute with the live map.** The web route auto-merges the live
   map's execution fields into session maps via `agent_endpoints.json`
   `execution_map` (`src/endpoints_config.py::apply_execution_overlay`).
2. **`debugger-platforn/.gitignore` blankets `*.json`** — committing results
   requires `git add -f`.
3. **Web Phase C re-runs OVERWRITE the session's `results/` folder.** This
   cost a 200-run its JSON exports once (commit `420f116`'s JSONs are actually
   from a 10-test run; its `traces/` are the authentic 200-run — recovered
   copy lives at `investigation/02_data/simulated/run_200tests_recovered.json`).
4. **PII in git history** (raw export). Private repo fine; `git filter-repo`
   before any public release. Raise before any push to a new remote.
5. **Python envs.** Research subsystems + web API run on **system python3**
   (pyenv 3.13.5, has fastapi/numpy/matplotlib). Phase B/C CLI use
   `debugger-platforn/venv` (`./venv/bin/python`). Both work for the
   comparison scripts.
6. **Persona-context prompt blocks on stdin.** Non-interactive runs: pipe
   `printf "\n"` (default-Y uses the pre-made context). Do NOT also redirect
   `< /dev/null` (kills the pipe → context OFF, changes the experiment).
7. **`@langchain/core` pinned 1.2.3** in tech_repair-live-agent (bun needs
   `uuid.v6`). The agent's OpenAI event-verifier throws non-fatal
   OUTPUT_PARSING_FAILURE ~10% of tests (upstream zod bug, fails open —
   a genuine production bug faithfully reproduced; do not fix).
8. **Suites are huge** (150-test suite ≈ 30MB; tiled 1000 ≈ 150MB) — never
   commit `results_scale_study/suites/`; regenerate with
   `gen_scale_suites.py` (deterministic, seed 42+N).

## 5. Platform features added 2026-07-24 (all committed, all verified)

- **`conversations.json` export**: every Phase C run writes all dialogues
  (all statuses, full turns + tool calls) via
  `ResultsAggregator.save_conversations()` — CLI, pipeline, and web route.
- **Pre-placed persona context**: `config/persona_context_default.txt`
  (Valeria's data, Spanish). CLI offers default-Y; web UI pre-fills via
  `GET /api/phase-c/persona-context-default` (deletable in the textarea).
- **Tool coverage fixed**: aggregator prefers `runtime_tools` from the agent
  map over the 55 static-analysis names (which pinned live coverage at 0%).
- **Artifact downloads**: `GET /api/artifacts/{session}/{type}?download=true`
  + Conversations/Report/Failures buttons on the Phase C completed view.
- **Web Phase C actually works now**: endpoint field pre-fills from
  `agent_endpoints.json` (was hardcoded dead `:3099`; agent is on `:3098`),
  and the execution-overlay merge (gotcha #1) makes session maps scoreable.
  Verified by the user's own browser runs (141/150 = 94%).

## 6. All execute-mode runs (live agent, chronological)

| Run | N | Result | Where |
|---|---|---|---|
| v1 (research map — the trap) | 10 | 0/10 vacuous | `results_tech_repair_live/` |
| v2 (live map, pre-context) | 10 | 9/10 | `results_tech_repair_live_v2/` |
| v3 (context on) | 10 | 10/10 | `results_tech_repair_live_v3/` |
| v4 (full suite) | 40 | 40/40, 100% tool cov | `results_tech_repair_live_v4/` |
| 200-run (tiled suite, CLI) | 200 | 197/200; 3 real repetition-loop failures (#8 #26 #147) | traces in commit `420f116`; consolidated JSON in `investigation/` |
| User web runs | 10, 150 | 141/150 (94%) | `pipeline_output/session-636fc721/results/` |
| Scale study | 7 batches, 2,560 total | see §7 | `results_scale_study/N*/` |

Oracle pass-rates are ~94–100% because tool-signature oracles can't see
semantic failures (8/8 hard attack tests "passed" in v2 — documented oracle
gap, motivates sprints X1/X2). The **comparison study does not use the
oracles** — see §7.

## 7. The real-vs-sim investigation (the dissertation's behavioural result)

**Design** (`docs/REAL_VS_SIM_COMPARISON_PLAN.md`, pre-registered):
adapt sim conversations to the production schema, run the **identical**
rule-based LLM-free scorer (`src/production/scoring.py`, min_score=3) on both
corpora, project both onto the frozen 16-category taxonomy
(`1.0-frozen-2026-07-14`), compare: reachability matrix, per-category rates
(Wilson CIs), JSD with bootstrap CIs vs split-half noise floor (0.0050) and
uniform anchor. Temperature was rejected as the main axis (literature: weak
lever). Tools: `compare_real_vs_sim.py`, `scale_curves.py`.

**Results** (`docs/results/real_vs_sim/` + `/scale`, and the LaTeX report):

- Real: 376/1,299 failures (28.9%). Sim (pooled 390): 82 (21.0%).
- **Reachability matrix**: found = resolution, loop_stall, missed_escalation,
  silent_abandonment, hallucination (5/7 = 71%). Missed = comprehension
  (40.7% of real failures; personas NEVER repeat verbatim — over-cooperativity,
  0 cases in 2,950 sim convs) and data_gap (12.8%; Valeria's data is complete).
  Unreachable by design = delivery_infra (no WhatsApp layer).
- **loop_stall dominates BOTH corpora**: 68.1% real / 80.5% sim. Mechanistic
  match: sim test #26 = agent repeats identical deflection 18 turns when the
  customer disputes data on file.
- Sim over-produces escalation_failure (23.2% vs 2.9%) and premature_exit
  (12.2% vs 2.4%) — adversarial suite composition; don't read sim frequencies
  as production forecasts.
- **JSD(real,sim) = 0.2392 [0.2010–0.2979]** vs noise floor 0.0050; roughly
  the real-vs-uniform anchor (0.2014) — driven by the two zero categories.
- **Scale study** (batches N=10/50/100/200/400/800/1000, seeds 42+N, fresh DB
  per batch, 96 min wall, $15.84 persona): coverage 29% at N=10 → **71% at
  N=50 → flat through N=1000 and the 2,560 pool**. JSD scale-invariant
  0.21–0.25 (CIs tighten ±0.16→±0.03). Failures linear (3→232), rate stable
  21–30%. **Scale buys volume and precision, never new failure kinds.**

**Everything bundled in `investigation/`** (data, scripts, results, README
with caveats, LaTeX report). Key commits: `8d29d63` platform upgrades,
`4077a5c` v3+v4, `420f116` 200-run, `7cd7d4b` web fixes, `ba576a3` scale
study, `b18dd34` comparison, `e9b91db` investigation package.

## 8. Static-mode results (2026-07-14, unchanged, complement §7)

RQ1 blind-arm recall 0.068 (CI 0.048–0.086) — "field runs on faith".
RQ3 feedback: held-out recall 0.112→0.312 (Δ+0.200, p=0.0001, robust 10/10
sensitivity configs). RQ4 arm ranking: feedback > blind/template > naive_llm
> gan. Reproduce via `run_experiments.py` / `run_sensitivity.py` with the
**pristine** research map. Archived in `docs/results/`.

## 9. WHAT REMAINS (priority order)

1. **Human annotation pass (~1h, only Eduardo can do it, still NOT done).**
   `python3 run_validation.py annotate --packet validation_packet` then
   `... agree`. Gates ALL headline claims (ground truth is rule-based; LLM
   pilot κ 0.51 lenient is explicitly not a substitute).
2. **Ethics submission** (paperwork ready; anonymisation evidence in
   `anonymization/`).
3. **Frustrated/repetitive personas** — highest-leverage simulator fix;
   predicted to open `comprehension` (re-measure with §7 tooling).
4. **Imperfect data seeding** (missing orders, null warranty) — predicted to
   open `data_gap`.
5. **Arm×context 2×2 at N=200** (blind vs feedback-seeded × context on/off) —
   ties §7 to RQ3/RQ4 behaviourally.
6. **Layer 2 case matcher** (embeddings real↔sim failure pairing) — plan §3,
   not yet built.
7. **X1/X2 semantic oracles** (LLM-judged categories, MAST-style κ validation
   on a human subsample) — the sim corpora already contain semantic failures
   invisible to both scorer and oracles (e.g. partial impersonation success).
8. Dissertation chapters — the LaTeX report lifts nearly verbatim into the
   behavioural chapter; `docs/RESEARCH_WORKFLOW.md` covers methodology.

## 10. Quick commands

```bash
# Live agent (terminal 1)
cd tech_repair-live-agent && bun run api                  # :3098

# Phase C against it (terminal 2)
cd debugger-platforn && printf "\n" | ./venv/bin/python execute_tests.py \
  generated_tech_repair/test_suite.json tech_repair_whatsapp_map_live.json \
  --count 40 --workers 4 --ai-personas -o results_new --no-monitor

# Web platform
cd debugger-platforn && uvicorn web.api.app:app --port 8000   # system python3
cd debugger-platforn/web/frontend && bun run dev              # :5173

# Real-vs-sim comparison / scale curves (system python3)
python3 compare_real_vs_sim.py --real ../docs/tech_repair-conversations-anonymized.json \
  --sim <conversations.json> -o ../docs/results/real_vs_sim
python3 scale_curves.py --real ../docs/tech_repair-conversations-anonymized.json \
  --batches results_scale_study -o ../docs/results/real_vs_sim/scale

# Report
cd investigation/05_report && tectonic report.tex

# Full test suite (738 tests)
cd debugger-platforn && python3 -m pytest tests/ -q
```
