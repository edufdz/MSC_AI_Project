# Sprint T — End-to-End Testing & Validation

## Goal

Verify that all enhancements from Sprints 1–9 work correctly, both individually and together. This sprint creates a comprehensive test suite for Phase A, including unit tests per module, integration tests for the full pipeline, regression tests against known agent codebases, and a validation harness that confirms the enhanced Agent Map produces richer Phase B output.

**Runs after**: All other sprints are complete.

## Test Architecture

```
tests/
├── phase_a/
│   ├── fixtures/                          # Test agent codebases
│   │   ├── python_agent/                  # Minimal Python agent with known tools
│   │   ├── typescript_agent/              # Minimal TS agent with known tools
│   │   ├── mixed_language_agent/          # Python + TS agent
│   │   ├── spanish_agent/                 # Agent with Spanish prompts
│   │   └── expected_outputs/             # Golden agent_map.json files
│   │
│   ├── unit/                             # Per-module unit tests
│   │   ├── test_ingestor.py
│   │   ├── test_static_analyzer.py
│   │   ├── test_pattern_detector.py
│   │   ├── test_risk_analyzer.py
│   │   ├── test_taint_analyzer.py        # Sprint 4
│   │   ├── test_rule_extractor.py        # Sprint 6
│   │   ├── test_behavioural_model.py     # Sprint 8
│   │   └── test_language_detection.py    # Sprint 9
│   │
│   ├── integration/                      # Full pipeline tests
│   │   ├── test_pipeline_python.py
│   │   ├── test_pipeline_typescript.py
│   │   ├── test_pipeline_mixed.py
│   │   └── test_agent_map_schema.py
│   │
│   └── validation/                       # Phase A → Phase B validation
│       ├── test_phase_b_consumption.py
│       └── test_enrichment_impact.py
```

## Tasks

### T.1 Create Test Fixtures

#### T.1.1 Python Agent Fixture

- [ ] Create `tests/phase_a/fixtures/python_agent/` with:
  - `main.py`: entry point with LangChain agent setup
  - `tools/search.py`: tool with `@tool` decorator, read-only, takes `query: str`
  - `tools/refund.py`: tool with `@tool` decorator, state-modifying, takes `order_id: str`, has guard clause (`if not order_id: raise ValueError`)
  - `tools/send_email.py`: tool that calls `requests.post()` with user email (PII flow)
  - `prompts/system.txt`: system prompt with 5 numbered rules in English
  - `config.py`: tool array in OpenAI format

  **Known expected outputs** (for golden comparison):
  - 4 tools detected (search, refund, send_email, config tools)
  - Framework: `langchain` with confidence > 0.5
  - Risks: PII (email in send_email), critical action (refund), taint flow (email → requests.post)
  - Preconditions: refund has `order_id must not be None`
  - 5 guardrail rules extracted

#### T.1.2 TypeScript Agent Fixture

- [ ] Create `tests/phase_a/fixtures/typescript_agent/` with:
  - `index.ts`: entry point with OpenAI function calling setup
  - `tools/booking.ts`: exported function with JSDoc, takes typed params, calls DB
  - `tools/lookup.ts`: exported function, read-only, uses `fetch()`
  - `tools/deleteUser.ts`: dangerous tool with `eval()` inside (for unsafe operation detection)
  - `prompts/system.md`: system prompt with 3 rules

  **Known expected outputs**:
  - 3+ tools detected (including from function-calling array)
  - TS/JS tree-sitter parser extracts parameter types and JSDoc
  - Unsafe operation flagged (eval in deleteUser)
  - Taxonomy: ASI05 + LLM01 for deleteUser

#### T.1.3 Spanish Agent Fixture

- [ ] Create `tests/phase_a/fixtures/spanish_agent/` with:
  - Python agent with Spanish system prompt
  - Rules written in Spanish (prohibitions, escalation triggers)
  - Tool descriptions in Spanish

  **Known expected outputs**:
  - `primary_language: "Spanish"`
  - `guardrail_language: "Spanish"`
  - Rules extracted in Spanish
  - `spanish_formality: "usted"`

### T.2 Unit Tests

#### T.2.1 Ingestor Tests (`test_ingestor.py`)

- [ ] Test file discovery: correct files found, excluded dirs skipped
- [ ] Test priority scoring: `agent.py` scores higher than `utils.py`
- [ ] Test language detection: `.py` → python, `.ts` → typescript
- [ ] Test entry point detection: `main.py` is flagged
- [ ] Test prompt file discovery: `.prompt`, `.jinja` files found
- [ ] Test language filter: `language_filter="python"` excludes TS files

#### T.2.2 Static Analyzer Tests (`test_static_analyzer.py`)

- [ ] **Python parser**: extracts functions, classes, imports, decorators, calls
- [ ] **TS/JS tree-sitter parser (Sprint 1)**: extracts same set from TS code
  - [ ] Test: parameter types are extracted (regex parser couldn't do this)
  - [ ] Test: decorators are extracted
  - [ ] Test: JSDoc comments are extracted as docstrings
  - [ ] Test: arrow functions are captured
  - [ ] Test: class methods are captured
  - [ ] Test: function calls within body are captured
- [ ] **Fallback**: if tree-sitter TS fails, regex parser runs without crash
- [ ] **Edge cases**: empty files, syntax errors, very large files (>10K lines)

#### T.2.3 Pattern Detector Tests (`test_pattern_detector.py`)

- [ ] Framework detection: LangChain imports → `langchain` with confidence > 0
- [ ] Tool extraction (LangChain): `@tool` decorated function → `ToolDefinition`
- [ ] Tool extraction (OpenAI): tool array variable → parsed tools
- [ ] Tool extraction (custom heuristic): function with `requests.post` + docstring → score ≥ 3
- [ ] Prompt extraction: variable named `system_prompt` with >50 chars → `PromptDefinition`
- [ ] Memory detection: `ConversationBufferMemory` import → `MemorySystem`
- [ ] **Preconditions (Sprint 2)**: guard clause in function → precondition extracted
- [ ] **Side effects (Sprint 2)**: `requests.post` in function → `state_modifying=True`

#### T.2.4 Risk Analyzer Tests (`test_risk_analyzer.py`)

- [ ] PII regex: email pattern in tool description → `RiskFlag(pii_type="email")`
- [ ] Critical action: `"payment"` in tool name → `RiskFlag(severity="critical")`
- [ ] **Taxonomy mapping (Sprint 3)**: PII risk → `taxonomy_ids=["LLM02", "ASI03"]`
- [ ] **Unsafe operations (Sprint 3)**: `eval(` in code → `taxonomy_ids=["ASI05", "LLM01"]`
- [ ] **Excessive agency (Sprint 3)**: 15 tools with no confirmation gates → `taxonomy_ids=["LLM06"]`
- [ ] Deduplication: same tool+risk_type+pii_type → single RiskFlag

#### T.2.5 Taint Analyzer Tests (`test_taint_analyzer.py`) — Sprint 4

- [ ] Source identification: parameter named `user_input` → TaintSource
- [ ] Sink identification: `requests.post()` call → TaintSink
- [ ] Flow tracing: `user_input` assigned to `email`, `email` passed to `requests.post()` → TaintFlow
- [ ] PII detection in flow: variable named `email` → `data_types=["email"]`
- [ ] No false positives: internal variable not connected to sink → no TaintFlow
- [ ] Read-only function (no sinks) → no flows

#### T.2.6 Rule Extractor Tests (`test_rule_extractor.py`) — Sprint 6

- [ ] Numbered rules: `"1. Never share data"` → PolicyRule(category="prohibition")
- [ ] Bullet rules: `"- Always verify identity"` → PolicyRule(category="requirement")
- [ ] Spanish rules: `"- Nunca compartir datos"` → PolicyRule(category="prohibition", language="Spanish")
- [ ] Complexity scoring: simple rule → 1, conditional rule → 2-3
- [ ] Scope detection: `"When handling refunds, always..."` → scope="conditional", target_tools=["refund"]
- [ ] Empty prompt → empty rule list (no crash)

#### T.2.7 Language Detection Tests (`test_language_detection.py`) — Sprint 9

- [ ] Spanish prompt → `primary_language: "Spanish"`
- [ ] English prompt → `primary_language: "English"`
- [ ] Mixed prompt → `code_switching_detected: True`
- [ ] Portuguese prompt → `primary_language: "Portuguese"`
- [ ] Formality: `"usted"` in prompt → `spanish_formality: "usted"`
- [ ] Guardrail mismatch: English rules + Spanish conversation → `language_mismatch: True`

#### T.2.8 Behavioural Model Tests (`test_behavioural_model.py`) — Sprint 8

- [ ] Dependency edge creation from static preconditions
- [ ] Dependency edge creation from AI-inferred dependencies
- [ ] Circular dependency detection
- [ ] Bottleneck tool detection
- [ ] Coverage target generation

### T.3 Integration Tests

#### T.3.1 Full Pipeline — Python Agent (`test_pipeline_python.py`)

- [ ] Run full Phase A pipeline against `fixtures/python_agent/` with `skip_ai=True`
- [ ] Assert: `agent_map.json` is valid JSON
- [ ] Assert: `agent_map.version == "1.0"`
- [ ] Assert: `len(agent_map.components.tools) >= 4`
- [ ] Assert: `agent_map.metadata.framework == "langchain"`
- [ ] Assert: at least 1 risk with `taxonomy_ids` containing `"LLM02"`
- [ ] Assert: at least 1 tool with `preconditions` non-empty
- [ ] Assert: at least 1 tool with `state_modifying == True`
- [ ] Assert: `guardrails.total_rules >= 5`
- [ ] Assert: `risk_flags.taint_flows` contains at least 1 flow

#### T.3.2 Full Pipeline — TypeScript Agent (`test_pipeline_typescript.py`)

- [ ] Run full Phase A against `fixtures/typescript_agent/` with `skip_ai=True`
- [ ] Assert: tools are extracted (tree-sitter parser, not regex)
- [ ] Assert: parameter types are present (regression test vs old regex parser)
- [ ] Assert: unsafe operation detected in `deleteUser.ts`

#### T.3.3 Full Pipeline — Mixed Language (`test_pipeline_mixed.py`)

- [ ] Run against a directory with both `.py` and `.ts` files
- [ ] Assert: tools from both languages are merged into single tool list
- [ ] Assert: no duplicate tools

#### T.3.4 Agent Map Schema Validation (`test_agent_map_schema.py`)

- [ ] Validate Agent Map against a JSON schema that includes all new fields:
  - `components.tools[].preconditions` (list[str])
  - `components.tools[].postconditions` (list[str])
  - `components.tools[].side_effects` (list[str])
  - `components.tools[].state_modifying` (bool)
  - `risk_flags.all_risks[].taxonomy_ids` (list[str])
  - `risk_flags.taint_flows` (list[dict])
  - `guardrails` (object with rules, interactions, etc.)
  - `metadata.language` (object)
  - `metadata.domain` (object)
  - `behavioural_model` (object, optional)
  - `trace_analysis` (object, optional)
- [ ] Ensure backward compatibility: old fields still present

### T.4 Validation: Phase A → Phase B Impact

#### T.4.1 Phase B Consumption Test (`test_phase_b_consumption.py`)

- [ ] Load an enhanced Agent Map with all new fields
- [ ] Feed it to Phase B's coverage calculator, persona builder, scenario library
- [ ] Assert: Phase B does not crash on new fields
- [ ] Assert: Phase B ignores unknown fields gracefully (backward compatible)

#### T.4.2 Enrichment Impact Test (`test_enrichment_impact.py`)

- [ ] Generate Agent Map **without** enhancements (original pipeline)
- [ ] Generate Agent Map **with** enhancements (enhanced pipeline)
- [ ] Compare:
  - [ ] Enhanced map has more tools (TS/JS coverage)
  - [ ] Enhanced map has more risk flags (taxonomy, taint flows, unsafe ops)
  - [ ] Enhanced map has preconditions/postconditions (original has none)
  - [ ] Enhanced map has guardrail rules (original has none)
  - [ ] Enhanced map has richer language metadata

### T.5 Performance & Regression

- [ ] **Performance**: Phase A on python_agent fixture completes in < 30 seconds (skip_ai=True)
- [ ] **Performance**: Phase A on typescript_agent fixture completes in < 30 seconds
- [ ] **Regression**: existing test suites (if any) pass without modification
- [ ] **Graceful degradation**: Phase A with missing tree-sitter-typescript still works (falls back to regex)
- [ ] **Graceful degradation**: Phase A with no Langfuse credentials skips trace analysis
- [ ] **Graceful degradation**: Phase A with `skip_ai=True` still produces all static analysis fields

### T.6 API Endpoint Tests

- [ ] `POST /api/phase-a/run` with enhanced parameters (`context_budget`, `use_traces`) → starts successfully
- [ ] `GET /api/phase-a/status/{session_id}` → returns progress with new step names
- [ ] WebSocket progress events include new steps (e.g., `"taint_analysis"`, `"guardrail_extraction"`)
- [ ] Result includes new Agent Map fields

## Files Created

| File | Purpose |
|------|---------|
| `tests/phase_a/fixtures/python_agent/` | Python test agent |
| `tests/phase_a/fixtures/typescript_agent/` | TypeScript test agent |
| `tests/phase_a/fixtures/spanish_agent/` | Spanish-language test agent |
| `tests/phase_a/unit/test_*.py` | 8 unit test files |
| `tests/phase_a/integration/test_*.py` | 4 integration test files |
| `tests/phase_a/validation/test_*.py` | 2 validation test files |

## Done When

- All unit tests pass
- All integration tests pass against fixture agents
- Phase B consumes enhanced Agent Maps without errors
- Enhanced Agent Maps contain measurably richer information than baseline
- Performance is acceptable (< 30s per fixture with skip_ai)
- Graceful degradation works for all optional features

## Running Tests

```bash
# Run all Phase A tests
pytest tests/phase_a/ -v

# Run only unit tests
pytest tests/phase_a/unit/ -v

# Run only integration tests
pytest tests/phase_a/integration/ -v

# Run with coverage report
pytest tests/phase_a/ --cov=src --cov-report=term-missing
```
