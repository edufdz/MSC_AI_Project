# Sprint E8 — APFD & Frequency-Weighted Prioritisation

## Goal

Replace the fixed 4-phase allocation with a greedy prioritiser that orders tests to maximise marginal predicted failure coverage, weighted by `trace_analysis.tool_frequency` and `failure_patterns` (operational profile) and by risk. Report APFD against the real-failure taxonomy as the suite-quality metric.

**Literature**: APFD is the standard prioritisation objective (Rothermel et al.; Elbaum et al.). Operational-profile testing finds field-relevant faults first (Musa, IEEE Software 1993). Combining fault-proneness with coverage improves prioritisation.

## Tasks

### E8.1 Fault-Proneness Estimator

**File**: `src/generator/prioritiser.py` (new file)

- [ ] Implement `estimate_fault_proneness(test_case: TestCase, agent_map: dict, trace_result=None) -> float`:
  - **Risk weight**: sum of risk_levels of required_tools (critical=4, high=3, medium=2, low=1)
  - **Trace frequency weight**: if trace_result available, weight by inverse of tool_frequency (rarely-called tools are more fault-prone because less exercised)
  - **Failure history weight**: if tool appears in failure_patterns, boost by 2x
  - **Oracle density**: number of oracles attached (more oracles = more chances to detect faults)
  - **Novelty weight**: how many new tool-pairs does this test cover that previous tests haven't?
  - Returns combined score (higher = test earlier)

### E8.2 Greedy APFD-Maximising Ordering

**File**: `src/generator/prioritiser.py`

- [ ] Implement `prioritise_suite(test_cases: list[TestCase], agent_map, trace_result=None) -> list[TestCase]`:
  1. Compute fault-proneness for each test
  2. Greedy selection: pick the test with highest marginal coverage gain
     - "Marginal coverage": new tools, new tool-pairs, new taxonomy categories covered by this test but not by previously selected tests
  3. Weighted by fault-proneness score
  4. Return reordered list

### E8.3 Budget Optimiser (replaces fixed 4-phase)

**File**: `src/generator/test_suite.py`

- [ ] Refactor `generate()` to use prioritisation:
  ```python
  def generate(self, target_count=250) -> TestSuite:
      # 1. Generate ALL candidate tests from all sources
      candidates = []
      candidates += self._tool_coverage_candidates()
      candidates += self._interaction_coverage_candidates()   # E3
      candidates += self._transition_coverage_candidates()     # E3
      candidates += self._production_seed_candidates()         # E1
      candidates += self._guardrail_pair_candidates()          # E11
      candidates += self._adversarial_candidates()             # E5
      candidates += self._edge_case_candidates()
      candidates += self._stressor_candidates()
      candidates += self._scenario_fill_candidates()
      
      # 2. Prioritise all candidates by marginal fault coverage
      ordered = prioritise_suite(candidates, self.agent_map, self.trace_result)
      
      # 3. Take top target_count
      test_cases = ordered[:target_count]
      
      # 4. Renumber and build summary
      ...
  ```

### E8.4 APFD Reporting

**File**: `generate_tests.py`

- [ ] After test generation, compute and display:
  ```python
  from src.evaluation.apfd import calculate_apfd
  # Estimated APFD based on fault-proneness (proxy for real faults)
  apfd = calculate_apfd(test_order, estimated_fault_matrix)
  console.print(f"Estimated APFD: {apfd:.3f}")
  ```

## Files Created/Modified

| File | Changes |
|------|---------|
| `src/generator/prioritiser.py` | **New file**: fault-proneness estimator, greedy APFD ordering |
| `src/generator/test_suite.py` | Refactored to candidate-then-prioritise pattern |
| `generate_tests.py` | APFD reporting |

## Done When

- Test ordering maximises marginal fault coverage (not fixed-phase)
- Production trace frequency weights test priority (rarely-used tools tested first)
- Failure-pattern tools get priority boost
- APFD metric computed and reported
- At equal test budget, new ordering detects more estimated faults than fixed 4-phase
