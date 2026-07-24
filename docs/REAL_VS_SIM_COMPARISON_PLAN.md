# Real vs. Simulated Failures — Comparison Methodology Plan

**Written 2026-07-24.** Companion to `PROJECT_STATUS.md` (research state),
`Agent_Failure_Analysis_Plan.pdf` (the production failure-analysis plan), and
`SAMSUNG_LIVE_SIMULATION.md` (the live-agent execute-mode work). This document
proposes **how to compare real production errors against simulated
conversations** for the dissertation, and how to structure the resulting
report chapter.

---

## 1. What question is actually being asked

The dissertation's RQ1 — *does synthetic testing predict production
failures?* — has so far been answered only in **static mode** (recall 0.068:
what suites are *designed* to target). With the live agent
(`samsung-live-agent/`, sprint X3) we can now answer the **behavioural**
version:

> When the simulator talks to the *real* agent code, do the failures that
> emerge match the failures observed in the 1,299 real conversations — in
> kind, in frequency, and in mechanism?

That is a **correspondence study** between two corpora:

| | Real corpus | Simulated corpus |
|---|---|---|
| Source | `docs/samsung-conversations-anonymized.json` (1,299 convs, 376 rule-based failures) | Phase C `conversations.json` runs against the live agent (v4: 40, session-636fc721: 200; more can be generated at ~$0.005/conv persona cost) |
| Failure labels | 8 production categories from structured signals (`src/production/`) | Same signals are observable in simulated dialogues (escalation, repeats, loops, abandonment) |
| Common language | **Frozen 16-category shared taxonomy** (`src/evaluation/taxonomy.py`, v1.0-frozen-2026-07-14) via the projection layer | Same |

Almost everything needed already exists; the new work is one adapter (run the
production failure scorer over simulated conversations) plus the analysis
itself.

## 2. Why *not* temperature (as the main axis)

Temperature was considered as the experimental variable. The literature says
it is a weak lever: reducing temperature to 0.2 had *no significant effect*
on behavioural fidelity of simulated users, and higher temperature only
mildly increases semantic diversity of open-ended text ([What Would GPT
Click, 2026](https://arxiv.org/pdf/2605.18302)). The deeper misalignments of
LLM-simulated users — systematic over-cooperativeness (politeness in 96% of
simulated vs 20% of real conversations), quiet strategy-pivoting instead of
irritation — are not temperature-addressable ([Lost in
Simulation](https://arxiv.org/html/2601.17087v2); [Synthetic Users, Real
Differences](https://arxiv.org/pdf/2605.02624)).

**Recommendation:** keep temperature as a small robustness appendix (one
sweep, §6.4), and use experimental axes that demonstrably change which
failures appear (§6).

## 3. The three comparison layers

### Layer 1 — Category-distribution correspondence (the headline numbers)

1. Run the **same** structured-signal failure scorer over both corpora.
   The production scorer (`src/production/`) uses human-process signals —
   escalation, human request, >40 messages, customer repeats, expiry
   without resolution — all of which exist in simulated conversations too
   (`conversations.json` has full turns, tool calls, outcomes). Delivery
   failures are structurally impossible in simulation → pre-registered as
   *unreachable* (§5).
2. Project both label sets into the frozen 16-category taxonomy.
3. Report:
   - **Coverage/recall**: which production failure categories does the
     simulation reproduce at all; per-category recall with bootstrap CIs
     (the machinery in `src/evaluation/measurement.py`).
   - **Distributional similarity**: Jensen–Shannon divergence between the
     two category distributions — symmetric and bounded, the standard
     choice for real-vs-generated comparison ([JSD
     properties](https://www.activeloop.ai/resources/glossary/jensen-shannon-divergence/);
     [statistical properties & power](https://arxiv.org/html/2607.12407)) —
     with a bootstrap CI, plus a chi-square/G-test of association.
   - **Null baselines** to anchor interpretation: (a) uniform distribution,
     (b) the echo-agent fidelity baseline (0.36 from `sandbox_bridge.py
     replay`), (c) a scrambled-labels permutation. "JSD = X" means nothing
     without these.

### Layer 2 — Case-level correspondence (mechanism matching)

Frequencies can match by accident; the dissertation is stronger if specific
real failures have simulated lookalikes.

1. For each real failure cluster (from the production pipeline's pattern
   aggregation), retrieve nearest simulated conversations (multilingual
   embeddings over anonymised text + failure signature: category, turn
   count, tools involved, outcome).
2. Manually verify the top matches; present 5–10 matched pairs as a table
   with short excerpts, and equally important, the *unmatched* clusters.
3. One pair already exists: session-636fc721 test #26 — the agent repeats
   the same phone-number deflection verbatim for 18 turns when the customer
   contests registered data — is a live reproduction of the production
   **Loop/stall** category (287 chats, the 2nd-largest real failure mode).

This mirrors the MAST methodology of trace-level annotation with
inter-annotator agreement ([Why Do Multi-Agent LLM Systems
Fail?](https://arxiv.org/abs/2503.13657), κ = 0.88 human, 0.77 LLM-judge):
if an LLM judge is used to label simulated failures, validate it on a
human-annotated subsample and report κ.

### Layer 3 — The two-sided gap (what each side finds that the other cannot)

- **Sim-only findings**: adversarial probes (impersonation, scope
  escalation) that pass tool-signature oracles but reveal semantic issues —
  production data cannot contain deliberate attacks at scale.
- **Real-only findings**: delivery failures (WhatsApp API), multi-customer
  data gaps, long-horizon threads spanning days — structurally out of the
  simulator's reach today.
- Present as a reachability matrix over the 16 categories:
  `reachable-and-found / reachable-but-missed / unreachable`. The
  *reachable-but-missed* cell is the actionable finding (next-step work for
  the simulator); *unreachable* cells are scope limits, not failures of the
  method. This framing follows the sim-to-real MDP-mismatch view
  ([Sim-to-Real Gap of Foundation-Model Agents](https://arxiv.org/html/2606.07017))
  and the observation that synthetic and production failure modes are
  structurally different ([Why AI Agents Break in
  Production](https://latitude.so/blog/why-ai-agents-break-in-production)).

## 4. Statistical treatment

- Per-category recall/precision: bootstrap CIs (≥1,000 resamples), Wilson
  intervals for small counts.
- Distribution match: JSD + bootstrap CI; chi-square with the caveat of
  sparse cells (merge or exact test below expected count 5).
- Significance of arm/config differences: the paired sign-flip permutation
  tests already in `measurement.py`.
- **Sample size**: rare real categories (missed escalation: 16/1,299 ≈ 1.2%)
  need enough simulated conversations to be observable — at 500 sims, a
  1.2%-rate category yields ~6 expected cases; report expected counts and
  power alongside, and treat categories under ~10 expected cases as
  qualitative-only.

## 5. Pre-registered validity threats (write these BEFORE running)

1. **Oracle gap**: tool-signature oracles miss semantic failures
   (demonstrated: 8/8 hard tests "passed" in v2). Mitigation: Layer 1 uses
   the signal-based scorer, not the Phase C pass/fail verdict.
2. **Over-cooperative simulated users**: expect under-representation of
   frustration-driven categories (missed escalation, silent abandonment) —
   cite [Lost in Simulation](https://arxiv.org/html/2601.17087v2) and
   check directionally.
3. **Single fake customer**: Valeria's two orders bound the reachable
   data-gap and multi-order failure space.
4. **Ground-truth labels are rule-based and the human κ pass (§4.1 of
   PROJECT_STATUS) is still pending** — complete it before headline claims.
5. **Clean transport**: simulated tool calls never time out or rate-limit,
   unlike production ([realism-benchmark
   critique](https://arxiv.org/pdf/2606.12191)); chaos injection covers a
   slice of this but not WhatsApp delivery.
6. Anonymisation noise on the real side (entity scrubbing may weaken
   embedding matches in Layer 2).

## 6. Experimental axes (what to actually vary)

| Axis | Why | Cost |
|---|---|---|
| 6.1 **Persona context** on/off | Already observed to change conversation shape drastically (2-turn convergence with context vs long exploration without) — directly manipulates the comprehension/loop categories | 2 runs |
| 6.2 **Generation arm**: blind vs feedback-seeded suites (ties to RQ3/RQ4) | The dissertation's own headline claim (feedback 0.112→0.312 static) gets its behavioural confirmation — *the* highest-value experiment | 2 runs |
| 6.3 **Scale/saturation**: category coverage vs N sims (N = 50…500+) | Reuses recall-vs-budget machinery; shows whether missing categories are budget-limited or structurally unreachable | marginal |
| 6.4 Temperature sweep (0.3 / 0.7 / 1.0 on the persona LLM) | Robustness appendix only (expected: diversity ↑ slightly, category mix ~unchanged) | 3 small runs |

Suggested headline experiment: **2×2 (arm × context) at N=200 each**, plus
the saturation curve pooled across runs. ~800 conversations ≈ $4–6 persona
cost + agent-side LLM cost; entirely feasible.

## 7. Report structure (dissertation chapter)

1. Motivation: static-mode RQ1 answered "designed-to-detect"; this chapter
   answers "actually-produces".
2. Method: corpora, shared taxonomy + projection (already defended),
   scorer-parity argument, layers 1–3, pre-registered threats.
3. Results: reachability matrix → category recall + JSD vs baselines →
   matched-pair case studies → axis effects (arm, context, saturation).
4. Discussion: what correspondence was achieved, what is budget-limited vs
   structurally unreachable, implications for "testing on faith".
5. Threats to validity: §5 verbatim, with observed evidence for each.

## 8. Implementation checklist (in order)

- [x] Adapter: run `src/production/` failure scoring over Phase C
      `conversations.json` (field mapping only — turns, roles, escalation
      signals, outcome; delivery signals marked N/A). →
      `compare_real_vs_sim.py::adapt_sim_conversation`
- [x] `compare_real_vs_sim.py`: projection → per-category table, recall+CIs,
      JSD + baselines (split-half noise floor, uniform), reachability matrix,
      chart, REPORT.md. First run (390 live-agent sims, 2026-07-24):
      coverage 5/7, JSD 0.2392 [0.2010–0.2979] vs noise floor 0.0050;
      loop_stall dominates both corpora (68% real / 81% sim);
      comprehension and data_gap at 0 in sim — pre-registered threats #2
      (over-cooperative personas never repeat verbatim) and #3 (single fully
      seeded fake customer) observed exactly as predicted. Results:
      `docs/results/real_vs_sim/`.
- [ ] Layer 2 matcher: embeddings + manual verification workflow.
- [ ] Run the 2×2 + saturation experiments (§6).
- [ ] Human annotation pass (§4.1 PROJECT_STATUS) — gating for headline claims.
- [ ] Optional LLM-judge for categories the rules can't see (hallucination),
      validated with κ on a human subsample (MAST-style).

## Sources

- [Lost in Simulation: LLM-Simulated Users are Unreliable Proxies](https://arxiv.org/html/2601.17087v2)
- [Synthetic Users, Real Differences: an Evaluation Framework for User Simulation](https://arxiv.org/pdf/2605.02624)
- [RealUserSim: Bridging the Reality Gap in Agent Benchmarking](https://arxiv.org/html/2605.20204)
- [Mind the Sim2Real Gap in User Simulation for Agentic Tasks](https://arxiv.org/html/2603.11245)
- [Simulated Customers Never Walk Away: Decision Fidelity of LLM User Simulators](https://arxiv.org/pdf/2606.20708)
- [The Sim-to-Real Gap of Foundation Model Agents: A Unified MDP Perspective](https://arxiv.org/html/2606.07017)
- [Why Do Multi-Agent LLM Systems Fail? (MAST)](https://arxiv.org/abs/2503.13657)
- [What Would GPT Click: Practical Effects of Human-AI Behavioral Misalignment](https://arxiv.org/pdf/2605.18302)
- [Statistical Properties and Power Analysis of Divergence Measures](https://arxiv.org/html/2607.12407)
- [Jensen–Shannon divergence (properties)](https://www.activeloop.ai/resources/glossary/jensen-shannon-divergence/)
- [Why AI Agents Break in Production](https://latitude.so/blog/why-ai-agents-break-in-production)
- [Agentic Environment Engineering survey (realism benchmarks)](https://arxiv.org/pdf/2606.12191)
