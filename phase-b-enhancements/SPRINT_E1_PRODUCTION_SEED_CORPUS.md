# Sprint E1 — Production-Failure Seed Corpus

## Goal

Convert every real production failure trace (escalation, complaint, QA flag) into a reproducible seed scenario and store it in a seed corpus that Phase B draws from preferentially, mutating seeds (swap persona, change formality, perturb one tool argument) to generate neighbour scenarios. This is the single highest-payoff change: field-failure-derived tests reproduce real failures and find faults that structural generation does not.

**Literature**: EvoCrash (Soltani et al., ICSE 2017), BugRedux (Jin & Orso, ICSE 2012), coverage-guided fuzzing seed quality (Herrera et al., ISSTA 2021), operational-profile testing (Musa, 1993).

## Why This Matters

The current B3 scenario library generates scenarios from the agent's tool surface and generic edge-case dimensions. It has zero knowledge of what actually fails in production. The TechRepair WhatsApp agent has Langfuse traces with escalation events, failure patterns, and complaint sequences — these are the ideal seeds because they are known to reach a failure.

## Tasks

### E1.1 Define Seed Scenario Data Model

**File**: `src/scenarios/seed_corpus.py` (new file)

- [ ] Define data structures:
  ```python
  @dataclass
  class FailureSeed:
      seed_id: str                       # UUID
      trace_id: str                      # Langfuse trace ID
      failure_category: str              # From FailureCategory enum (E12)
      tool_sequence: list[str]           # Observed tool call sequence
      user_goal_inferred: str            # What the user was trying to do
      persona_features: dict             # Extracted from trace: formality, language, etc.
      trigger_conditions: list[str]      # What caused the failure
      outcome: str                       # "escalation", "complaint", "timeout", "loop"
      conversation_snippet: list[dict]   # First N turns (anonymised)
      severity: str                      # critical/high/medium/low
      created_at: datetime

  @dataclass
  class SeedCorpus:
      seeds: list[FailureSeed]
      total_seeds: int
      by_category: dict[str, int]
      by_outcome: dict[str, int]
      by_tool: dict[str, int]           # Which tools are involved in failures
  ```

### E1.2 Trace-to-Seed Adapter

**File**: `src/scenarios/seed_corpus.py`

- [ ] Implement `build_seed_corpus(trace_result, agent_map) -> SeedCorpus`:
  1. Filter `trace_result.conversations` to failures only (outcome != "success")
  2. For each failed conversation:
     - Extract `tool_sequence` from the trace
     - Classify `failure_category` using heuristics:
       - Ends with escalation tool → `ESCALATION_FAILURE`
       - Tool called but wrong output → `WRONG_TOOL`
       - Same tool called 3+ times → `INFINITE_LOOP`
       - Conversation < 2 turns → `PREMATURE_EXIT`
     - Infer `user_goal` from first user message (truncated, anonymised)
     - Extract persona features from conversation style:
       - Formality: usted vs tú indicators
       - Language: Spanish/English
       - Verbosity: average message length
       - Emoji use: emoji count
     - Extract `trigger_conditions` from the last few turns before failure
  3. Deduplicate seeds by (failure_category, tool_sequence) — keep highest severity
  4. Return SeedCorpus

- [ ] Implement `extract_persona_from_trace(conversation) -> dict`:
  - Analyse user messages for style features
  - Return dict compatible with PersonaTraits fields

### E1.3 Seed-to-Scenario Converter

**File**: `src/scenarios/seed_corpus.py`

- [ ] Implement `seed_to_scenario(seed: FailureSeed, agent_map: dict) -> Scenario`:
  - Map seed to Scenario object:
    - `title`: "Production failure: {failure_category} in {tool_sequence[0]}"
    - `user_goal`: seed.user_goal_inferred
    - `required_tools`: seed.tool_sequence (the tools that were involved)
    - `type`: "error_path"
    - `difficulty`: "hard"
    - `success_conditions`: based on failure_category (the opposite of what went wrong)
    - `failure_conditions`: what actually happened
    - `source`: "production_seed"
    - `tags`: ["production_failure", seed.failure_category, seed.outcome]

- [ ] Implement `seed_to_persona(seed: FailureSeed) -> Persona`:
  - Map seed.persona_features to PersonaTraits
  - Set source="production_seed"
  - Preserve original conversation style

### E1.4 Seed Mutation Engine

**File**: `src/scenarios/seed_corpus.py`

- [ ] Implement `mutate_seed(seed: FailureSeed, mutation_type: str) -> FailureSeed`:
  
  **Mutation types**:
  - `"swap_persona"`: keep same tool sequence, change persona traits (formality, patience, verbosity)
  - `"perturb_tool_arg"`: keep same sequence but change one tool argument (e.g., different order_id format)
  - `"adjacent_tool"`: replace one tool in the sequence with a neighbouring tool (same dependency group)
  - `"add_noise"`: insert an unrelated tool call mid-sequence (simulates user tangent)
  - `"change_language"`: switch between Spanish/English (for the TechRepair bilingual agent)
  - `"change_formality"`: switch between usted/tú

- [ ] Implement `expand_seed_corpus(corpus: SeedCorpus, mutations_per_seed: int = 3) -> list[Scenario]`:
  - For each seed, generate `mutations_per_seed` mutated variants
  - Convert each mutant to a Scenario via `seed_to_scenario()`
  - Return expanded scenario list

### E1.5 Integrate into B3 Scenario Library

**File**: `src/scenarios/library.py`

- [ ] Add new method `load_production_seeds(trace_result, agent_map, mutations_per_seed=3) -> list[Scenario]`:
  - Calls `build_seed_corpus()`
  - Calls `expand_seed_corpus()`
  - Appends original seeds + mutations to self.scenarios
  - Logs: "Loaded {n} production seeds, expanded to {m} scenarios"

- [ ] Update `_run_phase_b()` in `generate_tests.py`:
  - After loading templates and before AI generation:
    ```python
    if trace_result and trace_result.failure_patterns:
        seed_scenarios = scenario_lib.load_production_seeds(trace_result, agent_map)
        console.print(f"Production seeds: {len(seed_scenarios)} scenarios from {len(trace_result.failure_patterns)} failure patterns")
    ```

### E1.6 Integrate into B4 Test Suite Allocation

**File**: `src/generator/test_suite.py`

- [ ] Add **Phase 0** before tool coverage: seed-preferential allocation
  ```python
  # Phase 0: Production-seed coverage (highest priority)
  seed_scenarios = [s for s in scenarios if s.source == "production_seed"]
  for scenario in seed_scenarios[:budget_fraction]:
      persona = seed_persona or select_persona_weighted(personas, scenario)
      create_test_case(scenario, persona, coverage_goal="production_seed")
  ```
- [ ] Reserve 20% of test budget for production seeds (configurable)

## Files Modified

| File | Changes |
|------|---------|
| `src/scenarios/seed_corpus.py` | **New file**: FailureSeed, SeedCorpus, trace adapter, mutations |
| `src/scenarios/library.py` | New `load_production_seeds()` method |
| `src/scenarios/models.py` | Add `"production_seed"` to source enum |
| `src/generator/test_suite.py` | Add Phase 0 seed-preferential allocation |
| `generate_tests.py` | Wire seed loading when traces available |

## Done When

- Langfuse failure traces are converted into FailureSeed objects with correct categories
- Each seed produces a valid Scenario with tool sequence, persona, and oracles
- Mutation engine generates 3+ variants per seed
- B4 allocates seeds preferentially (Phase 0)
- Running with `--use-traces` produces seed-derived test cases in the suite
- Measurement harness (E12) shows recall improvement vs baseline

## Validation

```bash
# Run Phase B with traces (seeds auto-loaded)
python generate_tests.py agent_map.json --use-traces --evaluate -o output/

# Check seed scenarios in catalog
python -c "import json; d=json.load(open('output/scenario_catalog.json')); print(sum(1 for s in d['scenarios'] if s['source']=='production_seed'))"
```
