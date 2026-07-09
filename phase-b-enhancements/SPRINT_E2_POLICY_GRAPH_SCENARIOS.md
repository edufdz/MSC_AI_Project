# Sprint E2 — Policy-Graph Scenario Generator

## Goal

Build a scenario generator that constructs a policy graph from Phase A guardrail rules (nodes weighted by complexity) and dependency edges (weighted by trace co-occurrence), then samples scenarios by weighted random walks — IntellAgent-style. This produces diverse, naturalistic multi-policy scenarios that exercise realistic rule combinations, replacing the current structure-blind scenario generation.

**Literature**: IntellAgent (Levi & Kadar, ICML 2025) reports Pearson correlations of 0.98 (Airline) and 0.92 (Retail) with tau-bench across model rankings. tau-bench shows policy-following is where agents fail: GPT-4o solves <50% of tasks at pass^1 (Yao et al., 2024).

## Tasks

### E2.1 Build the Policy Graph

**File**: `src/scenarios/policy_graph.py` (new file)

- [ ] Implement `build_policy_graph(agent_map: dict) -> PolicyGraph`:
  1. **Nodes**: one per guardrail rule from `agent_map["guardrails"]["rules"]`
     - Weight = rule.complexity (1–5)
     - Category = rule.category (prohibition, requirement, constraint, escalation, fallback)
     - Target tools = rule.target_tools
  2. **Edges**: co-occurrence relationships between rules
     - From `guardrails.interactions[]` (if available from AI extraction)
     - From shared target_tools: if rule A and rule B both target the same tool → edge with weight 0.5
     - From trace sequences: if tool for rule A and tool for rule B appear in same `trace_analysis.common_sequences` → edge with weight from trace frequency
     - From scope overlap: conditional rules with overlapping conditions → edge with weight 0.3
  3. **Edge types**: `"co_occurrence"`, `"conflict"`, `"dependency"` (from guardrails.interactions)

- [ ] Define `PolicyGraphNode` and `PolicyGraphEdge` dataclasses:
  ```python
  @dataclass
  class PolicyGraphNode:
      rule_id: str
      rule_text: str
      complexity: int          # 1-5, used as node weight
      category: str
      target_tools: list[str]
      scope: str

  @dataclass
  class PolicyGraphEdge:
      from_rule: str
      to_rule: str
      edge_type: str           # co_occurrence | conflict | dependency
      weight: float            # 0.0-1.0
  ```

### E2.2 Weighted Random Walk Sampler

**File**: `src/scenarios/policy_graph.py`

- [ ] Implement `sample_scenario_walk(graph, max_complexity: int = 10, walk_length: int = 3) -> list[PolicyGraphNode]`:
  1. Start from a random node, weighted by complexity (higher complexity = more likely start)
  2. Walk to adjacent nodes via edges, weighted by edge weight
  3. Accumulate total complexity; stop when `total_complexity >= max_complexity` or `walk_length` reached
  4. Return the list of visited nodes (= the rules this scenario should test)

- [ ] Implement `sample_n_scenarios(graph, n: int, complexity_budget: int = 15) -> list[list[PolicyGraphNode]]`:
  - Sample n walks with varying max_complexity (distribute budget)
  - Ensure diversity: reject walks that repeat > 50% of a previous walk's rules
  - Return n rule-sets

### E2.3 Walk-to-Scenario Converter

**File**: `src/scenarios/policy_graph.py`

- [ ] Implement `walk_to_scenario(walk: list[PolicyGraphNode], agent_map: dict) -> Scenario`:
  1. **Title**: "Policy test: {categories}" (e.g., "Policy test: prohibition + escalation")
  2. **User goal**: construct from rule texts — "User requests something that tests: {rule_1_text} and {rule_2_text}"
  3. **Required tools**: union of target_tools from all rules in the walk
  4. **Difficulty**: based on total complexity (1-5 → easy, 6-10 → medium, 11+ → hard)
  5. **Type**: if any rule is prohibition/escalation → "error_path", else "edge_case"
  6. **Success conditions**: all compliance oracles for the rules in the walk
  7. **Failure conditions**: any guardrail violation for the rules in the walk
  8. **Source**: "policy_graph"
  9. **Tags**: rule IDs from the walk (R001, R003, etc.)

### E2.4 AI-Enhanced Walk Naturalisation

**File**: `src/scenarios/policy_graph.py`

- [ ] Implement `naturalise_scenario(scenario: Scenario, agent_map: dict, llm_config) -> Scenario`:
  - Send the rule texts and tool context to Claude
  - Ask it to rewrite the `user_goal` and `description` as a natural customer request that would trigger all the rules simultaneously
  - Preserve the structural fields (required_tools, oracles, tags)
  - Example: rules ["Never disclose payment info", "If order > 30 days, escalate"] → "Customer asks for detailed payment breakdown on a 45-day-old order"

### E2.5 Integrate into B3

**File**: `src/scenarios/library.py`

- [ ] Add method `generate_policy_graph_scenarios(count: int = 10, naturalise: bool = True) -> list[Scenario]`:
  1. Build policy graph from agent_map
  2. Sample `count` walks
  3. Convert walks to scenarios
  4. If `naturalise` and not skip_ai: naturalise each scenario via LLM
  5. Append to self.scenarios

- [ ] Wire into `_run_phase_b()`:
  ```python
  # After template loading, before AI generation
  if agent_map.get("guardrails", {}).get("total_rules", 0) > 0:
      policy_scenarios = scenario_lib.generate_policy_graph_scenarios(count=min(scenario_count, 15))
  ```

## Files Created/Modified

| File | Changes |
|------|---------|
| `src/scenarios/policy_graph.py` | **New file**: policy graph, random walk sampler, scenario converter |
| `src/scenarios/library.py` | New `generate_policy_graph_scenarios()` method |
| `generate_tests.py` | Wire policy-graph generation |

## Done When

- Policy graph built from guardrail rules with complexity weights and co-occurrence edges
- Weighted random walks produce diverse rule combinations
- Walk-to-scenario converter creates valid Scenario objects with oracles
- AI naturalisation rewrites user goals as realistic customer requests
- Policy-graph scenarios appear in the scenario catalog with source="policy_graph"
- Measurement harness (E12) shows improved coverage of guardrail rules
