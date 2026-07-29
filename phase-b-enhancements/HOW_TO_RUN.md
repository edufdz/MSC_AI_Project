# Phase B Enhancements — Execution Guide

## Quick Reference

To run any sprint, feed Claude Code two files:
```
@phase-b-enhancements/CONTEXT.md @phase-b-enhancements/SPRINT_E<N>_<NAME>.md
```

The CONTEXT.md gives Claude the full picture of the current Phase B codebase (15 files, 3,809 LOC, every dataclass and algorithm). The sprint file gives it the exact changes to make.

---

## Sprint Dependency Graph

```
                    ┌──────────┐
                    │   E12    │  Measurement Harness
                    │ (Week 1) │  ← MUST run first: all others depend on it to prove value
                    └────┬─────┘
                         │
            ┌────────────┼────────────┐
            ▼            ▼            ▼
      ┌──────────┐ ┌──────────┐ ┌──────────┐
      │    E1    │ │    E4    │ │   E11    │
      │  Seeds   │ │ Oracles  │ │ Guardrail│
      │(Week 1-2)│ │(Week 1-2)│ │  Pairs   │
      └────┬─────┘ └────┬─────┘ │(Week 3)  │
           │             │       └──────────┘
           │        ┌────┘
           ▼        ▼
      ┌──────────┐ ┌──────────┐
      │    E2    │ │    E5    │
      │ Policy   │ │ Adversar.│
      │  Graph   │ │(Week 3)  │
      │(Week 2)  │ └──────────┘
      └──────────┘
      ┌──────────┐
      │    E3    │
      │Interact. │
      │ Coverage │
      │(Week 2)  │
      └────┬─────┘
           │
           ▼
      ┌──────────┐ ┌──────────┐ ┌──────────┐
      │    E6    │ │    E7    │ │    E8    │
      │ Prod.    │ │ Quality- │ │  APFD    │
      │ Personas │ │Diversity │ │Priorit.  │
      │(Backlog) │ │(Backlog) │ │(Backlog) │
      └──────────┘ └──────────┘ └──────────┘

                    ┌──────────┐
                    │   E-T    │  Testing Sprint
                    │  (Last)  │  ← Runs after all others
                    └──────────┘
```

---

## Execution Order

### Week 1 — Foundation

**Run first, alone:**

| Sprint | Command | Why First |
|--------|---------|-----------|
| **E12** | `@CONTEXT.md @SPRINT_E12_MEASUREMENT_HARNESS.md` | Every other sprint needs metrics to prove its value. Build APFD, diversity, precision/recall, mutation score. |

**Then, in parallel:**

| Sprint | Command | Can Parallel With |
|--------|---------|-------------------|
| **E1** | `@CONTEXT.md @SPRINT_E1_PRODUCTION_SEED_CORPUS.md` | E4 |
| **E4** | `@CONTEXT.md @SPRINT_E4_NON_LLM_ORACLES.md` | E1 |

**Why parallel**: E1 modifies `src/scenarios/seed_corpus.py` (new) and `src/scenarios/library.py` (new method). E4 modifies `src/oracles/` (new) and `src/scenarios/models.py` (add field) and `src/scenarios/library.py` (new method). They touch different methods in the same file — safe to parallel if you merge carefully. Alternatively, run E4 first (oracles), then E1 (seeds can attach oracles).

**Decision threshold after Week 1**: Run the measurement harness on the enhanced suite vs baseline. If precision/recall against production signals does not improve → the bottleneck is ground-truth signal quality, not generation. Shift effort to taxonomy and human-signal quality before continuing.

---

### Week 2 — Principled Coverage

**In parallel:**

| Sprint | Command | Can Parallel With |
|--------|---------|-------------------|
| **E2** | `@CONTEXT.md @SPRINT_E2_POLICY_GRAPH_SCENARIOS.md` | E3 |
| **E3** | `@CONTEXT.md @SPRINT_E3_INTERACTION_COVERAGE.md` | E2 |

**Why parallel**: E2 creates `src/scenarios/policy_graph.py` (new) and adds a method to `library.py`. E3 creates `src/coverage/interaction.py` and `src/coverage/transition.py` (new) and modifies `calculator.py` and `test_suite.py`. They touch completely different files.

**Decision threshold after Week 2**: If interaction coverage (E3) does not beat flat repetition on seeded faults → the agent's faults are genuinely single-tool. Keep flat counts for highest-risk tools only and reinvest saved budget into E1 seeds.

---

### Week 3 — Security & Guardrails

**In parallel:**

| Sprint | Command | Can Parallel With |
|--------|---------|-------------------|
| **E5** | `@CONTEXT.md @SPRINT_E5_ADVERSARIAL_GENERATION.md` | E11 |
| **E11** | `@CONTEXT.md @SPRINT_E11_GUARDRAIL_TEST_PAIRS.md` | E5 |

**Why parallel**: E5 creates `src/scenarios/adversarial.py` (new) and adds a method to `library.py` and `builder.py`. E11 creates `src/scenarios/guardrail_pairs.py` (new) and adds a method to `library.py`. Both add methods to `library.py` but different methods — safe to parallel.

**Depends on**: E4 (oracles) must be done first — both E5 and E11 attach oracles to their scenarios.

---

### Backlog — Realism & Efficiency

**Run in any order, after Weeks 1–3:**

| Sprint | Command | Can Parallel With |
|--------|---------|-------------------|
| **E6** | `@CONTEXT.md @SPRINT_E6_PRODUCTION_PERSONAS.md` | E7, E8 |
| **E7** | `@CONTEXT.md @SPRINT_E7_QUALITY_DIVERSITY.md` | E6, E8 |
| **E8** | `@CONTEXT.md @SPRINT_E8_APFD_PRIORITISATION.md` | E6, E7 |

**All three can run in parallel**: E6 creates `src/personas/trace_grounding.py` (new). E7 creates `src/personas/quality_diversity.py` (new) and modifies `builder.py` (dedup logic). E8 creates `src/generator/prioritiser.py` (new) and modifies `test_suite.py` (allocation logic). Different files.

**Note**: E8 refactors `test_suite.py` from fixed 4-phase to candidate-then-prioritise. If E3 has already modified `test_suite.py` (Phase 1.5 for transitions), E8 should be aware of those changes. Run E3 before E8, or at least read E3's changes first.

---

### Last — Testing Sprint

| Sprint | Command |
|--------|---------|
| **E-T** | `@CONTEXT.md @SPRINT_ET_TESTING.md` |

**Runs after all other sprints are complete.** Creates fixtures, unit tests, integration tests, regression tests, and validation comparisons.

---

## Parallelisation Summary

```
Week 1:     E12                    (alone — foundation)
Week 1-2:   E1 ∥ E4               (parallel — different new files)
Week 2:     E2 ∥ E3               (parallel — different modules)
Week 3:     E5 ∥ E11              (parallel — different new files, both need E4 done)
Backlog:    E6 ∥ E7 ∥ E8          (all parallel — all different files)
Last:       E-T                    (after everything)
```

**Maximum parallelism**: 3 sprints at once (Backlog week).
**Critical path**: E12 → E4 → E5/E11 → E-T (measurement → oracles → security tests → validation).

---

## File Conflict Matrix

Which sprints touch the same files (merge carefully if running in parallel):

| File | Modified By |
|------|-------------|
| `src/scenarios/library.py` | E1 (new method), E2 (new method), E5 (new method), E11 (new method) |
| `src/scenarios/models.py` | E4 (add oracles field) |
| `src/generator/test_suite.py` | E1 (Phase 0), E3 (Phase 1.5), E5 (Phase 2.5), E8 (full refactor) |
| `src/personas/builder.py` | E5 (new method), E6 (new method), E7 (replace dedup) |
| `src/coverage/calculator.py` | E3 (refactor) |
| `src/coverage/models.py` | E3 (new fields) |
| `generate_tests.py` | E1, E2, E5, E6, E8, E11, E12 (wire new features) |

**Safest parallel groups** (no shared files):
- E1 + E4 (seeds + oracles)
- E2 + E3 (policy graph + interaction coverage)
- E6 + E7 (personas — E7 modifies builder.py dedup, E6 adds new method)

**Requires sequential merge**:
- E8 should run after E3 (both modify test_suite.py allocation)
- E5 and E11 both add to library.py (but different methods — safe if careful)

---

## How to Feed Context to Claude

### For a single sprint:
```
@phase-b-enhancements/CONTEXT.md @phase-b-enhancements/SPRINT_E12_MEASUREMENT_HARNESS.md

Implement Sprint E12 from the spec.
```

### For parallel sprints (same session, different agents):
```
@phase-b-enhancements/CONTEXT.md @phase-b-enhancements/SPRINT_E1_PRODUCTION_SEED_CORPUS.md

Implement Sprint E1. Note: Sprint E4 (oracles) may be running in parallel — 
it adds an `oracles` field to Scenario in models.py. Don't conflict with that.
```

### For the TechRepair WhatsApp agent context:
```
@phase-a-enhancements/TECH_REPAIR_AGENT.md @phase-b-enhancements/CONTEXT.md @phase-b-enhancements/SPRINT_E1_PRODUCTION_SEED_CORPUS.md

Implement Sprint E1 for the TechRepair WhatsApp agent.
```

### To run tests after implementation:
```
@phase-b-enhancements/CONTEXT.md @phase-b-enhancements/SPRINT_ET_TESTING.md

Implement the testing sprint for Phase B enhancements.
```

---

## Decision Checkpoints

| After | Check | If Fails |
|-------|-------|----------|
| E12 | Baseline APFD and diversity computed | Fix harness before proceeding |
| E1 + E4 | Recall of production failures improves vs baseline | Bottleneck is ground-truth signals → improve taxonomy/labelling |
| E3 | Interaction coverage beats flat 25x on seeded faults | Agent faults are single-tool → keep flat counts, invest in E1 |
| E5 + E11 | Every OWASP/guardrail category has ≥1 test | Missing templates → add more attack patterns |
| E8 | APFD improves vs fixed 4-phase | Prioritisation model needs tuning → adjust fault-proneness weights |
| E-T | All tests pass, enrichment comparison positive | Regression → debug specific failing enhancement |

---

## Quick Command Reference

```bash
# Run Phase B (current baseline)
python generate_tests.py tech_repair_whatsapp_map.json --skip-ai -o output/

# Run Phase B with traces
python generate_tests.py tech_repair_whatsapp_map.json --skip-ai --use-traces -o output/

# Run Phase B with AI
python generate_tests.py tech_repair_whatsapp_map.json -o output/

# Run Phase B with evaluation (after E12)
python generate_tests.py tech_repair_whatsapp_map.json --skip-ai --evaluate -o output/

# Run all Phase B tests
pytest tests/phase_b/ -v

# Run specific enhancement tests
pytest tests/phase_b/unit/test_seed_corpus.py -v

# Compare enhanced vs baseline
pytest tests/phase_b/validation/test_enrichment_comparison.py -v
```
