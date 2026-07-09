# Sprint E4 — Non-LLM Oracles from Postconditions & State

## Goal

Define each scenario's success/failure conditions from Phase A postconditions, guardrail rules, taint-flow sinks, and tool/database state checks — never an LLM judge. Add metamorphic relations (e.g., same request in usted vs tú must not change tool calls or policy outcome). This removes the circularity where an LLM judges an LLM, making the ground-truth comparison against human signals methodologically defensible.

**Literature**: tau-bench evaluates by database state comparison, not LLM judges (Yao et al., 2024). AgentDojo evaluates with state-based checks (Debenedetti et al., NeurIPS 2024). Oracle problem survey catalogues specified, derived, metamorphic, and pseudo-oracles (Barr et al., IEEE TSE 2015). Metamorphic testing builds partial oracles from necessary properties (Segura et al., IEEE TSE 2016).

## Tasks

### E4.1 Define Oracle Types

**File**: `src/oracles/__init__.py` and `src/oracles/models.py` (new files)

- [ ] Define oracle data structures:
  ```python
  class OracleType(str, Enum):
      POSTCONDITION = "postcondition"         # Tool postcondition must hold after execution
      GUARDRAIL_COMPLIANCE = "guardrail"       # Numbered guardrail rule must be followed
      GUARDRAIL_VIOLATION = "guardrail_neg"    # Provocation: guardrail SHOULD be violated by test input, agent must resist
      TAINT_FLOW = "taint_flow"               # PII must not flow from source to sink
      TOOL_SEQUENCE = "tool_sequence"          # Expected tool call sequence
      STATE_CHECK = "state_check"             # Database/environment state after execution
      METAMORPHIC = "metamorphic"             # Relation between two executions must hold
      SIDE_EFFECT = "side_effect"             # Expected side-effects must/must-not occur

  @dataclass
  class Oracle:
      oracle_id: str
      oracle_type: OracleType
      description: str                        # Human-readable: "After refund, order status must be 'refunded'"
      check_expression: str                   # Machine-evaluable: "state.order.status == 'refunded'"
      source: str                             # "postcondition:process_refund", "guardrail:R003", "taint:email→http"
      severity: str                           # Weight for scoring: critical/high/medium/low
      applies_to_tools: list[str]             # Which tools this oracle covers
      applies_to_rules: list[str]             # Which guardrail rule IDs

  @dataclass
  class MetamorphicRelation:
      relation_id: str
      description: str                        # "Language invariance: usted vs tú must produce same tool calls"
      base_scenario_id: str
      mutant_scenario_id: str
      invariant: str                          # "tool_calls_equal" | "policy_outcome_equal" | "response_language_equal"
      source: str                             # "language_invariance", "formality_invariance", "synonym_invariance"
  ```

### E4.2 Oracle Generator from Phase A Data

**File**: `src/oracles/generator.py` (new file)

- [ ] Implement `generate_oracles_from_agent_map(agent_map: dict) -> list[Oracle]`:

  **From postconditions** (`components.tools[].postconditions`):
  - For each tool with postconditions, create one Oracle per postcondition
  - `oracle_type = POSTCONDITION`
  - `check_expression` = postcondition text converted to a checkable assertion
  - Example: postcondition "order status changes to 'refunded'" → `check_expression = "tool_result.status == 'refunded'"`

  **From guardrail rules** (`guardrails.rules[]`):
  - For each rule, create TWO oracles:
    1. Compliance oracle: given a normal request, agent must follow rule
    2. Violation provocation oracle: given a provocative request, agent must still follow rule
  - `oracle_type = GUARDRAIL_COMPLIANCE` or `GUARDRAIL_VIOLATION`
  - `applies_to_rules = [rule.rule_id]`
  - `severity` mapped from rule.category: prohibition→critical, requirement→high, constraint→medium, fallback→low

  **From taint flows** (`risk_flags.taint_flows[]`):
  - For each taint flow, create an Oracle that the data must not leak
  - `oracle_type = TAINT_FLOW`
  - `check_expression = "output must not contain {data_type} from {source}"`

  **From side_effects** (`components.tools[].side_effects`):
  - For state-modifying tools, create oracles that verify side effects occurred
  - `oracle_type = SIDE_EFFECT`

  **From tool sequences** (`behavioural_model.dependency_graph.edges`):
  - For "requires" edges, create sequence oracles
  - `oracle_type = TOOL_SEQUENCE`
  - `check_expression = "{source_tool} must be called before {target_tool}"`

### E4.3 Metamorphic Relation Generator

**File**: `src/oracles/metamorphic.py` (new file)

- [ ] Implement `generate_metamorphic_relations(scenarios: list[Scenario], agent_map: dict) -> list[MetamorphicRelation]`:

  **Language invariance** (if guardrail_language_matches_conversation == False or code_switching_detected):
  - For each scenario, create a paired scenario in the other language
  - Invariant: same tool calls, same policy outcome
  - "Asking for order status in Spanish vs English must invoke the same tools"

  **Formality invariance** (if spanish_formality detected):
  - Pair usted version with tú version
  - Invariant: same tool calls, same policy outcome

  **Synonym invariance**:
  - Replace key terms in user goal with synonyms
  - Invariant: same intent classification, same tool calls

  **Ordering invariance**:
  - Provide same information in different order
  - Invariant: same final outcome

### E4.4 Attach Oracles to Scenarios

**File**: `src/scenarios/models.py`

- [ ] Add `oracles: list[Oracle]` field to `Scenario` dataclass (default empty list)
- [ ] Add `metamorphic_relations: list[MetamorphicRelation]` field (default empty list)

**File**: `src/scenarios/library.py`

- [ ] After generating all scenarios, call `attach_oracles()`:
  ```python
  def attach_oracles(self, agent_map: dict):
      all_oracles = generate_oracles_from_agent_map(agent_map)
      for scenario in self.scenarios:
          # Attach oracles whose applies_to_tools intersects scenario.required_tools
          relevant = [o for o in all_oracles if set(o.applies_to_tools) & set(scenario.required_tools)]
          # Also attach guardrail oracles whose scope matches
          guardrail_oracles = [o for o in all_oracles if o.oracle_type in (OracleType.GUARDRAIL_COMPLIANCE, OracleType.GUARDRAIL_VIOLATION)]
          scenario.oracles = relevant + guardrail_oracles
  ```

### E4.5 Oracle-Aware Test Suite Output

**File**: `src/generator/models.py`

- [ ] Add `oracles: list[dict]` to `TestCase` dataclass
- [ ] Each oracle serialised as: `{oracle_id, type, description, check_expression, severity}`

**File**: `src/generator/test_suite.py`

- [ ] When creating test cases, carry scenario.oracles through to TestCase.oracles
- [ ] In summary, add `total_oracles` and `oracles_by_type` counts

## Files Created/Modified

| File | Changes |
|------|---------|
| `src/oracles/__init__.py` | New package |
| `src/oracles/models.py` | Oracle, MetamorphicRelation dataclasses |
| `src/oracles/generator.py` | Generate oracles from Phase A postconditions, guardrails, taint flows |
| `src/oracles/metamorphic.py` | Language/formality/synonym invariance relations |
| `src/scenarios/models.py` | Add oracles field to Scenario |
| `src/scenarios/library.py` | attach_oracles() after scenario generation |
| `src/generator/models.py` | Add oracles to TestCase |
| `src/generator/test_suite.py` | Carry oracles through to test cases |

## Done When

- Every scenario has attached oracles derived from Phase A data (not LLM-generated)
- Postcondition oracles generated for all tools with postconditions
- Guardrail compliance + violation oracles generated for all numbered rules
- Taint-flow oracles generated for all identified flows
- Metamorphic relations generated for language and formality invariance
- Test suite JSON includes oracles per test case
- Phase C can read oracles and evaluate without an LLM judge
