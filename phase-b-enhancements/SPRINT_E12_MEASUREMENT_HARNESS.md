# Sprint E12 — Suite-Quality Measurement Harness

## Goal

Build the measurement infrastructure that every other enhancement is judged against. Without this, no enhancement can demonstrate improved predictive validity — the methodological core of the dissertation. The harness computes: (i) fault-detection rate against a shared failure taxonomy, (ii) precision/recall of synthetic failures vs independent production signals, (iii) behaviour-space diversity (archive coverage), and (iv) mutation score against seeded agent faults.

**Must run first**: all other sprints depend on this to prove their value.

## Why This Matters

Just et al. (FSE 2014) found "a statistically significant correlation between mutant detection and real fault detection, independently of code coverage" over 357 real faults. Without a measurement harness, the project cannot demonstrate that any change to Phase B improved real-world test quality.

## Tasks

### E12.1 Define the Shared Failure Taxonomy

**File**: `src/evaluation/taxonomy.py` (new file)

- [ ] Define the failure taxonomy as an enum/dataclass:
  ```python
  class FailureCategory(str, Enum):
      WRONG_TOOL = "wrong_tool"                    # Agent called the wrong tool
      MISSED_TOOL = "missed_tool"                  # Agent should have called a tool but didn't
      HALLUCINATION = "hallucination"               # Agent fabricated information
      PII_LEAK = "pii_leak"                        # Agent disclosed PII
      GUARDRAIL_VIOLATION = "guardrail_violation"   # Agent violated a numbered policy rule
      EXCESSIVE_AGENCY = "excessive_agency"         # Agent took action without confirmation
      ESCALATION_FAILURE = "escalation_failure"     # Agent failed to escalate when it should have
      LANGUAGE_ERROR = "language_error"              # Agent responded in wrong language
      TOOL_MISUSE = "tool_misuse"                  # Agent called tool with wrong/dangerous args
      INFINITE_LOOP = "infinite_loop"               # Agent stuck in a loop
      PREMATURE_EXIT = "premature_exit"             # Agent ended conversation prematurely
      STYLE_VIOLATION = "style_violation"           # Agent violated style guide (tone, length)
  ```
- [ ] Map each category to OWASP/MITRE taxonomy IDs from Phase A
- [ ] Define severity weights: critical=4, high=3, medium=2, low=1

### E12.2 APFD Calculator

**File**: `src/evaluation/apfd.py` (new file)

- [ ] Implement `calculate_apfd(test_order: list[str], fault_detection_matrix: dict[str, set[str]]) -> float`:
  - Average Percentage of Faults Detected (Rothermel et al.)
  - `APFD = 1 - (sum of first-detection positions) / (n_tests × n_faults) + 1/(2 × n_tests)`
  - Higher is better (1.0 = every fault detected by first test)

- [ ] Implement `calculate_weighted_apfd(test_order, fault_matrix, fault_weights) -> float`:
  - Weight by failure severity (critical faults weighted higher)

- [ ] Implement `compare_orderings(ordering_a, ordering_b, fault_matrix) -> dict`:
  - Returns APFD for both, delta, and which ordering wins

### E12.3 Precision/Recall Against Production Signals

**File**: `src/evaluation/predictive_validity.py` (new file)

- [ ] Define `ProductionSignal` dataclass:
  ```python
  @dataclass
  class ProductionSignal:
      signal_id: str
      trace_id: str                    # Langfuse trace ID
      failure_category: FailureCategory
      description: str
      tool_involved: str | None
      guardrail_rule_id: str | None    # R001, R002, etc.
      timestamp: datetime
      source: str                      # "escalation", "complaint", "qa_flag", "human_label"
  ```

- [ ] Implement `compute_predictive_validity(synthetic_failures: list[dict], production_signals: list[ProductionSignal]) -> dict`:
  - **Precision**: of synthetic failures flagged, what fraction match a real production signal?
  - **Recall**: of real production signals, what fraction are covered by at least one synthetic test?
  - Matching: same failure_category + same tool_involved (or same guardrail_rule_id)
  - Returns: `{precision, recall, f1, matched_signals, unmatched_signals, false_positives}`

- [ ] Implement `load_production_signals(trace_result, agent_map) -> list[ProductionSignal]`:
  - Convert Langfuse failure_patterns into ProductionSignal objects
  - Convert escalation traces into ProductionSignal(source="escalation")
  - Map tool sequences that ended in failure to FailureCategory

### E12.4 Behaviour-Space Diversity Metric

**File**: `src/evaluation/diversity.py` (new file)

- [ ] Implement `compute_suite_diversity(test_suite: TestSuite) -> dict`:
  - **Trait-space coverage**: divide the 10-D persona trait space into cells (low/mid/high per trait = 3^10 cells), count filled cells / total cells
  - **Scenario-type coverage**: fraction of scenario types (happy_path, error_path, edge_case) × variant types represented
  - **Tool-pair coverage**: fraction of all tool pairs exercised by at least one test
  - **Archetype coverage**: fraction of persona archetypes used
  - Returns: `{trait_coverage, scenario_coverage, tool_pair_coverage, archetype_coverage, overall_diversity}`

### E12.5 Mutation Score Calculator

**File**: `src/evaluation/mutation.py` (new file)

- [ ] Define agent mutation operators:
  ```python
  class MutationOperator(str, Enum):
      REMOVE_GUARDRAIL = "remove_guardrail"       # Delete one guardrail rule from prompt
      SWAP_TOOL = "swap_tool"                      # Replace one tool call with another
      REMOVE_ESCALATION = "remove_escalation"      # Remove escalation trigger
      INJECT_PII = "inject_pii"                    # Add PII to a tool response
      WRONG_LANGUAGE = "wrong_language"             # Force response in wrong language
      REMOVE_CONFIRMATION = "remove_confirmation"   # Skip confirmation gate
      TRUNCATE_CONTEXT = "truncate_context"         # Cut conversation history
  ```

- [ ] Implement `generate_mutants(agent_map: dict, operators: list[MutationOperator]) -> list[dict]`:
  - Each mutant is a modified agent_map (one mutation applied)
  - Returns list of `{mutant_id, operator, description, modified_agent_map}`

- [ ] Implement `compute_mutation_score(test_suite, mutants, execution_results) -> float`:
  - `mutation_score = killed_mutants / total_mutants`
  - A mutant is "killed" if at least one test case detects the mutation (different outcome on mutant vs original)

### E12.6 Harness CLI Integration

**File**: `src/evaluation/harness.py` (new file)

- [ ] Implement `evaluate_suite(test_suite, agent_map, production_signals=None, trace_result=None) -> dict`:
  - Calls all metrics: APFD, diversity, predictive validity (if signals available)
  - Returns comprehensive quality report

- [ ] Add `--evaluate` flag to `generate_tests.py`:
  - After generating the test suite, run the harness and print results
  - Save evaluation report to `evaluation_report.json`

## Files Created

| File | Purpose |
|------|---------|
| `src/evaluation/__init__.py` | Package init |
| `src/evaluation/taxonomy.py` | Shared failure taxonomy enum |
| `src/evaluation/apfd.py` | Average Percentage of Faults Detected |
| `src/evaluation/predictive_validity.py` | Precision/recall vs production |
| `src/evaluation/diversity.py` | Behaviour-space diversity metrics |
| `src/evaluation/mutation.py` | Agent mutation operators and score |
| `src/evaluation/harness.py` | Unified evaluation harness |

## Done When

- APFD calculator produces correct values on synthetic examples
- Diversity metric reports trait, scenario, tool-pair, and archetype coverage
- Predictive validity computes precision/recall when given production signals
- Mutation operators generate valid agent_map mutants
- `--evaluate` flag produces a JSON evaluation report
- Baseline APFD and diversity computed for the current (unenhanced) test suite

## Validation

```bash
# Run Phase B with evaluation
python generate_tests.py /path/to/agent_map.json --skip-ai --evaluate -o output/

# Check evaluation report
cat output/evaluation_report.json
```
