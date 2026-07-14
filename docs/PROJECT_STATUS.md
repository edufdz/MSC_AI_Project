# Project Status — Full Context

**Last updated: 2026-07-14.** This is the single catch-up document for the
project. Read this first in any new working session (human or AI assistant)
— it says what exists, what the results are, how to reproduce them, and
what remains.

---

## 1. The project in three sentences

The dissertation ("Closing the Loop Between Synthetic Agent Testing and
Production Reality", Imperial MSc AI) asks whether synthetic adversarial
testing of a conversational agent predicts the failures that occur in real
production, and whether feeding real production failures back into test
generation improves that prediction. The testbed is the agent testing
platform in `debugger-platforn/` (Phases A–E pipeline + web UI) and 1,299
real Spanish WhatsApp support conversations from the deployed Samsung agent
(Pulpoo). **Design decision (2026-07-14): there is NO live connection
between the Samsung production system and this platform** — conversations
were extracted once, anonymised, and everything runs offline on the
anonymised corpus.

## 2. What exists and works (all pushed to main, 738 tests passing)

### The platform (pre-existing, fixed & enhanced)
- Phases A–E pipeline: analyze agent code → generate personas/scenarios/
  tests → execute → diagnose → improve; web UI (FastAPI + React) with
  per-phase pages. Runs fully offline with `--mock --skip-ai`.
- Fixes made: TypeScript agents no longer ignored by `run_pipeline.py`;
  offline runs auto-fall back to template scenarios; production-seed budget
  fraction actually enforced; SPA deep links no longer 404.
- Phase A now emits a hierarchical `code_tree` (directories → files →
  classes → functions, annotated with tools/prompts/risks/entry points),
  rendered as a collapsible tree in the Phase A page.

### The research subsystems (built 2026-07-14, the dissertation's "connective tissue")
| Component | Where | What it does |
|---|---|---|
| Batch anonymiser | `debugger-platforn/anonymize_export.py` + `anonymization/` | 3-pass (regex → Spanish NER → brand scrub); drops direct identifiers; ~2 min for the full corpus |
| Production ingestion + ground truth | `src/production/` | Failure scoring from human-process signals ONLY (no LLM judge): escalations, human takeovers, delivery failures, intent/confidence telemetry → 8 production failure categories |
| Frozen shared taxonomy | `src/evaluation/taxonomy.py` | 16 categories, version `1.0-frozen-2026-07-14` — do not change mid-campaign |
| Projection layer | `src/evaluation/projection.py` | Total maps: Phase D root causes AND production categories → shared taxonomy; unmapped values fail at import |
| Measurement engine | `src/evaluation/measurement.py` | Per-category precision/recall, recall-vs-budget curves, bootstrap CIs, paired sign-flip permutation tests |
| Production-feedback loop | `src/feedback/` | Train-split failures → seeds → re-seeded Phase B generation; hard leakage guard against held-out contamination |
| Sandbox bridge | `src/sandbox/`, `sandbox_bridge.py` | Offline simulated agent endpoint (echo mode) + replay/fidelity comparator (production vs simulation, no LLM) |
| Experiment runner | `run_experiments.py` | RQ1–RQ4 end to end; static (targeting) and execute (behavioural) modes; charts + REPORT.md |
| Generation arms (RQ4) | `src/experiments/arms.py` | template/blind, naive_llm, gan (generator-critic with LLM critic), feedback |
| Sensitivity sweep | `run_sensitivity.py` | RQ3 robustness across min_score 2–5, holdout 0.2–0.4, seeds 41–45 |
| Validation harness | `run_validation.py`, `src/production/validation.py` | Blind 50-conversation annotation packet + Cohen's κ agreement (see §4 — **the human pass is still TO DO**) |
| Web integration | `/api/research/*`, frontend **Research** page | Anonymise → ground-truth preview → run experiments → results/charts/history |

### The data
- `docs/samsung-conversations-export.json` — RAW export, 1,299 conversations,
  **contains real customer PII and is tracked in git history**. Keep the
  repo private; purge before any public release.
- `docs/samsung-conversations-anonymized.json` — the anonymised corpus every
  experiment uses (verified: zero email/phone leaks, identifiers dropped).
- `debugger-platforn/samsung_whatsapp_map.json` — Phase A agent map of the
  real Samsung agent (predates the code_tree feature; re-run Phase A on the
  agent repo to regenerate with the tree).

## 3. The results (archived in `docs/results/`, regenerable deterministically)

Ground truth: **376 failed conversations** out of 1,299 (structured signals,
no LLM). Time split: train = Jan–May, held-out = Jun 2026.

| Question | Result |
|---|---|
| **RQ1** — does synthetic testing predict production failures? | Blind-arm recall **0.068** (95% CI 0.048–0.086), precision 0.571. Low predictive validity — the quantified "field runs on faith" finding. |
| **RQ2** — what does it miss? | Systematic gaps: resolution, comprehension, data-gap, delivery, loops, hallucination — long-horizon and backend-data failure modes, characterised per category. |
| **RQ3** — does production feedback help? | Held-out recall **0.112 → 0.312** (Δ +0.200, p = 0.0001). **Robust in 10/10 sensitivity configurations** (Δ +0.165…+0.288, all p = 0.0001). |
| **RQ4** — which generation method wins? | **feedback > blind/template > naive_llm > gan** by held-out recall per budget. |

Caveat that must accompany any citation: these are **static-mode** numbers
(what suites are *designed* to detect). Execute mode works end-to-end but
was only demonstrated against the echo stand-in agent; behavioural numbers
require running a local copy of the Samsung agent behind the sandbox bridge.

Reproduce everything:
```bash
cd debugger-platforn
python3 run_experiments.py --export ../docs/samsung-conversations-anonymized.json \
    --agent-map samsung_whatsapp_map.json --budget 100 --arms blind,feedback,naive_llm,gan
python3 run_sensitivity.py --export ../docs/samsung-conversations-anonymized.json \
    --agent-map samsung_whatsapp_map.json
```

## 4. WHAT REMAINS — the to-do list, in priority order

### 4.1 The human annotation (~1 hour, only Eduardo can do it) — NOT DONE YET
**What it is, in plain words:** the ground truth (which conversations count
as "failures") comes from automatic rules. Before the dissertation can rely
on it, a human must read a sample of conversations and independently judge
them, so we can report how often the human agrees with the rules. An AI
cannot do this — the study's credibility rests on the labels being
human-verified.

**How to do it (everything is already prepared):**
```bash
cd ~/Desktop/dos-agent-debugger/MSC_AI_Project/debugger-platforn
python3 run_validation.py annotate --packet validation_packet
```
The terminal shows 50 anonymised conversations one at a time. For each you
answer three quick questions: did the agent fail (y/p/n)? which categories
(pick numbers)? optional one-line note. It saves after every answer; press
`q` anytime to stop and resume later. Do NOT open
`validation_packet/answer_key.json` until finished. When done:
```bash
python3 run_validation.py agree --packet validation_packet \
    --annotations validation_packet/annotations.json
```
That prints Cohen's κ and per-category agreement — the number the
dissertation reports. (An LLM *pilot* pass already exists — lenient
agreement 0.86, κ 0.51, no heuristic bugs found — but it is explicitly NOT
a substitute and is labelled as pilot-only in `docs/results/validation_pilot/`.)

### 4.2 Ethics submission (paperwork, ready to go)
The anonymisation system, its tests, and the verified-clean corpus are the
evidence the submission needs. See `anonymization/` + `docs/RESEARCH_WORKFLOW.md`.

### 4.3 Behavioural (execute-mode) results — optional but strengthens RQ1
Run a local copy of the Samsung agent (repo `pulpoo-final`, outside this
project) behind the sandbox bridge, then:
```bash
python3 sandbox_bridge.py serve --agent-map samsung_whatsapp_map.json --mode http \
    --upstream-url http://localhost:<agent-port> --port 8099
python3 run_experiments.py ... --mode execute --connector http://localhost:8099
```
Use `sandbox_bridge.py replay` to report the fidelity score (echo-mode
baseline to beat: 0.36).

### 4.4 Write the dissertation chapters
Nearly everything lifts directly: `docs/RESEARCH_WORKFLOW.md` (methodology),
`docs/results/rq4_full/REPORT.md` (results), `docs/results/sensitivity/
SENSITIVITY.md` (robustness), the projection tables in `results.json`
(taxonomy defence), plus the write-up notes below.

**Write-up notes collected along the way:**
- Static-mode seeds don't change results (identical across seeds 41–45) —
  expected: category-level targeting is invariant to pairing randomness;
  present as stability, not an anomaly.
- Strict vs lenient agreement in the pilot (κ 0.51 lenient vs 0.09 strict)
  suggests the ground truth captures "customer-unserved friction" rather
  than only catastrophic failure — frame the criterion accordingly.
- The pilot annotator redistributes the "resolution" category into
  comprehension/loop/missed-escalation — discuss category semantics.
- GAN arm accepted only 9/24 candidates in the demo run; its low RQ4 rank
  partly reflects fewer, narrower scenarios per budget in static targeting.

## 5. How to run everything (quick reference)

| What | Command |
|---|---|
| Full test suite (738) | `cd debugger-platforn && python3 -m pytest tests/ -q` |
| Web platform | `uvicorn web.api.app:app --port 8000` (+ `npm run dev` in `web/frontend`, or use the built dist served at :8000) |
| Offline pipeline demo | `python3 run_pipeline.py ../fake-car-dealership-agent --mock --skip-ai` |
| Anonymise a new export | `python3 anonymize_export.py --input <raw.json> --output <anon.json>` |
| Experiments (RQ1–4) | see §3 |
| Sensitivity | see §3 |
| Human validation | see §4.1 |
| Research web UI | http://localhost:8000/research |

Environment: no venv — system `python3` (pyenv 3.13.5) has all deps.
`ANTHROPIC_API_KEY` lives in `debugger-platforn/.env` (needed only for AI
phases, LLM arms, and the GAN critic). The anonymisation backend imports
with `anonymization/backend` on `sys.path` (handled by
`src/production/anonymize.py`).

## 6. Open flags

1. **PII in git history**: the raw export is tracked. Private repo = fine;
   purge with `git filter-repo` before making public or sharing.
2. **Human annotation not yet done** (§4.1) — the only remaining gating
   test that requires no new code.
3. `samsung_whatsapp_map.json` predates the Phase A code-tree feature;
   regenerate when convenient.
