# Sprint E3 — Interaction & Transition Coverage

## Goal

Replace the flat per-tool invocation counts (critical=25x, high=15x, medium=10x, low=5x) with a principled budget allocated to: (a) a t-way covering array over high/critical tool combinations and their key parameter values, and (b) transition-pair and round-trip coverage of the FSM. Per-tool repetition reduces to a small floor (3x) for stochastic variation.

**Literature**: NIST's empirical interaction rule shows ~67% of faults from single factors, ~93% from 2-way, ~98% from 3-way, and 100% by 6-way (Kuhn, Wallace & Gallo, IEEE TSE 2004). Round-trip/transition-tree coverage is a validated cost-effective middle ground for FSM testing (Binder; Utting & Legeard).

## Tasks

### E3.1 Covering Array Generator

**File**: `src/coverage/interaction.py` (new file)

- [ ] Implement `generate_covering_array(factors: list[dict], strength: int = 2) -> list[dict]`:
  - `factors` = list of `{name: str, levels: list[str]}` representing tools and their key parameter values
  - `strength` = t-way interaction strength (default 2 = pairwise)
  - Uses IPOG algorithm (In-Parameter-Order-General) or a greedy covering array construction
  - Returns list of test configurations, each mapping factor → level

  Example:
  ```python
  factors = [
      {"name": "tool", "levels": ["check_order", "process_refund", "escalate"]},
      {"name": "order_age", "levels": ["<30_days", ">30_days"]},
      {"name": "amount", "levels": ["<$100", ">$100", ">$500"]},
  ]
  # 2-way covering array: every pair of factor-levels appears in at least one row
  ```

- [ ] Implement `extract_factors_from_agent_map(agent_map: dict) -> list[dict]`:
  - Extract high/critical tools as one factor (tool selection)
  - For each tool with parameters, extract key parameter values as factors
  - Use preconditions to derive boundary values (e.g., "amount must not be None" → levels: [None, valid_amount])
  - Cap at 10 factors (manageable covering array size)

### E3.2 FSM Transition Coverage

**File**: `src/coverage/transition.py` (new file)

- [ ] Implement `compute_transition_pairs(fsm: dict) -> list[tuple[str, str, str, str]]`:
  - From `agent_map["behavioural_model"]["fsm"]`
  - Generate all transition pairs (1-switch coverage): for each pair of consecutive transitions (T1, T2) where T1.to_state == T2.from_state, create a test that exercises both
  - Returns list of `(state_A, trigger_1, state_B, trigger_2)` tuples

- [ ] Implement `compute_round_trip_paths(fsm: dict) -> list[list[str]]`:
  - Find all paths from initial state back to initial state (or to terminal state)
  - Cap at 20 paths (avoid combinatorial explosion)
  - Prioritise paths through high-risk tools

- [ ] Implement `compute_all_transitions(fsm: dict) -> list[tuple[str, str, str]]`:
  - Simpler: every transition exercised at least once
  - Returns list of `(from_state, trigger, to_state)`

### E3.3 Replace B1 Calculator

**File**: `src/coverage/calculator.py`

- [ ] Refactor `calculate_coverage_goals()`:
  ```python
  def calculate_coverage_goals(agent_map: dict) -> CoverageGoals:
      tools = agent_map["components"]["tools"]
      bm = agent_map.get("behavioural_model", {})
      fsm = bm.get("fsm")

      # --- Interaction coverage (replaces flat counts) ---
      factors = extract_factors_from_agent_map(agent_map)
      if factors and len(factors) >= 2:
          covering_array = generate_covering_array(factors, strength=2)
          tool_combinations = covering_array  # Each row is a test config
      else:
          # Fallback to existing pairwise combos
          tool_combinations = _legacy_tool_combinations(tools)

      # --- Transition coverage (if FSM available) ---
      transition_targets = []
      if fsm and fsm.get("transitions"):
          transition_targets = compute_all_transitions(fsm)
          # Add transition pairs for deeper coverage if budget allows
          if len(transition_targets) < 50:
              transition_targets += compute_transition_pairs(fsm)

      # --- Per-tool floor (reduced from 25x to 3x) ---
      min_invocations = {}
      for tool in tools:
          risk = tool.get("risk_level", "low")
          floor = {"critical": 3, "high": 3, "medium": 2, "low": 1}.get(risk, 1)
          min_invocations[tool["name"]] = floor

      return CoverageGoals(
          tool_coverage=ToolCoverageGoals(
              min_invocations_per_tool=min_invocations,
              tool_combinations=tool_combinations,
              interaction_strength=2,
          ),
          transition_coverage=transition_targets,
          # ... edge case and stressor unchanged
      )
  ```

### E3.4 Update Coverage Models

**File**: `src/coverage/models.py`

- [ ] Add fields to `ToolCoverageGoals`:
  ```python
  interaction_strength: int = 2          # t-way coverage strength
  covering_array: list[dict] = field(default_factory=list)  # Generated test configs
  ```

- [ ] Add `TransitionCoverageGoals` dataclass:
  ```python
  @dataclass
  class TransitionCoverageGoals:
      all_transitions: list[tuple[str, str, str]]       # (from, trigger, to)
      transition_pairs: list[tuple]                       # 1-switch pairs
      round_trip_paths: list[list[str]]                  # Full paths
  ```

- [ ] Add `transition_coverage: TransitionCoverageGoals | None` to `CoverageGoals`

### E3.5 Update B4 Allocation

**File**: `src/generator/test_suite.py`

- [ ] Modify Phase 1 (Tool Coverage):
  - Instead of `for tool in min_invocations: repeat N times`:
  - Iterate covering array rows → each row = one test case exercising that combination
  - Per-tool floor (3x) as a minimum guarantee

- [ ] Add new Phase 1.5 (Transition Coverage):
  - For each transition target, find a scenario that exercises that transition's trigger tool
  - Create test case with coverage_goal="transition_coverage"

## Files Created/Modified

| File | Changes |
|------|---------|
| `src/coverage/interaction.py` | **New file**: covering array generator, factor extraction |
| `src/coverage/transition.py` | **New file**: FSM transition-pair/round-trip coverage |
| `src/coverage/calculator.py` | Refactored to use interaction + transition coverage |
| `src/coverage/models.py` | New TransitionCoverageGoals, updated ToolCoverageGoals |
| `src/generator/test_suite.py` | Updated Phase 1 + new Phase 1.5 |

## Done When

- Covering array generated from tool × parameter factors at strength 2
- FSM transitions covered by at least one test each
- Per-tool repetition reduced to 3x floor (from 25x)
- Total test count is equal or lower than before, but interaction coverage is higher
- Measurement harness (E12) shows equal or better fault detection at lower test budget
