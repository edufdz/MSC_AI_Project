# Sprint 2 — Per-Tool Preconditions, Postconditions & Side-Effects

## Goal

Extend the `ToolDefinition` data model and extraction pipeline so every tool in the Agent Map carries explicit **preconditions** (what must be true before calling), **postconditions** (what becomes true after calling), and **side-effects** (state changes, external calls, data writes). This is grounded in design-by-contract and PDDL action modelling (Guan et al., NeurIPS 2023; arXiv 2604.08633): postconditions act as test oracles, preconditions enable boundary/negative tests, and side-effects let Phase B prioritise state-mutating tools for adversarial scenarios.

**Can run in parallel with**: Sprint 3 (OWASP taxonomy) — Sprint 2 modifies `ToolDefinition` and AI prompts; Sprint 3 modifies `RiskFlag` and `framework_signatures.py`.

## Why This Matters for Phase B

Currently Phase B knows a tool exists and what risk level it has, but not **what conditions must hold** to call it or **what changes** after it runs. With preconditions/postconditions:

- **Boundary tests**: test what happens when a precondition is violated (e.g., calling `refund_order` without a valid `order_id`)
- **Oracle generation**: postconditions define what success looks like (e.g., after `book_appointment`, the database should contain a new appointment)
- **State-mutation prioritisation**: side-effects flag which tools change state, so Phase B generates rollback and conflict scenarios
- **Dependency chains**: preconditions that reference other tools' postconditions reveal required tool orderings

## Tasks

### 2.1 Extend the `ToolDefinition` Dataclass

**File**: `src/patterns/detector.py` (lines 24-34)

- [ ] Add new fields to `ToolDefinition`:
  ```python
  @dataclass
  class ToolDefinition:
      # ... existing fields ...
      preconditions: list[str] = field(default_factory=list)    # e.g., ["order_id must be valid", "user must be authenticated"]
      postconditions: list[str] = field(default_factory=list)   # e.g., ["refund is issued", "order status changes to 'refunded'"]
      side_effects: list[str] = field(default_factory=list)     # e.g., ["writes to orders table", "sends email notification"]
      state_modifying: bool = True                               # True if tool changes state (write), False if read-only
  ```

### 2.2 Static Extraction of Side-Effects

**File**: `src/patterns/detector.py`

Create a new function `_extract_side_effects(func: FunctionInfo) -> tuple[list[str], bool]` that analyzes function body text to detect:

- [ ] **Database writes**: keywords `insert`, `update`, `delete`, `save`, `commit`, `execute` (with write-like SQL patterns)
- [ ] **HTTP mutations**: `post(`, `put(`, `patch(`, `delete(` (as opposed to `get(`)
- [ ] **File writes**: `write(`, `open(..., 'w')`, `save_to_file`
- [ ] **Email/notification sends**: `send_email`, `send_sms`, `send_notification`, `notify`
- [ ] **State changes**: `self.state =`, `session[`, `cache.set`, `redis.set`
- [ ] **External API calls**: `requests.post`, `httpx.post`, `fetch(` with non-GET method

Return `(side_effects_list, is_state_modifying)`. If no write indicators found, set `state_modifying = False`.

### 2.3 Static Extraction of Preconditions from Code

**File**: `src/patterns/detector.py`

Create `_extract_preconditions_from_code(func: FunctionInfo) -> list[str]`:

- [ ] Scan for early guard clauses: `if not X: raise`, `if X is None: return`, `assert X`
- [ ] Scan for validation calls: `validate(`, `check_`, `verify_`, `ensure_`
- [ ] Scan for required parameter checks: `if param not in`, `if not isinstance`
- [ ] Convert each to a human-readable precondition string: e.g., `"order_id must not be None"`
- [ ] Limit to first 10 preconditions per tool (avoid noise)

### 2.4 AI-Enhanced Precondition/Postcondition Extraction

**File**: `src/ai_analyzer/analyzer.py`

Extend `analyze_tools_semantically()` (line 204) to also extract preconditions and postconditions:

- [ ] Update the `TOOL_ANALYSIS_PROMPT` in `src/ai_analyzer/prompts.py` to request:
  ```
  For each tool, also determine:
  - preconditions: list of conditions that must be true before this tool can be called
    (e.g., "user must be authenticated", "order_id must exist in database")
  - postconditions: list of conditions that become true after successful execution
    (e.g., "appointment is created in system", "refund is processed")
  - side_effects: list of state changes or external actions performed
    (e.g., "writes to database", "sends email", "charges payment")
  ```

- [ ] Extend `ToolSemanticInfo` (line 46) with new fields:
  ```python
  preconditions: list[str] = field(default_factory=list)
  postconditions: list[str] = field(default_factory=list)
  side_effects: list[str] = field(default_factory=list)
  ```

### 2.5 Merge Static and AI Extractions

**File**: `src/graph/builder.py`

In `_tool_to_dict()` (line 146), merge the static and AI-extracted data:

- [ ] Preconditions: union of code-extracted and AI-extracted, deduplicated
- [ ] Postconditions: from AI analysis (not reliably extractable from code)
- [ ] Side-effects: union of code-detected and AI-extracted
- [ ] `state_modifying`: code-detected flag overrides AI `read_only` field if they conflict (code is ground truth)

### 2.6 Update Agent Map Schema

**File**: `src/graph/builder.py`

In `generate_agent_map()` (line 163), add the new fields to each tool in the output:

- [ ] Add `preconditions`, `postconditions`, `side_effects`, `state_modifying` to each tool dict in `components.tools[]`
- [ ] Ensure backward compatibility: new fields default to empty lists / `True` so existing Phase B code doesn't break

### 2.7 Update CLI Summary

**File**: `analyze.py`

- [ ] In `_print_pattern_summary()` (line 57), show count of tools with preconditions and state-modifying vs read-only tools

## Files Modified

| File | Changes |
|------|---------|
| `src/patterns/detector.py` | Add fields to `ToolDefinition`, new extraction functions |
| `src/ai_analyzer/analyzer.py` | Extend `ToolSemanticInfo`, update analysis |
| `src/ai_analyzer/prompts.py` | Update `TOOL_ANALYSIS_PROMPT` |
| `src/graph/builder.py` | Merge static+AI data, update map schema |
| `analyze.py` | Update CLI summary |

## Done When

- Every `ToolDefinition` carries `preconditions`, `postconditions`, `side_effects`, `state_modifying` fields
- Static extraction detects at least: DB writes, HTTP mutations, file writes, notification sends, guard clauses
- AI analysis (when enabled) produces natural-language preconditions and postconditions per tool
- The Agent Map `components.tools[]` includes all new fields
- Existing Phase B code that reads the Agent Map does not break (new fields are additive)

## Example Output

```json
{
  "id": "refund_order",
  "name": "refund_order",
  "description": "Process a refund for a customer order",
  "parameters": [{"name": "order_id", "type": "str"}, {"name": "reason", "type": "str"}],
  "preconditions": [
    "order_id must exist in the orders database",
    "order status must be 'completed' or 'delivered'",
    "refund has not already been issued for this order"
  ],
  "postconditions": [
    "order status changes to 'refunded'",
    "refund amount is credited to customer's payment method",
    "refund confirmation email is sent"
  ],
  "side_effects": [
    "writes to orders table (status update)",
    "writes to refunds table (new record)",
    "sends email notification",
    "calls payment gateway API"
  ],
  "state_modifying": true,
  "risk_level": "critical",
  "read_only": false
}
```
