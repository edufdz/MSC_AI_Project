# Sprint 1 — Tree-sitter TS/JS AST Parsing

## Goal

Replace the regex-based TypeScript/JavaScript parser (`src/analysis/static_analyzer.py:387-486`) with full tree-sitter AST traversal, bringing TS/JS parsing to parity with the existing Python parser. This is the highest-confidence fix: structured static analysis achieves 84.9% completeness vs 60.3% for pattern matching (PyCG study, arXiv 2410.00603).

**Can run in parallel with**: Sprint 3 (OWASP taxonomy mapping) — no overlapping files.

## Why This Matters for Phase B

A more complete tool catalogue and call graph means Phase B generates scenarios that exercise tools and tool-combinations that the regex parser currently misses. Missed tools = invisible attack surface = blind spots in the test suite.

## What the Regex Parser Currently Misses

The current `parse_typescript_file()` (lines 387-486) uses 5 regex patterns and **cannot extract**:
- Parameter types, defaults, and destructured parameters
- TypeScript decorators (`@decorator`)
- JSDoc comments (which often contain tool descriptions)
- Nested function declarations within object literals
- TypeScript interfaces and type aliases
- Re-exports (`export { X } from './module'`)
- Method definitions inside class bodies (only finds the class name)
- Computed property names and dynamic registrations
- Template literal strings (tool descriptions in backtick strings)

## Tasks

### 1.1 Add tree-sitter TS/JS Dependencies

- [ ] Add `tree-sitter-typescript>=0.23.0` to `requirements.txt` (line 9, after `tree-sitter-python`)
- [ ] Add `tree-sitter-javascript>=0.23.0` to `requirements.txt`
- [ ] Add both to `pyproject.toml` dependencies section
- [ ] Verify installation: `python -c "import tree_sitter_typescript; import tree_sitter_javascript"`

### 1.2 Initialize TS/JS Language Objects

**File**: `src/analysis/static_analyzer.py`

- [ ] Add imports at the top (after line 14):
  ```python
  import tree_sitter_typescript as tstypescript
  import tree_sitter_javascript as tsjavascript
  ```
- [ ] Create language objects (after line 14):
  ```python
  TS_LANGUAGE = Language(tstypescript.language_typescript())
  TSX_LANGUAGE = Language(tstypescript.language_tsx())
  JS_LANGUAGE = Language(tsjavascript.language())
  ```
- [ ] Create parsers for each language

### 1.3 Implement `parse_typescript_file_treesitter()`

**File**: `src/analysis/static_analyzer.py`

Replace the regex-based `parse_typescript_file()` (lines 387-486) with a tree-sitter implementation. Model it on `parse_python_file()` (lines 204-384) but handle TS/JS AST differences.

**Must extract** (matching or exceeding Python parser capabilities):

- [ ] **Imports**: `import_statement`, `import_clause` nodes
  - Handle: `import X from 'Y'`, `import { A, B } from 'Y'`, `import * as X from 'Y'`, `require('Y')`
  - Extract: module path, imported names, aliases

- [ ] **Functions**: `function_declaration`, `arrow_function`, `method_definition` nodes
  - Handle: `function foo()`, `const foo = () =>`, `const foo = function()`, `async function foo()`
  - Extract: name, parameters with types and defaults, return type, body text, `is_async` flag
  - Extract: decorators from `decorator` nodes (TypeScript)
  - Extract: JSDoc from preceding comment nodes (`/** ... */`)
  - Extract: function calls within body (`call_expression` nodes) → populate `calls` list

- [ ] **Classes**: `class_declaration` nodes
  - Extract: name, base classes (from `extends` clause), implements (from `implements` clause)
  - Extract: all methods as `FunctionInfo` objects
  - Extract: class properties/fields
  - Extract: decorators

- [ ] **Variables**: `variable_declaration` nodes with `export` keyword
  - Extract: name, value text (up to 500 chars for normal variables, 6000 for tool arrays)
  - This is critical for tool array detection in `_extract_openai_tools()` (detector.py:195-235)

- [ ] **Type aliases and interfaces**: `type_alias_declaration`, `interface_declaration`
  - Extract as metadata (useful for tool schema detection)

### 1.4 Handle TSX (React) Files

- [ ] Use `TSX_LANGUAGE` for `.tsx` files (JSX syntax in tree-sitter TS grammar)
- [ ] Use `TS_LANGUAGE` for `.ts` files
- [ ] Use `JS_LANGUAGE` for `.js` and `.jsx` files

### 1.5 Update the Dispatcher

**File**: `src/analysis/static_analyzer.py`

- [ ] Update `analyze_files()` (line 489) to route `.ts`, `.tsx`, `.js`, `.jsx` files to the new tree-sitter parser
- [ ] Keep the regex parser as a fallback if tree-sitter fails (graceful degradation)
- [ ] Log a warning when falling back to regex

### 1.6 Extract Function Calls (Call Graph)

The Python parser extracts `calls` (line 163: `_extract_function_calls`). The TS/JS parser must do the same:

- [ ] Walk `call_expression` nodes in function bodies
- [ ] Handle: `foo()`, `this.foo()`, `obj.foo()`, `foo.bar.baz()`, `await foo()`
- [ ] Populate `FunctionInfo.calls` list
- [ ] This is needed by `_extract_custom_tools()` (detector.py:321) which scores functions by what they call (HTTP calls, DB calls, etc.)

### 1.7 Preserve Backward Compatibility

- [ ] The output `FileSymbols` structure must remain identical — same dataclass fields, same types
- [ ] `ToolDefinition` extraction in `detector.py` must work without changes (it reads `FileSymbols.functions`, `.classes`, `.variables`, `.imports`)
- [ ] Verify: `_extract_openai_tools()` can still find tool arrays in `.variables[].value_text`
- [ ] Verify: `_extract_custom_tools()` scoring still works (it reads `body_text` for HTTP/DB indicators)

## Files Modified

| File | Changes |
|------|---------|
| `requirements.txt` | Add `tree-sitter-typescript`, `tree-sitter-javascript` |
| `pyproject.toml` | Add same dependencies |
| `src/analysis/static_analyzer.py` | New TS/JS tree-sitter parser, updated dispatcher |

## Done When

- Running Phase A against a TypeScript agent codebase extracts **all** function signatures, class definitions, imports, decorators, JSDoc comments, and function call graphs
- The `FileSymbols` output for a TS/JS file is structurally identical to what the Python parser produces
- The regex parser still works as a fallback if tree-sitter parsing fails
- All existing tests pass without modification
- Tool extraction (`detector.py`) produces equal or more tools from TS/JS codebases than before

## Validation

```bash
# Run Phase A against a known TS agent codebase and compare tool counts
python analyze.py /path/to/ts-agent --skip-ai -o test_map.json

# Compare: new tool count >= old tool count
# Compare: new function count >= old function count
# Verify: no regressions on Python parsing
python analyze.py /path/to/python-agent --skip-ai -o test_map_py.json
```
