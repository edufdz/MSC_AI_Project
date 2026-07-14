# Phase A Enhancements — Execution Order & Dependencies

## Overview

9 enhancement sprints + 1 testing sprint, organized into parallel groups and sequential dependencies. Sprints within the same group can be executed by **simultaneous agents** with no file conflicts.

---

## Dependency Graph

```
                  ┌──── Sprint 1 (Tree-sitter TS/JS) ────┐
                  │                                       │
 Group 1 ────────├──── Sprint 3 (OWASP Taxonomy) ───────├──── (all finish)
 (parallel)       │                                       │         │
                  └──── Sprint 9 (Multilingual Meta) ────┘         │
                                                                    │
                           ┌────────────────────────────────────────┤
                           │                                        │
                     Sprint 2 (Preconditions)                 Sprint 5 (Hierarchical Summarisation)
                           │
                           │
                  ┌────────┴────────┐
                  │                 │
 Group 2 ───────├ Sprint 4 (Taint) ├──── (both finish)
 (parallel)      │                 │
                  └ Sprint 6 (Rules)┘
                           │
                           │
                     Sprint 7 (Langfuse Traces)
                           │
                           │
                     Sprint 8 (Behavioural Model)
                           │ 
                     Sprint T (Testing)
                           Ç │
```Ç 
Ç 
---Ç 

## Execution Schedule

### Group 1 — Run in Parallel (no dependencies)

| Sprint | Name | Effort | Files Touched |
|--------|------|--------|---------------|
| 1 | Tree-sitter TS/JS AST parsing | Medium | `src/analysis/static_analyzer.py`, `requirements.txt`, `pyproject.toml` |
| 3 | OWASP/MITRE risk taxonomy mapping | Small | `config/framework_signatures.py`, `src/risk/analyzer.py`, `src/graph/builder.py`, `analyze.py` |
| 9 | Multilingual/domain metadata fields | Small | `src/graph/builder.py`, `config/framework_signatures.py` |

**No file conflicts**: Sprint 1 touches the static analyzer. Sprint 3 touches risk analyzer and framework signatures. Sprint 9 touches builder.py and framework signatures — but Sprint 3 and 9 modify **different sections** of those files (Sprint 3 adds risk constants; Sprint 9 adds language word lists).

**Note**: If running Sprints 3 and 9 on the same agent, coordinate on `config/framework_signatures.py` — Sprint 3 adds `OWASP_LLM_2025`, `OWASP_AGENTIC_2026`, `RISK_TO_TAXONOMY` dicts; Sprint 9 adds `SPANISH_INDICATORS`, `PORTUGUESE_INDICATORS`, `DOMAIN_INDICATORS` dicts. No overlap.

---

### After Group 1 — Sequential (depends on Sprint 1)

| Sprint | Name | Effort | Depends On | Why |
|--------|------|--------|-----------|-----|
| 2 | Per-tool preconditions/postconditions | Medium | Sprint 1 | Needs complete AST from all languages to extract guard clauses and side-effects from TS/JS tools |
| 5 | Hierarchical code summarisation | Large | Sprint 1 | Needs accurate call graphs from tree-sitter for all languages to build the relevance-ranked context |

**Sprints 2 and 5 can run in parallel with each other** — Sprint 2 modifies `detector.py` and AI prompts; Sprint 5 creates a new `code_navigator.py` and modifies `ai_analyzer/analyzer.py`. Minimal overlap (both touch `analyzer.py` but different functions).

---

### Group 2 — Run in Parallel (depends on Group 1)

| Sprint | Name | Effort | Depends On | Why |
|--------|------|--------|-----------|-----|
| 4 | Intra-procedural taint/data-flow analysis | Large | Group 1 complete | Uses enriched `FileSymbols` from Sprint 1's tree-sitter parser; uses taxonomy IDs from Sprint 3 |
| 6 | Guardrail/policy rule extraction | Medium | Group 1 complete | Uses language metadata from Sprint 9 for rule language detection |

**No file conflicts**: Sprint 4 creates a new `src/analysis/taint_analyzer.py` and modifies `risk/analyzer.py`. Sprint 6 creates a new `src/patterns/rule_extractor.py` and modifies AI prompts. Different files entirely.

---

### After Group 2 — Sequential

| Sprint | Name | Effort | Depends On | Why |
|--------|------|--------|-----------|-----|
| 7 | Dynamic trace integration (Langfuse) | Large | Sprints 2 + 3 | Needs enriched tool model (preconditions from Sprint 2, taxonomy from Sprint 3) to compare static vs dynamic analysis |

---

### After Sprint 7 — Sequential

| Sprint | Name | Effort | Depends On | Why |
|--------|------|--------|-----------|-----|
| 8 | Behavioural model layer (FSM + dependency graph) | Large | Sprints 2 + 7 | Needs preconditions (Sprint 2) for dependency typing and trace data (Sprint 7) for FSM inference |

---

### After All — Final

| Sprint | Name | Effort | Depends On | Why |
|--------|------|--------|-----------|-----|
| T | End-to-end testing & validation | Medium | All sprints | Validates everything works together, creates test fixtures, regression tests |

---

## Timeline View

```
Phase  ┃  Sprints Running                         ┃  Agents Needed
━━━━━━━╋━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╋━━━━━━━━━━━━━━
  1    ┃  Sprint 1 ┆ Sprint 3 ┆ Sprint 9          ┃  3 agents
       ┃                                           ┃
  2    ┃  Sprint 2 ┆ Sprint 5                      ┃  2 agents
       ┃                                           ┃
  3    ┃  Sprint 4 ┆ Sprint 6                      ┃  2 agents
       ┃                                           ┃
  4    ┃  Sprint 7                                 ┃  1 agent
       ┃                                           ┃
  5    ┃  Sprint 8                                 ┃  1 agent
       ┃                                           ┃
  6    ┃  Sprint T                                 ┃  1 agent
```

**Maximum parallelism**: 3 agents (Phase 1)
**Total phases**: 6 sequential phases
**Critical path**: Sprint 1 → Sprint 2 → Sprint 7 → Sprint 8 → Sprint T

---

## Quick Reference: What Each Sprint Produces

| Sprint | Input | Output (new in Agent Map) |
|--------|-------|---------------------------|
| 1 | TS/JS source files | Complete `FileSymbols` with types, decorators, JSDoc, call graphs |
| 2 | `FileSymbols` + tools | `tools[].preconditions`, `postconditions`, `side_effects`, `state_modifying` |
| 3 | Existing risks | `risks[].taxonomy_ids`, `risk_summary.by_taxonomy`, unsafe ops + excessive agency detection |
| 4 | `FileSymbols` | `risk_flags.taint_flows[]` (source → sink paths with PII types) |
| 5 | `FileSymbols` + call graph | Better AI analysis (no truncation, relevance-ranked context, fact validation) |
| 6 | Prompts | `guardrails.rules[]` with categories, complexity, scope, interactions |
| 7 | Langfuse traces | `trace_analysis` (tool frequency, common sequences, failure patterns, static vs dynamic comparison) |
| 8 | Preconditions + traces | `behavioural_model` (typed dependency graph, FSM states/transitions, coverage targets) |
| 9 | Prompts | `metadata.language` (rich object), `metadata.domain` (type, industry, channel) |
| T | All of the above | Test fixtures, unit tests, integration tests, validation harness |

---

## How to Run Each Sprint

Each sprint has its own MD file with detailed tasks, file paths, line numbers, and done-when criteria:

```
phase-a-enhancements/
├── CONTEXT.md                          ← Plug this into a new terminal first
├── SPRINT_1_TREESITTER_TS_JS.md
├── SPRINT_2_PRECONDITIONS.md
├── SPRINT_3_OWASP_TAXONOMY.md
├── SPRINT_4_TAINT_ANALYSIS.md
├── SPRINT_5_HIERARCHICAL_SUMMARISATION.md
├── SPRINT_6_GUARDRAIL_EXTRACTION.md
├── SPRINT_7_LANGFUSE_TRACES.md
├── SPRINT_8_BEHAVIOURAL_MODEL.md
├── SPRINT_9_MULTILINGUAL_METADATA.md
└── SPRINT_T_TESTING.md
```

**To start a sprint in a new agent terminal**:
1. Provide `CONTEXT.md` for background
2. Provide the sprint's MD file for tasks
3. The agent has everything it needs — file paths, line numbers, data structures, done-when criteria

---

## Abort Conditions

The literature review identified conditions where certain sprints can be deprioritised:

| Condition | Action |
|-----------|--------|
| TS/JS tool extraction recall is already high | Demote Sprint 1 |
| Agent repo fits under 80K chars | Defer Sprint 5 |
| Langfuse trace volume is low (<50 conversations) | Defer Sprint 7 until traces accumulate |
| Guardrails enforced in code (hooks), not prompts | Weight Sprint 4 above Sprint 6 |
| No TS/JS in the agent codebase | Skip Sprint 1, proceed directly to Sprint 2 |
