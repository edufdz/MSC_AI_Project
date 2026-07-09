# Sprint E-T — End-to-End Testing & Validation for Phase B Enhancements

## Goal

Verify that all Phase B enhancements (E1–E12) work correctly, both individually and together. Create unit tests per new module, integration tests for the full enhanced pipeline, regression tests ensuring the baseline still works, and validation tests confirming the enhanced suite is measurably richer than the original.

**Runs after**: All other sprints are complete (or incrementally after each sprint lands).

## Test Architecture

```
tests/
├── phase_b/
│   ├── fixtures/                              # Pre-built agent maps for testing
│   │   ├── samsung_agent_map.json             # Real Samsung WhatsApp agent map (from Phase A)
│   │   ├── python_agent_map.json              # Simple Python agent map (from Phase A fixtures)
│   │   ├── mock_trace_result.json             # Simulated Langfuse trace data with failures
│   │   └── mock_production_signals.json       # Simulated production failure signals
│   │
│   ├── unit/                                  # Per-module unit tests
│   │   ├── test_measurement_harness.py        # E12
│   │   ├── test_seed_corpus.py                # E1
│   │   ├── test_oracles.py                    # E4
│   │   ├── test_policy_graph.py               # E2
│   │   ├── test_interaction_coverage.py       # E3
│   │   ├── test_adversarial.py                # E5
│   │   ├── test_guardrail_pairs.py            # E11
│   │   ├── test_trace_grounding.py            # E6
│   │   ├── test_quality_diversity.py          # E7
│   │   └── test_prioritiser.py                # E8
│   │
│   ├── integration/                           # Full pipeline tests
│   │   ├── test_enhanced_pipeline.py          # Full B1–B4 with all enhancements
│   │   ├── test_baseline_regression.py        # Original pipeline still works
│   │   └── test_suite_schema.py               # Output schema validation
│   │
│   └── validation/                            # Enhancement impact measurement
│       ├── test_enrichment_comparison.py       # Enhanced vs baseline comparison
│       └── test_phase_c_consumption.py         # Phase C can read enhanced output
```

## Tasks

### E-T.1 Create Test Fixtures

#### E-T.1.1 Agent Map Fixtures

- [ ] Copy `samsung_whatsapp_map.json` (from Phase A run) into `tests/phase_b/fixtures/`
- [ ] Generate `python_agent_map.json` by running Phase A on `tests/phase_a/fixtures/python_agent/`
- [ ] Both must include all enhanced fields: guardrails, behavioural_model, preconditions, postconditions, side_effects, taint_flows, taxonomy_ids

#### E-T.1.2 Mock Trace Data

- [ ] Create `tests/phase_b/fixtures/mock_trace_result.json`:
  ```python
  # Simulated TraceAnalysisResult with:
  # - 20 conversations (10 success, 5 escalation, 3 timeout, 2 loop)
  # - tool_frequency for 6 tools
  # - 8 common_sequences (bigrams)
  # - 5 failure_patterns
  # - 2 tools_not_in_static, 1 tools_not_in_traces
  ```

- [ ] Create helper `tests/phase_b/fixtures/helpers.py`:
  ```python
  def load_agent_map(name="samsung") -> dict
  def load_mock_traces() -> MockTraceResult
  def load_mock_production_signals() -> list[ProductionSignal]
  ```

#### E-T.1.3 Mock Production Signals

- [ ] Create `tests/phase_b/fixtures/mock_production_signals.json`:
  - 10 production signals across 5 failure categories
  - Mapped to specific tools and guardrail rule IDs
  - Mix of escalation, complaint, qa_flag sources

### E-T.2 Unit Tests — Measurement Harness (E12)

**File**: `tests/phase_b/unit/test_measurement_harness.py`

- [ ] `TestFailureTaxonomy`:
  - All FailureCategory enum values exist
  - Severity weights are assigned

- [ ] `TestAPFD`:
  - Known test order + fault matrix → correct APFD value
  - Perfect ordering → APFD close to 1.0
  - Worst ordering → APFD close to 0.0
  - Weighted APFD weights critical faults higher
  - compare_orderings returns correct delta

- [ ] `TestPredictiveValidity`:
  - Precision: 3 synthetic failures, 2 match production → precision = 0.67
  - Recall: 5 production signals, 3 covered by synthetic → recall = 0.60
  - F1 computed correctly
  - Empty inputs → zero metrics (no crash)

- [ ] `TestDiversity`:
  - Suite with all same persona → low diversity
  - Suite with varied personas → high diversity
  - Tool-pair coverage computed correctly

- [ ] `TestMutationOperators`:
  - REMOVE_GUARDRAIL produces agent_map with one fewer rule
  - SWAP_TOOL produces agent_map with a different tool name
  - Each mutant differs from original in exactly one way

### E-T.3 Unit Tests — Production Seeds (E1)

**File**: `tests/phase_b/unit/test_seed_corpus.py`

- [ ] `TestTraceToSeed`:
  - Failed conversation → FailureSeed with correct category
  - Escalation trace → ESCALATION_FAILURE category
  - Repeated tool 3x → INFINITE_LOOP category
  - Short conversation → PREMATURE_EXIT category
  - Successful conversation → filtered out (not a seed)

- [ ] `TestSeedToScenario`:
  - FailureSeed → valid Scenario with source="production_seed"
  - required_tools matches seed.tool_sequence
  - type is "error_path"

- [ ] `TestSeedMutation`:
  - "swap_persona" changes persona traits but keeps tool sequence
  - "perturb_tool_arg" changes tool args but keeps sequence
  - "adjacent_tool" replaces one tool with a dependency neighbour
  - "change_language" switches between Spanish/English
  - Each mutation produces a valid FailureSeed

- [ ] `TestCorpusExpansion`:
  - 3 seeds × 3 mutations = 9 expanded scenarios (+ 3 originals = 12)
  - All expanded scenarios are valid Scenario objects

### E-T.4 Unit Tests — Non-LLM Oracles (E4)

**File**: `tests/phase_b/unit/test_oracles.py`

- [ ] `TestOracleGeneration`:
  - Tool with postconditions → POSTCONDITION oracles generated
  - Guardrail rule → GUARDRAIL_COMPLIANCE + GUARDRAIL_VIOLATION oracles
  - Taint flow → TAINT_FLOW oracle
  - Side-effect tool → SIDE_EFFECT oracle
  - Dependency edge → TOOL_SEQUENCE oracle
  - Tool with no postconditions → no POSTCONDITION oracles (but still gets guardrail oracles)

- [ ] `TestMetamorphicRelations`:
  - Language mismatch in agent_map → language-invariance relation generated
  - Spanish formality detected → formality-invariance relation generated
  - No mismatch → no language relations (still generates synonym relations)

- [ ] `TestOracleAttachment`:
  - Scenario with required_tools → gets oracles for those tools
  - All scenarios get guardrail oracles
  - Oracle count > 0 for every scenario

### E-T.5 Unit Tests — Policy Graph (E2)

**File**: `tests/phase_b/unit/test_policy_graph.py`

- [ ] `TestGraphConstruction`:
  - 5 guardrail rules → 5 graph nodes
  - Rules with shared target_tools → edge between them
  - Node weights match rule complexity

- [ ] `TestRandomWalk`:
  - Walk with max_complexity=5 → total complexity ≤ 5
  - Walk with walk_length=3 → at most 3 nodes
  - 10 walks → at least 5 distinct rule combinations (diversity check)
  - Walk stops at complexity budget

- [ ] `TestWalkToScenario`:
  - Walk with prohibition rule → type="error_path"
  - Walk with 2 rules → required_tools is union of both rules' target_tools
  - Walk total_complexity > 10 → difficulty="hard"
  - Source is "policy_graph"

### E-T.6 Unit Tests — Interaction Coverage (E3)

**File**: `tests/phase_b/unit/test_interaction_coverage.py`

- [ ] `TestCoveringArray`:
  - 3 factors × 2 levels each at strength 2 → all 2-way pairs covered
  - Verify: every pair of (factor_i=level_a, factor_j=level_b) appears in at least one row
  - Array size ≤ theoretical upper bound

- [ ] `TestFactorExtraction`:
  - Agent map with 3 critical tools → tool factor with 3 levels
  - Tool with 2 parameters → parameter factors extracted
  - Preconditions → boundary value levels

- [ ] `TestTransitionCoverage`:
  - FSM with 5 transitions → all 5 in all_transitions
  - FSM with A→B→C → transition pair (A→B, B→C) generated
  - No FSM → empty transition coverage (no crash)

- [ ] `TestReducedRepetition`:
  - Critical tool min_invocations = 3 (not 25)
  - Total test count lower than baseline at equal fault coverage

### E-T.7 Unit Tests — Adversarial Generation (E5)

**File**: `tests/phase_b/unit/test_adversarial.py`

- [ ] `TestAttackTemplates`:
  - LLM01 templates exist and have pattern field
  - LLM02 templates have pii_variants
  - All taxonomy IDs in ATTACK_TEMPLATES are valid OWASP/MITRE IDs

- [ ] `TestTaintFlowAttacks`:
  - Agent map with 2 taint flows → 2 adversarial scenarios
  - Each has oracle_type=TAINT_FLOW
  - Source is "adversarial_taint"

- [ ] `TestTaxonomyAttacks`:
  - Agent map with LLM02 risk → generates PII extraction scenario
  - Agent map with LLM06 risk → generates excessive agency scenario
  - Scenarios are in conversation language (Spanish for Samsung)

- [ ] `TestAdversarialPersonas`:
  - LLM01 taxonomy → "Social Engineer" persona with tests_boundaries=true
  - LLM02 taxonomy → "Data Extractor" persona
  - Source is "adversarial"

### E-T.8 Unit Tests — Guardrail Pairs (E11)

**File**: `tests/phase_b/unit/test_guardrail_pairs.py`

- [ ] `TestPairGeneration`:
  - 5 rules → at least 10 scenarios (1 compliance + 1 violation each)
  - Complexity-3 rule → 4 scenarios (2 compliance + 2 violation)
  - Compliance test has type="happy_path"
  - Violation test has type="error_path"

- [ ] `TestLanguageMismatch`:
  - English rules + Spanish conversation → provocations in Spanish
  - Tags include "language_mismatch"

- [ ] `TestLanguageInvariance`:
  - Metamorphic relation generated for each compliance test
  - Invariant is "tool_calls_equal" or "policy_outcome_equal"

- [ ] `TestConditionalRules`:
  - Rule with scope="conditional" → test with condition met + test without

### E-T.9 Unit Tests — Production Personas (E6)

**File**: `tests/phase_b/unit/test_trace_grounding.py`

- [ ] `TestTraitAnalysis`:
  - Long messages → high verbosity score
  - Many emojis → emoji_use="frequent"
  - Usted usage → formality="formal"
  - Fast escalation → low patience

- [ ] `TestDistributionFitting`:
  - 20 conversations → mean/std for each trait dimension
  - Sampled personas fall within observed distribution range

- [ ] `TestProductionPersonas`:
  - Source is "production_grounded"
  - Traits are within fitted distribution (not extreme outliers)

### E-T.10 Unit Tests — Quality Diversity (E7)

**File**: `tests/phase_b/unit/test_quality_diversity.py`

- [ ] `TestMAPElites`:
  - Archive starts empty → coverage = 0.0
  - Add 10 diverse personas → coverage > 0.0
  - Add duplicate persona to occupied cell → kept only if higher quality
  - select_diverse(5) returns 5 personas from different cells

- [ ] `TestVsCosineDedup`:
  - 20 personas through MAP-Elites → higher coverage than through cosine dedup
  - No duplicate personas in same cell

### E-T.11 Unit Tests — Prioritisation (E8)

**File**: `tests/phase_b/unit/test_prioritiser.py`

- [ ] `TestFaultProneness`:
  - Test with critical tools → higher score than test with low tools
  - Test with failure-pattern tools → boosted score
  - Test with more oracles → higher score

- [ ] `TestGreedyOrdering`:
  - 10 tests → ordered list of 10 tests
  - First test has highest individual fault-proneness
  - Subsequent tests add marginal coverage (not just highest score)

- [ ] `TestVsFixedPhase`:
  - At equal budget, greedy ordering covers more tool-pairs than fixed 4-phase
  - APFD of greedy ordering ≥ APFD of fixed ordering

### E-T.12 Integration Tests

#### E-T.12.1 Full Enhanced Pipeline

**File**: `tests/phase_b/integration/test_enhanced_pipeline.py`

- [ ] Run full B1–B4 against Samsung agent map with all enhancements enabled (skip_ai=True):
  - Assert: test_suite.json is valid JSON
  - Assert: total_tests > 0
  - Assert: scenarios include source="policy_graph"
  - Assert: scenarios include source="guardrail_compliance" and "guardrail_violation"
  - Assert: test cases have oracles attached
  - Assert: coverage_goals use interaction coverage (min_invocations ≤ 3 per tool, not 25)
  - Assert: behavioural_model coverage_targets consumed
  - Assert: APFD reported

- [ ] Run with mock traces:
  - Assert: scenarios include source="production_seed"
  - Assert: personas include source="production_grounded"
  - Assert: seed scenarios appear in Phase 0 allocation

- [ ] Run with adversarial enabled:
  - Assert: scenarios include source="adversarial_taint" or "adversarial_taxonomy"
  - Assert: every taxonomy_id in risk_flags has at least one adversarial test

#### E-T.12.2 Baseline Regression

**File**: `tests/phase_b/integration/test_baseline_regression.py`

- [ ] Run original pipeline (no enhancements, skip_ai=True):
  - Assert: still produces valid test_suite.json
  - Assert: tool_coverage tests present
  - Assert: edge_case tests present
  - Assert: no crash from missing enhanced fields

- [ ] Run with minimal agent_map (no guardrails, no behavioural_model, no traces):
  - Assert: graceful degradation — enhanced generators produce empty lists, not crashes
  - Assert: base pipeline still fills test budget

#### E-T.12.3 Output Schema Validation

**File**: `tests/phase_b/integration/test_suite_schema.py`

- [ ] Validate test_suite.json has all expected fields:
  - test_cases[].oracles (list, can be empty)
  - test_cases[].coverage_goal includes new goals: "production_seed", "transition_coverage", "adversarial", "guardrail_compliance"
  - summary.by_coverage_goal includes new categories
  - summary.tool_invocation_counts ≤ old counts (interaction coverage reduces repetition)

- [ ] Validate persona_library.json:
  - personas[].source includes new sources: "production_grounded", "adversarial"

- [ ] Validate scenario_catalog.json:
  - scenarios[].source includes: "policy_graph", "production_seed", "guardrail_compliance", "guardrail_violation", "adversarial_taint", "adversarial_taxonomy"
  - scenarios[].oracles field present

### E-T.13 Validation Tests

#### E-T.13.1 Enrichment Comparison

**File**: `tests/phase_b/validation/test_enrichment_comparison.py`

- [ ] Generate test suite **without** enhancements (baseline)
- [ ] Generate test suite **with** all enhancements
- [ ] Compare:
  - [ ] Enhanced suite has more scenario sources (baseline: 3-4, enhanced: 8+)
  - [ ] Enhanced suite has oracles attached (baseline: 0)
  - [ ] Enhanced suite has lower per-tool repetition but higher interaction coverage
  - [ ] Enhanced suite covers more guardrail rules (baseline: 0, enhanced: all rules)
  - [ ] Enhanced suite has adversarial scenarios (baseline: only "adversarial" variant type)
  - [ ] Enhanced diversity score ≥ baseline diversity score
  - [ ] Enhanced APFD ≥ baseline APFD

#### E-T.13.2 Phase C Consumption

**File**: `tests/phase_b/validation/test_phase_c_consumption.py`

- [ ] Load enhanced test_suite.json
- [ ] Assert: Phase C executor can read all test cases without crash
- [ ] Assert: Phase C can read oracle definitions
- [ ] Assert: new fields are ignored gracefully by unmodified Phase C code

### E-T.14 Performance

- [ ] Enhanced pipeline on Samsung agent map completes in < 60 seconds (skip_ai=True)
- [ ] Enhanced pipeline on Python agent map completes in < 30 seconds (skip_ai=True)
- [ ] Covering array generation for 10 factors × 3 levels completes in < 5 seconds
- [ ] Policy-graph walk sampling (20 walks) completes in < 1 second
- [ ] MAP-Elites archive insertion of 100 personas completes in < 1 second

## Files Created

| File | Purpose |
|------|---------|
| `tests/phase_b/__init__.py` | Package init |
| `tests/phase_b/fixtures/helpers.py` | Fixture loading utilities |
| `tests/phase_b/fixtures/mock_trace_result.json` | Simulated trace data |
| `tests/phase_b/fixtures/mock_production_signals.json` | Simulated production signals |
| `tests/phase_b/unit/test_measurement_harness.py` | E12 unit tests |
| `tests/phase_b/unit/test_seed_corpus.py` | E1 unit tests |
| `tests/phase_b/unit/test_oracles.py` | E4 unit tests |
| `tests/phase_b/unit/test_policy_graph.py` | E2 unit tests |
| `tests/phase_b/unit/test_interaction_coverage.py` | E3 unit tests |
| `tests/phase_b/unit/test_adversarial.py` | E5 unit tests |
| `tests/phase_b/unit/test_guardrail_pairs.py` | E11 unit tests |
| `tests/phase_b/unit/test_trace_grounding.py` | E6 unit tests |
| `tests/phase_b/unit/test_quality_diversity.py` | E7 unit tests |
| `tests/phase_b/unit/test_prioritiser.py` | E8 unit tests |
| `tests/phase_b/integration/test_enhanced_pipeline.py` | Full pipeline integration |
| `tests/phase_b/integration/test_baseline_regression.py` | Baseline regression |
| `tests/phase_b/integration/test_suite_schema.py` | Schema validation |
| `tests/phase_b/validation/test_enrichment_comparison.py` | Enhanced vs baseline |
| `tests/phase_b/validation/test_phase_c_consumption.py` | Phase C compatibility |

## Done When

- All unit tests pass for each enhancement module
- Integration tests pass with Samsung agent map
- Baseline regression passes without enhancements
- Enrichment comparison demonstrates measurable improvement
- Performance targets met
- Phase C can consume enhanced output

## Running Tests

```bash
# Run all Phase B tests
pytest tests/phase_b/ -v

# Run only unit tests
pytest tests/phase_b/unit/ -v

# Run only integration tests
pytest tests/phase_b/integration/ -v

# Run specific enhancement tests
pytest tests/phase_b/unit/test_seed_corpus.py -v          # E1
pytest tests/phase_b/unit/test_measurement_harness.py -v   # E12

# Run with coverage
pytest tests/phase_b/ --cov=src --cov-report=term-missing
```
