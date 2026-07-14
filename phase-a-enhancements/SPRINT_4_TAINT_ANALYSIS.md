# Sprint 4 — Intra-Procedural Taint/Data-Flow Analysis

## Goal

Replace the naive regex PII detection (`src/risk/analyzer.py:26-76`) with an intra-procedural taint/data-flow pass that tracks untrusted input from **sources** through **propagation** to **sinks**. Modelled on CodeQL's source/propagation/sink framework and inspired by AgentArmor's Program Dependence Graph approach (which reduced attack success rate from 41% to 3%).

**Can run in parallel with**: Sprint 6 (guardrail extraction) — this sprint adds a new `src/analysis/taint_analyzer.py` module; Sprint 6 modifies AI prompts.

## Why This Matters for Phase B

A PII-flow path from user input → tool parameter → outbound WhatsApp message is a **concrete, prioritised data-exfiltration test case**. An injection-prone sink (user input → `eval()`) is a **concrete injection scenario**. Regex PII detection can only say "this tool's code mentions an email pattern" — it cannot trace whether that email actually flows to an unsafe destination.

## Current Limitations

The current PII detection in `risk/analyzer.py` (lines 26-76):
- Checks parameter **names** against keyword lists (line 35): `if param_name in address_keywords`
- Checks tool **description + code_snippet** against regex patterns (lines 61-74): `re.search(pattern, text)`
- Has **no concept of data flow**: if `user_email` is assigned to a variable, passed to a function, and then logged — the regex won't connect those steps
- Cannot distinguish: "tool validates an email" (safe) vs "tool sends an email to an external API" (risky)

## Architecture

```
Source Nodes                 Propagation                    Sink Nodes
─────────────               ───────────                    ──────────
user message input     →    variable assignments      →    external API calls
tool return values     →    function parameters       →    database writes
retrieved documents    →    string concatenation      →    logging/print statements
environment variables  →    dict/list operations      →    eval/exec calls
                       →    function return values    →    file writes
                                                      →    outbound messages (email/SMS)
```

## Tasks

### 4.1 Create Taint Analyzer Module

**File**: `src/analysis/taint_analyzer.py` (new file)

- [ ] Define data structures:
  ```python
  @dataclass
  class TaintSource:
      variable: str           # variable name that carries tainted data
      source_type: str        # "user_input" | "tool_output" | "retrieved_doc" | "env_var"
      location: dict          # {file, line}
      description: str        # human-readable: "user message parameter"

  @dataclass
  class TaintSink:
      variable: str           # variable being consumed
      sink_type: str          # "external_api" | "database_write" | "logging" | "code_execution" | "outbound_message" | "file_write"
      location: dict
      description: str

  @dataclass
  class TaintFlow:
      source: TaintSource
      sink: TaintSink
      path: list[str]         # variable names through the flow: ["user_input", "email", "payload", "requests.post"]
      data_types: list[str]   # PII types detected in flow: ["email", "phone"]
      risk_level: str         # "low" | "medium" | "high" | "critical"
      taxonomy_ids: list[str] # ["LLM02", "ASI03"] (from Sprint 3)
  ```

### 4.2 Identify Taint Sources

- [ ] Create `identify_sources(func: FunctionInfo) -> list[TaintSource]`:
  - **User input parameters**: function parameters named `message`, `user_input`, `query`, `request`, `input`, `text`, `prompt`
  - **Tool outputs**: variables assigned from function calls that match tool names
  - **External data**: variables assigned from `os.environ`, `os.getenv`, `request.json`, `request.body`
  - **Retrieved documents**: variables from `retrieve`, `search`, `fetch`, `get_context`, `vector_store.query`

### 4.3 Identify Taint Sinks

- [ ] Create `identify_sinks(func: FunctionInfo) -> list[TaintSink]`:
  - **External API calls**: `requests.post`, `httpx.post`, `aiohttp`, `fetch(`, `urllib.request`
  - **Database writes**: `.execute(` with INSERT/UPDATE/DELETE, `.save()`, `.commit()`
  - **Logging**: `print(`, `logger.`, `logging.`, `console.log`
  - **Code execution**: `eval(`, `exec(`, `subprocess.`, `os.system(`
  - **Outbound messages**: `send_email`, `send_sms`, `send_message`, `notify`
  - **File writes**: `open(... 'w')`, `.write(`, `json.dump(`

### 4.4 Trace Intra-Procedural Flows

- [ ] Create `trace_flows(func: FunctionInfo, sources: list[TaintSource], sinks: list[TaintSink]) -> list[TaintFlow]`:
  - **Assignment propagation**: if `x = source_var`, then `x` is tainted
  - **Function call propagation**: if `result = foo(tainted_var)`, then `result` is tainted
  - **String formatting propagation**: if `msg = f"Hello {tainted_var}"`, then `msg` is tainted
  - **Dict/list propagation**: if `data["key"] = tainted_var`, then `data` is tainted
  - **Return propagation**: if function returns a tainted variable, mark the function as a taint propagator
  - Walk the function body line-by-line (using `body_text` split by newlines), tracking which variables are tainted
  - When a tainted variable reaches a sink → create a `TaintFlow`

**Implementation approach**: This is a simplified, line-by-line analysis over the source text (not full AST data-flow). It won't catch all flows but will catch the most common patterns: direct assignment chains, string formatting, and function call wrapping.

### 4.5 Detect PII Types in Flows

- [ ] For each `TaintFlow`, check if the flow carries PII:
  - Check variable names against PII keywords: `email`, `phone`, `ssn`, `credit_card`, `address`, `name`, `password`
  - Check if the source or any intermediate variable matches PII_PATTERNS regex
  - Populate `data_types` field

### 4.6 Integrate with Risk Analyzer

**File**: `src/risk/analyzer.py`

- [ ] Add new function `detect_taint_risks(all_symbols: list[FileSymbols]) -> list[RiskFlag]`:
  - For each file, for each function:
    1. Identify sources
    2. Identify sinks
    3. Trace flows
    4. Convert each `TaintFlow` to a `RiskFlag`:
       - `risk_type`: `"taint_flow"`
       - `severity`: based on sink type — `"critical"` for code_execution, `"high"` for external_api/outbound_message, `"medium"` for database_write/logging
       - `description`: `"Data flows from {source.description} to {sink.description} via {path}"`
       - `taxonomy_ids`: `["LLM02"]` for PII flows, `["ASI05", "LLM01"]` for code execution sinks

- [ ] Update `analyze_risks()` (line 126) to call `detect_taint_risks()` and include results

### 4.7 Update Agent Map with Flow Data

**File**: `src/graph/builder.py`

- [ ] Add a `taint_flows` section to `risk_flags` in the Agent Map:
  ```json
  "risk_flags": {
      "pii_handling": true,
      "taint_flows": [
          {
              "source": "user message parameter 'query'",
              "sink": "requests.post() to external API",
              "path": ["query", "processed_query", "api_payload"],
              "data_types": ["email"],
              "risk_level": "high",
              "taxonomy_ids": ["LLM02", "ASI03"]
          }
      ],
      "all_risks": [...]
  }
  ```

### 4.8 Keep Regex PII as Fallback

- [ ] Do **not** remove the existing regex PII detection — keep it as a supplementary check
- [ ] Taint flows provide **path-aware** risks; regex provides **pattern-aware** risks
- [ ] Deduplicate: if a taint flow and a regex risk flag refer to the same tool + PII type, keep the taint flow (richer information)

## Files Modified

| File | Changes |
|------|---------|
| `src/analysis/taint_analyzer.py` | **New file**: TaintSource, TaintSink, TaintFlow, analysis functions |
| `src/risk/analyzer.py` | New `detect_taint_risks()`, updated `analyze_risks()` |
| `src/graph/builder.py` | Add `taint_flows` to Agent Map output |
| `analyze.py` | Update CLI to show taint flow summary |

## Scope Limitations

This sprint implements **intra-procedural** taint analysis (within a single function body). It does **not** implement:
- Inter-procedural tracking (across function calls) — that's a follow-on
- Full AST data-flow graph (uses line-by-line text analysis) — sufficient for common patterns
- CodeQL-level precision — this is a lightweight approximation

## Done When

- A new `src/analysis/taint_analyzer.py` module exists with source/sink/flow detection
- `analyze_risks()` includes taint flow results alongside regex PII results
- The Agent Map contains a `taint_flows` section with source→sink paths
- Running Phase A against a codebase with obvious data flows (e.g., `user_input → requests.post()`) produces taint flow entries
- Existing regex PII detection still works as a fallback
