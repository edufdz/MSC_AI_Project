# Phase B Enhancement Programme — Context

## What This Is

A series of evidence-based enhancements to **Phase B (Generate)** of the Agent-Testing Platform. Phase B takes the Agent Map produced by Phase A and generates a structured test suite (personas, scenarios, test cases) for Phase C to execute against the live agent.

## Why These Enhancements Exist

This work is part of an MSC AI research project. A literature review identified that **the current Phase B pipeline generates tests from the agent's structural surface (tools, risk levels) rather than from production failure patterns, policy interactions, and operational profiles**. The enhancements are grounded in peer-reviewed findings:

- **Soltani, Panichella & van Deursen (ICSE 2017)**: Field-failure-derived tests reproduce real failures and uncover failures that coverage-based generation misses (EvoCrash)
- **Just et al. (FSE 2014)**: Statistically significant correlation between mutant detection and real fault detection, independently of code coverage (357 real faults across 321 KLOC)
- **Kuhn, Wallace & Gallo (IEEE TSE 2004)**: ~67% of faults from single factors, ~93% from 2-way interactions, ~98% from 3-way; 4-to-6-way is "effectively exhaustive" (NIST interaction rule)
- **Levi & Kadar (ICML 2025)**: IntellAgent policy-graph weighted random walks achieve Pearson 0.98/0.92 correlation with tau-bench model rankings
- **Yao et al. (2024)**: tau-bench evaluates by database state comparison, not LLM judges; GPT-4o solves <50% of tasks at pass^1
- **Perez et al. (EMNLP 2022)**: Automated red-teaming with LMs uncovers tens of thousands of failures at scale
- **Debenedetti et al. (NeurIPS 2024)**: AgentDojo shows tool-using agents are vulnerable to injection; evaluates with state-based checks over 97 tasks
- **Musa (IEEE Software 1993)**: Operational-profile testing finds field-relevant faults first
- **Barr et al. (IEEE TSE 2015)**: Oracle problem survey — specified, derived, metamorphic, and pseudo-oracles avoid LLM judge circularity

## The Codebase

**Platform**: Agent-Testing Platform — end-to-end AI-powered platform for testing, debugging, and certifying conversational AI agents.

**Root directory**: `debugger-platforn/` (note the typo — intentional, do not rename)

**Phase B pipeline** (4 sequential stages):

```
agent_map.json → [B1 Coverage Config] → [B2 Persona Library] → [B3 Scenario Catalog] → [B4 Test Suite Assembly] → test_suite.json
```

### Key Source Files

| Module | Path | Purpose | LOC |
|--------|------|---------|-----|
| CLI entry | `generate_tests.py` | Click CLI, orchestrates B1–B4 | 422 |
| Coverage models | `src/coverage/models.py` | CoverageGoals, SandboxConfig, TestConfiguration dataclasses | 59 |
| Coverage calculator | `src/coverage/calculator.py` | Risk-based min invocations, sandbox mode, cost limits | 178 |
| Persona models | `src/personas/models.py` | PersonaTraits (10 numeric), PersonaStyle, PersonaEdgeBehaviors, Persona | 100 |
| Persona builder | `src/personas/builder.py` | Template, AI, tool-attack, flow-attack persona generation + cosine dedup | 776 |
| Persona templates | `src/personas/templates.py` | Pre-built personas by domain (support, sales, scheduling, etc.) | 605 |
| Persona metrics | `src/personas/metrics.py` | Trait coverage report, diversity score, archetype distribution | 98 |
| Persona affinity | `src/personas/affinity.py` | Weighted persona-scenario pairing score | 99 |
| Tlahuac adapter | `src/personas/tlahuac_adapter.py` | External persona/scenario loading + API client | 347 |
| Scenario models | `src/scenarios/models.py` | Scenario, ScenarioSuccessConditions, ChaosConfig, ScenarioCatalog | 62 |
| Scenario library | `src/scenarios/library.py` | Template, AI, variant scenario generation (5 offline types) | 658 |
| Scenario templates | `src/scenarios/templates.py` | Pre-built scenarios by domain | ~250 |
| Test suite models | `src/generator/models.py` | TestCase, TestSuiteSummary, TestSuite | 45 |
| Test suite generator | `src/generator/test_suite.py` | 4-phase allocation: tool-coverage → edge-case → stressor → fill | 331 |
| LLM config | `src/execution/llm_config.py` | Multi-provider LLM support (Anthropic, OpenAI, Groq, etc.) | 353 |

### Key Data Structures

**PersonaTraits** (10 numeric dimensions, 1–10 scale):
`patience, clarity, tech_savviness, politeness, verbosity, emotional_volatility, trust_level, detail_orientation, decision_speed, language_proficiency`

**PersonaStyle**: `tone` (polite/neutral/frustrated/angry), `formality` (formal/casual/slang), `typo_rate` (0.0–1.0), `abbreviation_use`, `emoji_use`

**PersonaEdgeBehaviors** (5 boolean flags): `rage_quits, changes_mind, provides_incomplete_info, asks_off_topic, tests_boundaries`

**Persona sources** (6 types): `template, ai_generated, custom, tlahuac, tool_attack, flow_attack`

**Scenario variant types** (5 offline + 7 AI): `ambiguity, missing_info, interruption, error, adversarial` (offline); + `constraint, multi_step` (AI)

**Test allocation phases** (4, fixed priority):
1. Tool coverage — min invocations per tool by risk (critical=25, high=15, medium=10, low=5)
2. Edge-case — variant-type allocation (ambiguity, missing_info, interruption, adversarial)
3. Stressor — chaos injection (timeout, malformed_response, data_conflict)
4. Scenario fill — pad to target count

### What Phase A Provides (Agent Map)

Phase B reads `agent_map.json` and uses:
- `components.tools[]` — tool inventory with risk_level, read_only, parameters, preconditions, postconditions, side_effects, state_modifying
- `metadata` — type, purpose, conversation_language, domain
- `risk_flags` — pii_handling, critical_actions, taint_flows, all_risks with taxonomy_ids
- `guardrails` — numbered policy rules with category, complexity, scope, target_tools, conditions
- `behavioural_model` — dependency graph (edges, bottlenecks, cycles, chains), FSM (states, transitions), coverage_targets
- `success_criteria` — cost/turn/latency limits
- `trace_analysis` — tool_frequency, common_sequences, failure_patterns (optional)
- `components.prompts[]` — system prompt content for context

### Current Limitations (what the sprints fix)

1. **B1 uses flat risk-based repetition** (`calculator.py`): 25x repetition of a critical tool finds almost nothing new after the first few calls; interaction coverage not used
2. **B2 personas are hand-authored trait vectors** (`builder.py`): not grounded in real user population; cosine dedup at 0.85 is a weak diversity mechanism
3. **B3 scenarios are structure-driven** (`library.py`): generated from tool surface and generic edge-case dimensions, not from production failures or policy interactions
4. **B4 allocation is fixed 4-phase** (`test_suite.py`): category-based allocation, not fault-detection-optimised prioritisation
5. **No production-failure seeding**: the pipeline doesn't use Langfuse failure traces to generate scenarios
6. **No non-LLM oracles**: success/failure conditions are strings, not executable postcondition/state checks
7. **No policy-graph scenario generation**: guardrail rules exist but aren't used for IntellAgent-style weighted random walks
8. **No adversarial generation from risk taxonomy**: OWASP/MITRE mappings and taint flows aren't used to generate targeted attack scenarios
9. **No measurement harness**: no way to measure if enhancements improve predictive validity

## Sprint Overview

| Sprint | Name | Tier | Effort | Key Literature |
|--------|------|------|--------|----------------|
| E12 | Measurement harness | 1 | Medium | Just et al. (FSE 2014), APFD |
| E1 | Production-failure seed corpus | 1 | Medium | EvoCrash (ICSE 2017), BugRedux, AFL |
| E4 | Non-LLM oracles from postconditions | 1 | Medium | tau-bench, Barr et al. (IEEE TSE 2015) |
| E2 | Policy-graph scenario generator | 1 | Medium | IntellAgent (ICML 2025) |
| E3 | Interaction & transition coverage | 1 | Medium | NIST interaction rule (IEEE TSE 2004) |
| E5 | Risk-guided adversarial generation | 1 | Medium | Perez et al. (EMNLP 2022), AgentDojo |
| E11 | Guardrail compliance/violation pairs | 3 | Small | Property-based testing, Segura et al. |
| E6 | Production-grounded personas | 2 | Medium | Gao et al., persona drift literature |
| E7 | Quality-diversity selection | 2 | Medium | MAP-Elites, DPP, Rainbow Teaming |
| E8 | APFD-weighted prioritisation | 2 | Medium | Rothermel et al., Musa (1993) |
| E9 | ALI-Agent iterative refinement | 3 | Large | ALI-Agent (NeurIPS 2024) |
| E10 | Principled chaos/stressor config | 3 | Medium | Chaos engineering, ReliabilityBench |

### Recommended Sprint Order

```
Week 1:  E12 (measurement harness) — nothing else can be judged without it
Week 1-2: E1 (production seeds) + E4 (non-LLM oracles) — highest predictive-validity payoff
Week 2:  E2 (policy-graph) + E3 (interaction coverage) — principled coverage replaces flat counts
Week 3:  E5 (adversarial) + E11 (guardrail pairs) — exploit Phase A risk/guardrail data
Backlog: E6 (grounded personas) + E7 (quality-diversity) + E8 (APFD prioritisation)
Defer:   E9 (iterative refinement) + E10 (principled chaos) — need Phase C execution loop
```

### Decision Thresholds

- If precision/recall does not improve after E1+E4 → bottleneck is ground-truth signal, not generation; shift to taxonomy/human-signal quality
- If interaction coverage (E3) does not beat flat repetition on seeded faults → agent faults are genuinely single-tool; keep flat counts for highest-risk tools only
