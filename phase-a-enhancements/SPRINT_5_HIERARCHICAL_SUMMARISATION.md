# Sprint 5 — Hierarchical Code Summarisation (Replace 80K Cap)

## Goal

Replace the hard 80K-character context cap in `src/ai_analyzer/analyzer.py:33,145` with a **call-graph-guided hierarchical summarisation** strategy. Currently, `_build_context_summary()` concatenates imports, tools, prompts, and entry point code, then truncates at 80K chars — silently losing information for large repos. The literature shows hierarchical summarisation achieves Pass@10 of 0.89 vs flat-retrieval baselines (ICCSA 2025), and RepoGraph (ICLR 2025) reports a 32.8% relative improvement on SWE-bench.

**Depends on**: Sprint 1 (needs complete AST for all languages to build accurate call graphs).

## Why This Matters for Phase B

If the AI semantic analysis truncates the agent's core logic, the extracted workflow model (decision strategy, guardrails, ambiguity handling) will be inaccurate or incomplete. Inaccurate guardrail extraction → Phase B can't generate rule-violation tests. Incomplete workflow → Phase B generates scenarios that don't match the agent's actual flow.

## Current Problem

**File**: `src/ai_analyzer/analyzer.py`

```python
MAX_CONTEXT_CHARS = 80_000  # line 33

def _build_context_summary(...) -> str:  # line 106
    # Builds context from:
    # - Framework name
    # - File list (all files)
    # - Key imports (max 30 unique)
    # - Tool summaries (first 20, descriptions truncated to 150 chars)
    # - Prompt content (first 5, content first 200 chars)
    # - Entry point code (first 3000 chars)
    return context[:MAX_CONTEXT_CHARS]  # line 145 — hard truncation
```

For a repo with 50+ files, the imports and file list alone can consume 20K+ characters, leaving little room for the actual code that matters.

## Tasks

### 5.1 Build Import/Call Graph from FileSymbols

**File**: `src/ai_analyzer/code_navigator.py` (new file)

- [ ] Create `build_call_graph(all_symbols: list[FileSymbols]) -> nx.DiGraph`:
  - Nodes: every function and class across all files
  - Edges: from `FunctionInfo.calls` (already extracted by static analyzer)
  - Edge data: call site location
  - Node data: file path, function name, is_entry_point flag

- [ ] Create `find_relevant_subgraph(graph, entry_points, tool_functions, max_nodes=50) -> set[str]`:
  - Start from entry points and tool function definitions
  - BFS/DFS to find all functions reachable from entry points that eventually call tools
  - Return the set of function names that form the "relevant spine" of the agent

### 5.2 Implement Hierarchical Summarisation

**File**: `src/ai_analyzer/code_navigator.py`

- [ ] Create `summarise_repository(all_symbols, relevant_functions, tools, prompts, framework) -> list[CodeChunk]`:

  ```python
  @dataclass
  class CodeChunk:
      level: str          # "project" | "module" | "function"
      path: str           # file path
      name: str           # function/class name or module name
      summary: str        # human-readable summary (for project/module level)
      code: str           # actual source code (for function level)
      relevance: float    # 0.0-1.0 (based on distance from entry points / tools)
      char_count: int
  ```

  **Three-level hierarchy**:

  1. **Project level** (1 chunk): framework, file count, tool count, entry points, purpose
  2. **Module level** (1 per file): file path, classes defined, functions defined, imports — as a short summary, not full code
  3. **Function level** (1 per relevant function): full source code, only for functions in the relevant subgraph

### 5.3 Implement Budget-Aware Context Assembly

**File**: `src/ai_analyzer/code_navigator.py`

- [ ] Create `assemble_context(chunks: list[CodeChunk], budget_chars: int = 80_000) -> str`:
  - **Priority order**:
    1. Project-level summary (always included)
    2. All prompt contents (always included — critical for guardrail extraction)
    3. Entry point function code (highest priority)
    4. Tool function code (sorted by risk level: critical > high > medium > low)
    5. Functions called by tools (sorted by relevance)
    6. Module-level summaries for remaining files
  - Fill until budget is reached
  - **Never truncate mid-function** — either include the full function or skip it
  - Track what was included vs excluded for a coverage report

- [ ] Return both the context string and a coverage metadata dict:
  ```python
  {
      "total_functions": 120,
      "included_functions": 45,
      "included_by_level": {"entry_point": 3, "tool_definition": 12, "tool_dependency": 20, "other": 10},
      "excluded_functions": 75,
      "budget_used_chars": 78500,
      "budget_total_chars": 80000,
  }
  ```

### 5.4 Replace `_build_context_summary()`

**File**: `src/ai_analyzer/analyzer.py`

- [ ] Replace `_build_context_summary()` (lines 106-145) with a call to the new hierarchical assembler:
  ```python
  def _build_context_summary(all_symbols, tools, prompts, entry_point_code, framework):
      graph = build_call_graph(all_symbols)
      relevant = find_relevant_subgraph(graph, entry_points, tool_functions)
      chunks = summarise_repository(all_symbols, relevant, tools, prompts, framework)
      context, coverage = assemble_context(chunks, budget_chars=MAX_CONTEXT_CHARS)
      return context
  ```

- [ ] Log the coverage metadata so developers can see what was included/excluded

### 5.5 LLM-Fact Validation

**File**: `src/ai_analyzer/analyzer.py`

The call-graph study (arXiv 2410.00603) shows LLMs hallucinate structural facts. Add a validation step:

- [ ] After `analyze_tools_semantically()` returns, cross-check AI claims against static facts:
  - If AI says a tool is `read_only=True` but taint analysis (Sprint 4) found write sinks → flag conflict
  - If AI says tool A depends on tool B, but the call graph has no path from A to B → flag as unverified
  - If AI claims a guardrail exists but no matching code pattern found → flag as unverified
- [ ] Add a `confidence` field to each AI-derived fact: `"verified"` (matches static), `"unverified"` (no static evidence), `"conflicted"` (contradicts static)

### 5.6 Make Budget Configurable

**File**: `src/ai_analyzer/analyzer.py`

- [ ] Make `MAX_CONTEXT_CHARS` configurable via CLI flag `--context-budget` and API parameter
- [ ] Default remains 80K but can be increased for models with larger context windows
- [ ] Update `analyze.py` Click options and `web/api/routes/phase_a.py` request model

## Files Modified

| File | Changes |
|------|---------|
| `src/ai_analyzer/code_navigator.py` | **New file**: call graph, hierarchical summarisation, context assembly |
| `src/ai_analyzer/analyzer.py` | Replace `_build_context_summary()`, add LLM-fact validation |
| `analyze.py` | Add `--context-budget` CLI option |
| `web/api/routes/phase_a.py` | Add `context_budget` to request model |

## Done When

- Context assembly uses call-graph-guided relevance ranking instead of flat concatenation
- Functions are never truncated mid-body
- Coverage metadata shows what percentage of functions were included
- LLM-derived facts are cross-checked against static analysis
- Running Phase A against a large repo (>80K chars of source) produces better AI analysis than the truncated version
- The `--context-budget` flag allows adjusting the limit

## Validation

```bash
# Run against a large repo and check coverage
python analyze.py /path/to/large-agent --verbose 2>&1 | grep "context_coverage"

# Compare AI analysis quality: old (truncated) vs new (hierarchical)
python analyze.py /path/to/large-agent --skip-ai -o map_static.json
python analyze.py /path/to/large-agent -o map_full.json
# Diff: map_full should have more tools with verified semantics
```
