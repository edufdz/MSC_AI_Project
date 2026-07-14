# Plavio Agent Debugger — Phases A to C

## Technical Documentation

> This document provides a detailed technical breakdown of the first three phases of the Plavio Agent Debugger pipeline. Phase A receives the deepest coverage as the foundational analysis stage.

---

## Table of Contents

- [Architecture Overview](#architecture-overview)
- [Phase A: Analyze](#phase-a-analyze)
  - [Pipeline Overview](#a-pipeline-overview)
  - [Step 1: Ingestion](#step-1-ingestion)
  - [Step 2: Static Analysis](#step-2-static-analysis-tree-sitter)
  - [Step 3: Pattern Detection](#step-3-pattern-detection)
  - [Step 4: Risk Analysis](#step-4-risk-analysis)
  - [Step 5: AI Semantic Analysis](#step-5-ai-semantic-analysis)
  - [Step 6: Agent Map Generation](#step-6-agent-map-generation--graph)
  - [API Integration](#a-api-integration)
- [Phase B: Generate Tests](#phase-b-generate-tests)
  - [B1: Coverage Goals](#b1-coverage-goals)
  - [B2: Persona Library](#b2-persona-library)
  - [B3: Scenario Catalog](#b3-scenario-catalog)
  - [B4: Test Suite Assembly](#b4-test-suite-assembly)
- [Phase C: Execute Tests](#phase-c-execute-tests)
  - [Execution Engine](#execution-engine)
  - [Agent Connectors](#agent-connectors)
  - [Conversation Simulator](#conversation-simulator)
  - [GAN Simulator](#gan-simulator-adversarial-mode)
  - [Real-Time Monitor](#real-time-monitor)
  - [Results Aggregation](#results-aggregation)
- [Data Flow Summary](#data-flow-summary)

---

## Architecture Overview

The pipeline follows an artifact-driven architecture where each phase produces JSON files consumed by the next:

```
┌──────────────────┐       ┌──────────────────┐       ┌──────────────────────┐
│   PHASE A        │       │   PHASE B        │       │   PHASE C            │
│   Analyze        │──────▶│   Generate Tests  │──────▶│   Execute Tests      │
│                  │       │                  │       │                      │
│ Input:           │       │ Input:           │       │ Input:               │
│  repo path       │       │  agent_map.json  │       │  test_suite.json     │
│                  │       │                  │       │  agent_map.json      │
│ Output:          │       │ Output:          │       │                      │
│  agent_map.json  │       │  test_suite.json │       │ Output:              │
│  graph.png       │       │  persona_lib.json│       │  test_run_report.json│
│                  │       │  scenario_cat.json│      │  failure_inbox.json  │
│                  │       │  test_config.json │       │  traces/             │
└──────────────────┘       └──────────────────┘       └──────────────────────┘
```

All artifacts are stored in `pipeline_output/{session_id}/` and persist across sessions.

**Tech stack**: Python 3.10+, FastAPI, Tree-sitter, NetworkX, Anthropic SDK, React/TypeScript frontend with WebSocket progress streaming.

---

# Phase A: Analyze

**Purpose**: Scan an agent's source code and produce a structured Agent Map that documents what the agent does, how it works, and what risks it carries.

**Entry points**:
- CLI: `analyze.py`
- API: `POST /api/phase-a/run`

**Source modules**:
| Module | Path | Role |
|--------|------|------|
| Ingestor | `src/ingestion/ingestor.py` | File discovery and prioritization |
| Static Analyzer | `src/analysis/static_analyzer.py` | AST parsing via Tree-sitter |
| Pattern Detector | `src/patterns/detector.py` | Framework, tool, prompt, memory detection |
| Risk Analyzer | `src/risk/analyzer.py` | PII and critical action scanning |
| AI Analyzer | `src/ai_analyzer/analyzer.py` | Claude-powered semantic understanding |
| Graph Builder | `src/graph/builder.py` | Agent Map assembly and graph construction |
| Visualizer | `src/graph/visualizer.py` | PNG and Mermaid diagram generation |
| Framework Signatures | `config/framework_signatures.py` | Signature database for framework detection |

## A: Pipeline Overview

Phase A executes a **6-step sequential pipeline**:

```
repo_path
  │
  ▼
[1. Ingestion]  ──▶  IngestionResult (files sorted by priority, entry points, prompt files)
  │
  ▼
[2. Static Analysis]  ──▶  list[FileSymbols] (functions, classes, imports per file)
  │
  ▼
[3. Pattern Detection]  ──▶  PatternResult (framework, tools, prompts, memory systems)
  │
  ▼
[4. Risk Analysis]  ──▶  list[RiskFlag] (PII, critical actions)
  │
  ▼
[5. AI Semantic Analysis]  ──▶  SemanticAnalysisResult (goal, workflows, dependencies)
  │                              (optional — skipped if skip_ai=True or no API key)
  ▼
[6. Agent Map Generation]  ──▶  agent_map.json + agent_map.png + agent_map.mmd
```

Each step's output feeds into the next. Steps 1–4 are fully offline (no API calls). Step 5 requires an Anthropic API key. Step 6 merges everything into the final artifact.

---

## Step 1: Ingestion

**File**: `src/ingestion/ingestor.py`
**Function**: `ingest_directory(root_path, language_filter=None) → IngestionResult`

### What it does

Traverses the target codebase directory, collects source files relevant to agent analysis, and sorts them by how likely they are to contain agent logic.

### Directory and file filtering

**Excluded directories** (skipped entirely during traversal):
```
__pycache__, .git, .hg, .svn, node_modules, venv, .venv,
env, .env, dist, build, .eggs, *.egg-info, .tox,
.mypy_cache, .pytest_cache, .ruff_cache
```

**Excluded file patterns** (fnmatch):
```
test_*.py, *_test.py, conftest.py, setup.py, setup.cfg
```

**Included file patterns** (agent-relevant globs):
```
**/agent*.py       **/agents/**/*.py     **/tool*.py        **/tools/**/*.py
**/chain*.py       **/chains/**/*.py     **/workflow*.py     **/workflows/**/*.py
**/graph*.py       **/graphs/**/*.py     **/*llm*.py         **/*openai*.py
**/*anthropic*.py  **/prompt*.py         **/prompts/**/*.py  **/crew*.py
**/main.py         **/app.py             **/run.py           **/cli.py
```

### Language detection

Maps file extensions to languages:
| Extension | Language |
|-----------|----------|
| `.py` | python |
| `.js`, `.jsx` | javascript |
| `.ts`, `.tsx` | typescript |
| `.go` | go |
| `.rs` | rust |

If `language_filter` is provided, only files matching that language are kept.

### Priority scoring algorithm

Every file receives a priority score. Higher score = more likely to contain agent logic.

**Keyword bonuses** (checked against lowercase filename):

| Keyword in filename | Points |
|---------------------|--------|
| `agent` | +10 |
| `tool` | +8 |
| `chain`, `workflow`, `graph` | +7 |
| `prompt` | +6 |
| `llm`, `openai`, `anthropic` | +5 |
| Filename is an entry point name | +4 |

**Depth penalty**: If the file is nested more than 4 directories deep → **−2**

**Entry point names** (recognized as canonical entry points):
```
main.py, app.py, run.py, cli.py, agent.py, server.py, __main__.py
```

### Prompt file discovery

Separately, `find_prompt_files()` scans for files with these extensions that also have "prompt" in their name:
```
.txt, .md, .prompt, .jinja, .jinja2
```

### Output data structure

```python
@dataclass
class FileInfo:
    path: str              # absolute path
    relative_path: str     # relative to root
    language: str          # "python", "javascript", etc.
    size_bytes: int
    is_entry_point: bool
    priority: int          # higher = more agent-relevant

@dataclass
class IngestionResult:
    root_path: str
    project_type: str      # most frequent language ("python", "javascript", etc.)
    files: list[FileInfo]  # sorted by priority (descending)
    entry_points: list[str]
    total_files_scanned: int
    prompt_files: list[str]
```

---

## Step 2: Static Analysis (Tree-sitter)

**File**: `src/analysis/static_analyzer.py`
**Function**: `analyze_files(file_paths: list[str]) → list[FileSymbols]`

### What it does

Parses each source file into an AST and extracts structural information: functions, classes, imports, variables, and their relationships.

### Parsing strategies

| Language | Parser | Method |
|----------|--------|--------|
| Python | Tree-sitter (`tree-sitter-python`) | Full AST traversal |
| TypeScript/JavaScript | Regex-based | Pattern matching fallback |

### Python parsing (`parse_python_file`)

Uses the Tree-sitter Python grammar to walk the AST. Extracts:

**Functions**:
- Name, parameters (with type annotations and defaults), docstring
- All `@decorator` names
- Full body text (source code)
- `is_async` flag
- `calls`: list of function names called within the body (found by walking `call` AST nodes)

**Classes**:
- Name, base classes, docstring, decorators
- All methods (parsed as `FunctionInfo`)
- Class-level variable assignments: `(name, value_snippet)`

**Imports**:
- Module path, imported names, aliases
- Handles `from X import Y`, `import X`, and `from X import *`

**Variables**:
- Top-level assignments: name and value text (truncated to 500 characters)

### TypeScript/JavaScript parsing (`parse_typescript_file`)

Uses regex patterns since Tree-sitter TS grammar isn't bundled:

**Import pattern**:
```regex
import\s+(?:(?:\{[^}]*\}|\*\s+as\s+\w+|\w+)...
```

**Function patterns** (3 variants):
```regex
(?:export\s+)?(?:async\s+)?function\s+(\w+)\s*\(
(?:export\s+)?const\s+(\w+)\s*=\s*(?:async\s*)?\([^)]*\)\s*=>
(?:export\s+)?(?:async\s+)?(\w+)\s*:\s*\([^)]*\)\s*=>
```

**Class pattern**:
```regex
(?:export\s+)?class\s+(\w+)
```

Body text is truncated to 500 characters for TS/JS functions.

### Error handling

Parse errors are collected in `parse_errors` but **never stop processing**. A file with syntax errors still yields whatever could be extracted.

### Output data structures

```python
@dataclass
class FunctionInfo:
    name: str
    params: list[ParamInfo]          # [{name, type_annotation, default}]
    docstring: str | None
    decorators: list[str]
    body_text: str                   # source code of body
    location: Location               # {file, line, column}
    is_async: bool
    calls: list[str]                 # function names called within

@dataclass
class ClassInfo:
    name: str
    bases: list[str]                 # base class names
    docstring: str | None
    methods: list[FunctionInfo]
    decorators: list[str]
    location: Location
    class_variables: list[tuple[str, str | None]]

@dataclass
class ImportInfo:
    module: str
    names: list[str]                 # ["*"] for star imports
    alias: str | None
    location: Location

@dataclass
class FileSymbols:
    file_path: str
    language: str
    functions: list[FunctionInfo]
    classes: list[ClassInfo]
    imports: list[ImportInfo]
    variables: list[VariableInfo]    # [{name, value_text, location}]
    parse_errors: list[str]
```

---

## Step 3: Pattern Detection

**File**: `src/patterns/detector.py`
**Function**: `detect_patterns(all_symbols, prompt_files, prompt_encoding) → PatternResult`

This is the most complex step. It runs four detection sub-systems.

### 3A: Framework Detection

**Function**: `detect_framework(all_symbols) → (framework_name, confidence)`

Scores each known framework by scanning all `FileSymbols` for matching imports, decorators, and class bases.

**Scoring rules**:
| Match type | Points per match |
|------------|-----------------|
| Import matches a framework's import pattern | +2 |
| Decorator matches a framework's decorator list | +3 |
| Class base matches a framework's class list | +3 |

**Confidence normalization**: `min(score / 20.0, 1.0)`

If the best score is 0, returns `("custom", 0.0)`.

**Known frameworks** (from `config/framework_signatures.py`):

| Framework | Key imports | Key classes | Key decorators |
|-----------|-------------|-------------|----------------|
| `langchain` | `from langchain`, `from langchain.agents`, `.tools`, `.chains` | `BaseTool`, `StructuredTool`, `AgentExecutor`, `LLMChain` | `@tool`, `@chain` |
| `langgraph` | `from langgraph.graph`, `.prebuilt`, `.checkpoint` | `StateGraph`, `MessageGraph`, `Graph` | — |
| `openai_native` | `from openai`, `import openai` | `OpenAI`, `AsyncOpenAI` | — |
| `anthropic_native` | `from anthropic`, `import anthropic` | `Anthropic`, `AsyncAnthropic` | — |
| `crewai` | `from crewai` | `Agent`, `Task`, `Crew`, `Process` | `@task`, `@agent` |
| `autogpt` | `from autogpt` | `Agent`, `AutoGPT` | — |

### 3B: Tool Extraction

Four strategies run cumulatively, with deduplication at the end (highest confidence wins per name).

#### Strategy 1: LangChain tools

Finds functions decorated with `@tool` and classes extending `BaseTool`, `StructuredTool`, or `Tool`.

For class-based tools, looks for `_run`, `_arun`, or `run` methods to extract parameters and docstrings.

Source label: `"langchain_decorator"` or `"langchain_class"`.

#### Strategy 2: OpenAI/Claude tool arrays

Searches all variables for tool definition arrays. A variable is considered a tool array if:
- Name contains: `tools`, `functions`, `function_definitions`, `tool_definitions`, `tool_list`, `tool_defs`, `agent_tools`
- OR name ends with `"tools"` and has length > 4
- AND name does NOT contain: `execute`, `handler`, `node`, `runner`
- AND value text length ≥ 50 characters

Extracts tool names and descriptions via regex:
```regex
"name"\s*:\s*"([^"]+)"
"description"\s*:\s*"([^"]+)"
```

Source label: `"openai_function_calling"`. Confidence: `0.8`.

#### Strategy 3: One-tool-per-file

Scans files whose paths look like tool definition directories:
- Contains `/tools/` or `tools`
- Contains `agent` + (`tool` | `definition` | `skill`)
- Contains `/skills/` or `skill`

Extracts the first `name` and `description` found in each file via regex:
```regex
\bname\s*:\s*["']([^"']+)["']
\bdescription\s*:\s*["']([^"']+)["']
```

Filters by name length (2–60 chars) and excludes type keywords.

Source label: `"openai_tool_file"`. Confidence: `0.85`.

#### Strategy 4: Custom heuristic scoring

For every function across all files, computes a tool-likelihood score:

| Indicator | Points |
|-----------|--------|
| HTTP/API calls (`requests.`, `httpx.`, `aiohttp.`, `fetch(`, `axios`) | +3 |
| Database calls (`execute`, `query`, `cursor.`, `session.`, `db.`) | +2 |
| API route file (detected by pattern) | +3 |
| Route handler function (`get`, `post`, `put`) | +2 |
| Tool-like naming (`tool`, `action`, `execute`, `run_`, `handler`) | +2 |
| Descriptive docstring (> 20 chars) | +1 |
| Type-annotated parameters | +1 |
| Exported function (TypeScript) | +1 |

**Threshold**: score ≥ 3 → included as tool.
**Confidence**: `min(score / 8.0, 1.0)`.

**Executor exclusions** — these patterns are filtered out (they invoke tools, not are tools):
```
executetool, execute_tool, runtool, run_tool, createtoolsnode,
create_tools_node, toolsnode, tools_node, handletool, process_tool,
tool_executor, tool_execution, invoketool, dispatch_tool
```

Source label: `"custom_heuristic"`.

#### Tool data structure

```python
@dataclass
class ToolDefinition:
    id: str                # lowercase_with_underscores
    name: str
    description: str | None
    parameters: list[dict] # [{name, type, default}]
    source: str            # langchain_decorator | openai_function_calling | custom_heuristic | openai_tool_file
    location: dict         # {file, line}
    confidence: float      # [0.0, 1.0]
    risk_level: str        # low | medium | high | critical
    sandbox_safe: bool
    code_snippet: str | None  # up to 500 chars
```

### 3C: Prompt Extraction

Three strategies:

1. **Named variables**: finds variables whose names contain `prompt`, `system`, `instruction`, `template`, or `persona`. Must be > 50 characters. Extracts `{variable}` template patterns.

2. **PromptTemplate objects**: regex for `template\s*=\s*["'](.+?)["']` in `PromptTemplate` / `ChatPromptTemplate` instantiations.

3. **Prompt files**: reads files from the prompt file list (Step 1), truncates content to 2000 characters.

```python
@dataclass
class PromptDefinition:
    name: str
    type: str           # system_prompt | template | file
    content: str        # up to 2000 chars
    variables: list[str]
    location: dict
```

### 3D: Memory System Detection

Scans imports and class instantiations for known patterns:

| Memory type | Detection patterns |
|-------------|-------------------|
| `conversation_buffer` | `ConversationBufferMemory`, `ConversationSummaryMemory`, `ConversationBufferWindowMemory`, `ConversationTokenBufferMemory`, `VectorStoreRetrieverMemory` |
| `vector_store` | `Pinecone`, `Chroma`, `FAISS`, `Weaviate`, `Qdrant`, `Milvus`, `PGVector` |
| `persistent_state` | `redis`, `psycopg`, `pymongo`, `sqlite3`, `sqlalchemy`, `motor`, `aioredis` |
| `class_state` | Class variables with state-like names |

```python
@dataclass
class MemorySystem:
    type: str            # conversation_buffer | vector_store | persistent_state | class_state
    implementation: str  # class name or module
    location: dict
```

### Pattern Detection output

```python
@dataclass
class PatternResult:
    framework: str
    framework_confidence: float
    tools: list[ToolDefinition]
    prompts: list[PromptDefinition]
    memory_systems: list[MemorySystem]
```

---

## Step 4: Risk Analysis

**File**: `src/risk/analyzer.py`
**Function**: `analyze_risks(tools, prompts) → list[RiskFlag]`

### PII Detection

Scans tool parameters, descriptions, code snippets, and prompt content against regex patterns:

| PII type | Pattern |
|----------|---------|
| Email | `\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z\|a-z]{2,}\b` |
| Phone | `\b\d{3}[-.]?\d{3}[-.]?\d{4}\b` |
| SSN | `\b\d{3}-\d{2}-\d{4}\b` |
| Credit card | `\b\d{4}[- ]?\d{4}[- ]?\d{4}[- ]?\d{4}\b` |
| Address | keyword match: `address`, `street`, `city`, `state`, `zip`, `postal` |

Severity: `"high"` for parameter names and prompts, `"medium"` for code patterns.

### Critical Action Detection

Searches tool name + description + code snippet (all lowercased) for action keywords:

| Category | Keywords | Severity |
|----------|----------|----------|
| Financial | `payment`, `charge`, `refund`, `purchase`, `transaction`, `billing`, `invoice`, `transfer`, `withdraw` | **critical** |
| Data modification | `delete`, `remove`, `update`, `modify`, `drop`, `truncate` | high |
| User management | `create_user`, `delete_user`, `change_password`, `grant_access`, `revoke_access` | high |
| Communication | `send_email`, `send_sms`, `notify`, `alert`, `post_message` | high |

### Deduplication

One risk flag per unique `(tool, risk_type, pii_type)` combination.

```python
@dataclass
class RiskFlag:
    location: dict        # {file, line}
    tool: str | None
    risk_type: str        # pii | critical_action | data_modification
    pii_type: str | None  # email | phone | ssn | credit_card | address
    severity: str         # low | medium | high | critical
    description: str
    mitigation: str | None
```

---

## Step 5: AI Semantic Analysis

**File**: `src/ai_analyzer/analyzer.py`
**Function**: `run_semantic_analysis(...) → SemanticAnalysisResult`

**Prerequisites**: `ANTHROPIC_API_KEY` set, `skip_ai=False`.
**Model**: `claude-sonnet-4-5-20250929`
**Max tokens per call**: 4096
**Context limit**: 80,000 characters

This step sends agent context to Claude for four independent semantic analyses.

### Context building

`_build_context_summary()` creates a compact text representation:
- Framework name
- File list (all analyzed files)
- Imports (up to 30)
- Tool summaries (up to 20, with code snippets)
- Prompt content (up to 5)
- Entry point source code

Total context is capped at 80K characters.

### Sub-analysis 1: Goal Understanding

**Prompt**: `GOAL_UNDERSTANDING_PROMPT` (from `src/ai_analyzer/prompts.py`)

Claude determines:
1. **Purpose**: brief description of what the agent does
2. **Domain**: one of `support | sales | scheduling | ops | research | coding | data | custom`
3. **Capabilities**: list of things the agent can do
4. **Success criteria**: measurable outcomes
5. **Confidence**: 0.0–1.0

### Sub-analysis 2: Tool Semantics

**Prompt**: `TOOL_ANALYSIS_PROMPT`

Processes tools in **batches of 10** to stay within context limits.

Per tool, Claude determines:
- `purpose`: what the tool actually does (beyond its name)
- `required_inputs`: human-readable list
- `output`: what the tool returns
- `read_only`: whether it modifies state
- `handles_sensitive_data`: boolean
- `sensitive_data_types`: list (e.g., `["email", "payment_info"]`)
- `dependencies`: other tools it requires
- `risk_level`: `low | medium | high | critical`

### Sub-analysis 3: Workflow Analysis

**Prompt**: `WORKFLOW_ANALYSIS_PROMPT`

Claude determines:
- `decision_strategy`: `react | plan-and-execute | function-calling | state-machine | custom`
- `typical_flow`: ordered list of steps in a normal conversation
- `error_handling`: strategies for `timeout`, `malformed_response`, `tool_failure`
- `guardrails`: safety measures in place
- `ambiguity_handling`: how the agent handles unclear requests

### Sub-analysis 4: Dependency Analysis

**Prompt**: `DEPENDENCY_ANALYSIS_PROMPT`

Processes up to **15 tools**. Claude determines:
- `dependencies`: `[{tool, requires: [other_tools], reason}]`
- `mutually_exclusive`: groups of tools that conflict
- `common_sequences`: typical tool call orderings
- `circular_dependency_risks`: tools involved in cycles

### JSON parsing

Claude responses are expected as JSON. The parser strips markdown fences (` ```json ... ``` `) before parsing. On parse failure, the sub-analysis is skipped with an error.

### Output

```python
@dataclass
class SemanticAnalysisResult:
    goal: GoalAnalysis | None
    tool_semantics: list[ToolSemanticInfo]
    workflow: WorkflowAnalysis | None
    dependency_analysis: DependencyAnalysis | None
```

---

## Step 6: Agent Map Generation & Graph

**File**: `src/graph/builder.py`
**Function**: `generate_agent_map(...) → dict`

### Graph construction

`build_architecture_graph()` creates a `NetworkX DiGraph` with:

**Nodes**:

| Node | Type | Attributes |
|------|------|------------|
| `agent` | agent | framework, purpose, domain |
| `orchestrator` | orchestrator | decision_strategy |
| `planner` | planner | (only if strategy = "plan-and-execute") |
| `tool_{id}` | tool | name, description, source, risk_level (per tool) |
| `memory` | memory_subsystem | (if memory systems exist) |
| `memory_{type}_{i}` | memory | type, implementation |
| `retrieval` | retrieval_subsystem | (if vector stores exist) |
| `retrieval_{impl}_{i}` | retrieval | type, implementation |

**Edges**:

| Source → Target | Relationship |
|-----------------|-------------|
| agent → orchestrator | contains |
| orchestrator → tool_* | invokes |
| orchestrator → planner | delegates |
| tool_* → tool_* | requires (from dependency analysis) |
| agent → memory | uses |
| memory → memory_* | contains |
| agent → retrieval | uses |
| retrieval → retrieval_* | contains |

### Conversation language detection

`_detect_conversation_language(prompts)` counts Spanish indicators in prompt content:

**Spanish words** (30 words): `bienvenido`, `hola`, `servicio`, `cliente`, `cita`, `reserva`, `consulta`, etc.

**Spanish characters**: `¿`, `¡`, `ñ`, `á`, `é`, `í`, `ó`, `ú`, `ü`

**Threshold**: score ≥ 3 → `"Spanish"`, otherwise `"English"`.

### Final Agent Map structure

```json
{
  "version": "1.0",
  "generated_at": "ISO 8601 timestamp",
  "agent_id": "UUID",

  "metadata": {
    "name": "Agent",
    "type": "domain from goal analysis (or 'custom')",
    "framework": "langchain | crewai | openai_native | custom | ...",
    "framework_confidence": 0.0-1.0,
    "language": "python",
    "purpose": "from AI goal analysis (or 'Unknown')",
    "capabilities": ["capability_1", "capability_2"],
    "conversation_language": "Spanish | English"
  },

  "components": {
    "orchestrator": {
      "type": "react | plan-and-execute | function-calling | ...",
      "error_handling": {"timeout": "...", "malformed_response": "..."},
      "guardrails": ["guardrail_1"],
      "typical_flow": ["step_1", "step_2"],
      "ambiguity_handling": "..."
    },
    "tools": [
      {
        "id": "tool_id",
        "name": "Tool Name",
        "description": "what it does (AI-enhanced if available)",
        "parameters": [{"name": "param", "type": "str", "default": null}],
        "dependencies": ["other_tool"],
        "sandbox_safe": true,
        "risk_level": "low | medium | high | critical",
        "read_only": true,
        "handles_sensitive_data": false,
        "source": "langchain_decorator | openai_function_calling | ...",
        "confidence": 0.95,
        "location": {"file": "path/to/file.py", "line": 42}
      }
    ],
    "memory": {
      "systems": [{"type": "...", "implementation": "...", "location": {...}}],
      "conversation_history": true,
      "persistent_state": false
    },
    "retrieval": {
      "systems": [{"type": "vector_store", "implementation": "FAISS", "location": {...}}],
      "exists": true
    },
    "prompts": [
      {
        "name": "system_prompt",
        "type": "system_prompt | template | file",
        "content": "first 2000 chars...",
        "variables": ["user_name", "context"],
        "location": {"file": "...", "line": 10}
      }
    ]
  },

  "success_criteria": {
    "task_completion": ["criteria from AI analysis"],
    "max_latency_ms": 10000,
    "max_cost_per_conversation": 1.00,
    "max_turns": 20
  },

  "risk_flags": {
    "pii_handling": true,
    "critical_actions": ["payment_tool", "delete_user"],
    "all_risks": [
      {
        "tool": "payment_tool",
        "risk_type": "critical_action",
        "pii_type": null,
        "severity": "critical",
        "description": "Financial operation: payment",
        "mitigation": "Require user confirmation before execution",
        "location": {"file": "...", "line": 55}
      }
    ]
  },

  "graph": {
    "nodes": [
      {"id": "agent", "type": "agent", "framework": "langchain", "purpose": "..."},
      {"id": "orchestrator", "type": "orchestrator", "strategy": "react"},
      {"id": "tool_search", "type": "tool", "name": "search", "risk_level": "low"}
    ],
    "edges": [
      {"source": "agent", "target": "orchestrator", "relationship": "contains"},
      {"source": "orchestrator", "target": "tool_search", "relationship": "invokes"}
    ]
  },

  "source_files": {
    "analyzed_files": ["path/to/file1.py", "path/to/file2.py"],
    "entry_points": ["path/to/main.py"],
    "repository": "/absolute/path/to/repo"
  }
}
```

### Visualization

**File**: `src/graph/visualizer.py`
**Function**: `visualize_agent_map(agent_map, output_dir) → (png_path, mmd_path)`

Generates two outputs:

**PNG** (`_render_png`):
- Multipartite layout: Agent (layer 0) → Orchestrator (layer 1) → Tools (layer 2) → Memory/Retrieval (layers 3–4)
- Color-coded by node type and risk level
- Dark theme, DPI 150, dynamically sized figure

**Node colors**:
| Node type | Color |
|-----------|-------|
| Agent | `#6366f1` (indigo) |
| Orchestrator | `#3b82f6` (blue) |
| Planner | `#06b6d4` (cyan) |
| Tool (low risk) | `#22c55e` (green) |
| Tool (medium risk) | `#f97316` (orange) |
| Tool (high risk) | `#ef4444` (red) |
| Memory | `#a855f7` (purple) |
| Retrieval | `#06b6d4` (cyan) |

**Mermaid** (`_render_mermaid`):
- Node shapes: `[[label]]` for agent/orchestrator, `(label)` for tools, `[(label)]` for memory/retrieval
- CSS classes for risk coloring
- Subgraphs for Memory and Retrieval subsystems

---

## A: API Integration

**File**: `web/api/routes/phase_a.py`

### Endpoints

**`POST /api/phase-a/run`** — starts Phase A asynchronously.

Request:
```python
class PhaseARequest:
    session_id: str
    repo_path: str
    skip_ai: bool = False
    language: str | None = None
    prompt_encoding: str = "utf-8"
```

Response: `{"status": "started", "session_id": "..."}`

**`GET /api/phase-a/status/{session_id}`** — polls for status.

### Progress events (via WebSocket)

| Step | Message | Progress % |
|------|---------|-----------|
| Ingestion | `scanning_codebase` | 10% |
| Static analysis | `parsing_treesitter` | 25% |
| Pattern detection | `detecting_patterns` | 45% |
| Risk analysis | `analyzing_risks` | 60% |
| AI analysis | `ai_analysis` | 70% |
| Building map | `building_map` | 90% |
| Complete | `phase_complete` | 100% |

### Error handling

- Exceptions are caught, phase status set to `"error"`, and a `phase_error` event emitted
- Graph generation failure (e.g., matplotlib missing) is a graceful skip, not a fatal error
- Session artifacts are persisted even on partial completion

---

# Phase B: Generate Tests

**Purpose**: Consume the Agent Map and produce a comprehensive test suite with personas, scenarios, and coverage guarantees.

**Entry points**:
- CLI: `generate_tests.py`
- API: `POST /api/phase-b/run`

Phase B runs four sub-steps sequentially: B1 → B2 → B3 → B4.

## B1: Coverage Goals

**File**: `src/coverage/calculator.py`

Reads the tool inventory from `agent_map` and computes:

### Minimum invocations per tool (by risk level)

| Risk level | Min calls |
|------------|-----------|
| Critical | 25 |
| High | 15 |
| Medium | 10 |
| Low | 5 |

### Tool combinations

Generates pairs of high/critical-risk tools (up to 10 pairs) for combination testing.

### Edge-case coverage (scales with risk profile)

| Edge case | Base count | Multiplied by risk multiplier |
|-----------|-----------|-------------------------------|
| Ambiguous requests | 40 | critical: ×2.0, high: ×1.5, medium: ×1.0, low: ×0.8 |
| Incomplete information | 35 | same multipliers |
| User changes mind | 20 | same multipliers |
| Contradictory statements | 15 | same multipliers |

### Stressor coverage (scales with tool count)

| Stressor | Base count | Scaled by tool count |
|----------|-----------|---------------------|
| Timeout scenarios | 50 | × scale factor |
| Malformed responses | 25 | × scale factor |
| Data conflicts | 30 | × scale factor |

### Sandbox configuration

- Critical/high-risk tools → **mock mode** with confirmation required
- Cost limits: `max_llm_cost_per_episode`: min(success_criteria.max_cost, 0.10), `max_total_cost_per_run`: 50.00
- Safety: `max_turns_per_episode`: 20, `timeout_per_tool_call_sec`: 10, `block_real_external_calls`: true

---

## B2: Persona Library

**File**: `src/personas/builder.py`
**Models**: `src/personas/models.py`
**Templates**: `src/personas/templates.py`

### Persona data model

Each persona has three dimensions:

**Traits** (all integers 1–10):
| Trait | 1 means | 10 means |
|-------|---------|----------|
| Patience | Impatient | Very patient |
| Clarity | Vague communicator | Crystal clear |
| Tech savviness | Technophobe | Expert |
| Politeness | Rude | Very polite |
| Verbosity | Terse | Wordy |
| Emotional volatility | Stoic | Extreme mood swings |
| Trust level | Suspicious | Blind trust |
| Detail orientation | Big-picture only | Obsessively detailed |
| Decision speed | Agonizes | Instant decisions |
| Language proficiency | Broken language | Fluent |

**Style**:
- `tone`: polite | neutral | frustrated | angry
- `formality`: formal | casual | slang
- `typo_rate`: 0.0–1.0
- `abbreviation_use`: low | medium | high
- `emoji_use`: none | rare | moderate | frequent

**Edge behaviors** (booleans):
- `rage_quits`, `changes_mind`, `provides_incomplete_info`, `asks_off_topic`, `tests_boundaries`

### Archetype classification

A persona is automatically classified based on traits:
- **adversarial**: low politeness + tests boundaries or rage quits
- **demanding_expert**: high tech savviness + detail orientation + low patience
- **confused_novice**: low clarity + low tech savviness
- **rambler**: high verbosity + off-topic tendency
- **ideal_customer**: high patience + clarity + politeness
- **general**: default

### Persona sources

| Source | Method | Details |
|--------|--------|---------|
| Templates | `load_templates()` | 20+ hardcoded personas across support/sales/scheduling/research/coding domains. Spanish and Portuguese translations available. |
| AI-generated | `generate_personas(count)` | Claude creates diverse personas based on agent type, tools, and trait gap analysis. Deduplicates via cosine similarity (threshold 0.85 on 10 traits). |
| Tool-attack | `generate_tool_attack_personas()` | One persona per tool, designed to stress that specific tool. Risk-based trait profiles. Adapts to parameter complexity, chain position, read-only status, sensitive data. |
| Flow-attack | `generate_flow_attack_personas()` | One persona per tool chain. Patience inversely proportional to chain length: `base_patience = max(2, 7 - chain_len)`. |
| External | `load_from_external(data_dir)` | Reads `personas.json` from external packs (Tlahuac format). |

---

## B3: Scenario Catalog

**File**: `src/scenarios/library.py`
**Models**: `src/scenarios/models.py`
**Templates**: `src/scenarios/templates.py`

### Scenario data model

```python
Scenario:
    scenario_id, title, description, user_goal
    category: support | sales | scheduling | ...
    difficulty: easy | medium | hard
    type: happy_path | error_path | edge_case
    required_tools: list[str]
    optional_tools: list[str]
    forbidden_tools: list[str]
    success_conditions:
        tool_called: str | None           # single tool expected
        tools_called: list[str] | None    # multiple tools expected
        user_satisfied: bool
        info_provided: list[str] | None   # specific info expected
    failure_conditions:
        hallucinated_response: bool
        wrong_tool_called: bool
        pii_leaked: bool
    chaos_config:
        inject_timeout: float             # probability, default 0.1
        inject_malformed_response: float  # default 0.05
        inject_data_conflict: float       # default 0.08
    estimated_turns: int                  # default 5
    starter_openers: list[str]            # pre-written first messages
    variant_type: str | None              # ambiguity | missing_info | interruption | constraint | error
```

### Scenario sources

| Source | Details |
|--------|---------|
| Templates | 50+ built-in scenarios across domains (order tracking, refunds, booking, pricing, etc.) |
| AI-generated | Claude creates scenarios tailored to the agent's tools and risk profile |
| Variants (AI) | 7 variant dimensions: ambiguity, missing_info, interruption, constraint, error, multi_step, adversarial |
| Variants (offline) | 5 deterministic variants per base: ambiguity, missing_info, interruption, error_path, adversarial |
| External | Loaded from Tlahuac packs |

---

## B4: Test Suite Assembly

**File**: `src/generator/test_suite.py`

### 4-phase allocation strategy

The generator fills `target_count` test slots (default 150) using a priority-based allocation:

1. **Tool coverage tests**: guarantee each tool reaches its minimum invocations (from B1). Prefer tool-attack personas. Generate tool-combination tests.

2. **Edge-case tests**: allocate tests for ambiguity, missing info, changes mind, contradictions. Map variant_type → edge-case scenario type.

3. **Stressor tests**: chaos injection tests (timeout, malformed response, data conflict). Override chaos_config with high injection probabilities. Prefer error_path scenarios.

4. **Scenario fill**: pad remaining slots with random persona × scenario pairs.

### Execution config per test

```python
ExecutionConfig:
    max_turns: 40
    timeout_per_tool_call_sec: 10
    sandbox_mode: str
    chaos_injection:
        inject_timeout: float
        inject_malformed_response: float
        inject_data_conflict: float
```

### Cost and duration estimates

- **Duration**: `scenario.estimated_turns × 6 seconds` per test
- **Cost**: `total_turns × $0.002` per turn

### Output

`test_suite.json` containing all test cases + summary with breakdowns by difficulty, coverage goal, scenario type, persona, and tool invocation counts.

---

# Phase C: Execute Tests

**Purpose**: Run the test suite against the agent (mock or real) and collect results with live monitoring.

**Entry points**:
- CLI: `execute_tests.py`
- API: `POST /api/phase-c/run`

## Execution Engine

**File**: `src/execution/runner.py`
**Class**: `TestExecutionEngine`

### Parallel execution

- Uses `asyncio.Semaphore` for bounded parallelism (default 10 workers)
- Staggers test starts by **0.5 seconds** to avoid thundering herd
- Emits `run_started` event with full test list

### Timeout calculation

```python
restarts = (max_restarts + 1) if use_gan else 1
timeout_sec = restarts * max_turns * 6 + 60
```

### Minimum turns for genuine failure

If a test fails in fewer than **6 turns**, it's classified as a connection error rather than a genuine agent failure.

---

## Agent Connectors

**File**: `src/execution/agent_connector.py`

Three connector implementations:

### MockAgentConnector

Simulates agent responses locally. No external API calls.

| Parameter | Default | Purpose |
|-----------|---------|---------|
| `fail_rate` | 0.05 | 5% chance of simulated failure |
| `tool_call_rate` | 0.4 | 40% chance response includes tool calls |
| `latency_range` | (50, 300) ms | Random simulated latency |

Simulates tool chains: tracks current chain position, calls tools in sequence, emits confirmation on chain completion.

### APIAgentConnector

Sends HTTP POST to the agent's endpoint.

- Endpoint: from `agent_map.api_endpoint`
- Timeout: 120s (accounts for LLM processing latency)
- Payload: `{"message": str, "session_id": str}`
- Headers: Content-Type + optional Bearer auth

### VictoriaConnector

Specialized connector for Victoria-framework agents.

- Class-level semaphore: **3 concurrent requests** (shared across all instances)
- Retry strategy: exponential backoff with jitter, max 2 retries, base 3.0s
- Authentication: session cookie from environment variable `VICTORIA_SESSION_COOKIE`
- Flow: create conversation → send debug messages → extract tool calls from actions array

---

## Conversation Simulator

**File**: `src/execution/conversation_simulator.py`
**Class**: `ConversationSimulator`

### Conversation flow

```
1. Reset agent connection
2. Generate first persona message (from scenario.starter_openers or AI)
3. Loop until max_turns or termination:
   a. Maybe inject chaos event (timeout, malformed response, data conflict)
   b. Send message to agent
   c. Record user turn + agent turn
   d. Emit tool_called events
   e. Check success/failure conditions
   f. Generate follow-up persona message
   g. Update mood state
4. Return TestResult
```

### Mood drift model

The simulator tracks persona mood throughout the conversation:

```python
MoodState:
    frustration: float [0-10]         # escalates with failures
    trust: float [0-10]               # initialized from persona.trust_level
    current_patience: float [0-10]    # initialized from persona.patience
    escalation_level: int [0-3]       # 0=calm, 1=annoyed, 2=frustrated, 3=angry
    turns_without_progress: int       # increments when no success detected
```

### Chaos injection

`_maybe_inject_chaos(turn_count)` rolls against chaos_config probabilities:
- **Timeout**: skips agent call entirely, returns `"[CHAOS] timeout"` message
- **Malformed response**: corrupts the agent response before persona sees it
- **Data conflict**: injects contradictory information

### Persona message generation

- **AI mode** (`use_ai_personas=True`): Claude drives persona dialogue, respecting traits, style, edge behaviors, and mood drift
- **Offline mode** (`use_ai_personas=False`): randomized templates based on persona archetype — deterministic and free

### Callback hook

The simulator accepts an `on_agent_turn` callback:
```python
async (turns, agent_turn_count) → Optional[dict]
    None          → continue normally
    {"action": "restart", "reason": "..."}   → abort conversation
    {"action": "continue", "coaching": "..."} → inject coaching into persona
```

This hook is used by the GAN simulator's Critic agent.

---

## GAN Simulator (Adversarial Mode)

**File**: `src/execution/gan_simulator.py`
**Class**: `GANConversationSimulator`

### Architecture

```
Generator (ConversationSimulator + Persona LLM)
          ↕ conversation turns ↕
Critic Agent (evaluates quality every N turns)
          ↕ coaching / restart ↕
```

### Configuration

| Parameter | Default | Purpose |
|-----------|---------|---------|
| `evaluate_every` | 2 | Critic evaluates every N agent turns |
| `max_restarts` | 2 | Maximum conversation restarts |
| `quality_threshold` | 3.0 | Minimum quality (0–10) to avoid restart |

### Flow

1. Start conversation via ConversationSimulator
2. After every `evaluate_every` agent turns, Critic evaluates:
   - **"restart"**: conversation quality too low → discard and retry
   - **"continue"** with coaching: inject guidance into persona's next message
   - **"accept"**: quality is good enough → use this result
3. Track best attempt by quality_score across restarts
4. Stop after `max_restarts` failures → use best attempt

### Critic modes

- **AI Critic** (`CriticAgent`): LLM-based quality evaluation
- **Offline Critic** (`OfflineCriticAgent`): heuristic-based (no API calls)

### Cost impact

~2× LLM calls per test (Generator + Critic). Worst case with restarts: ~6×.

---

## Real-Time Monitor

**File**: `src/execution/monitor.py`
**Class**: `RealTimeMonitor`

Consumes events from the execution queue at ~4 refreshes/second.

### Tracked metrics

- Completed / passed / failed / errors / timeouts / running
- Total cost, total duration
- Recent failures and passes (last 5 each)
- Breakdown by difficulty level
- Pass rate percentage

### Events consumed

| Event | Action |
|-------|--------|
| `test_started` | Increment running counter |
| `test_completed` | Update counters based on status |
| `tool_called` | Track tool coverage |
| `run_completed` | Stop monitoring loop |

### Display

Rich Live display with: progress bar, worker count, elapsed time + ETA, pass/fail/error/timeout counts, difficulty breakdown.

---

## Results Aggregation

**File**: `src/execution/aggregator.py`
**Class**: `ResultsAggregator`

### Test run report (`test_run_report.json`)

```python
TestRunReport:
    total_tests, passed, failed, errors, timeouts
    pass_rate: float
    total_duration_sec, avg_duration_sec
    total_cost_usd: float
    tool_coverage: dict[str, int]       # invocations per tool
    tools_not_covered: list[str]        # tools with 0 invocations
    coverage_pct: float                 # (expected - missed) / expected × 100
    by_difficulty: dict[str, dict]      # easy/medium/hard breakdown
    by_coverage_goal: dict[str, dict]
```

### Failure inbox (`failure_inbox.json`)

Filters tests with status `failed | error | timeout`. Per failure:
- Test metadata (ID, scenario, persona, difficulty)
- Failure reason
- Tools called sequence
- Chaos events injected
- Conversation trace (full turn-by-turn)

### Passed inbox (optional)

Extracts passed tests with trace files for false-success detection during optional AI validation.

---

## Data Flow Summary

```
                    PHASE A                         PHASE B                           PHASE C
┌─────────────────────────────────┐   ┌──────────────────────────────┐   ┌────────────────────────────────┐
│                                 │   │                              │   │                                │
│  repo_path                      │   │  agent_map.json              │   │  test_suite.json               │
│    ↓                            │   │    ↓                         │   │  agent_map.json                │
│  [Ingest] → files + priorities  │   │  [B1] → coverage goals      │   │    ↓                           │
│    ↓                            │   │    ↓                         │   │  [Connector] mock/API/Victoria │
│  [Parse] → AST symbols         │   │  [B2] → persona library      │   │    ↓                           │
│    ↓                            │   │    ↓                         │   │  [Simulator] conversation loop │
│  [Detect] → framework, tools,  │   │  [B3] → scenario catalog     │   │    ↓                           │
│            prompts, memory      │   │    ↓                         │   │  [Monitor] real-time events    │
│    ↓                            │   │  [B4] → test suite assembly  │   │    ↓                           │
│  [Risk] → PII, critical actions│   │                              │   │  [Aggregate] report + inbox    │
│    ↓                            │   │  Outputs:                    │   │                                │
│  [AI] → goal, workflow, deps   │   │   test_suite.json            │   │  Outputs:                      │
│    ↓                            │   │   persona_library.json       │   │   test_run_report.json         │
│  [Build] → agent map + graph   │   │   scenario_catalog.json      │   │   failure_inbox.json           │
│                                 │   │   test_configuration.json    │   │   traces/trace_*.json          │
│  Outputs:                       │   │                              │   │   conversations.log            │
│   agent_map.json                │   │                              │   │                                │
│   agent_map.png                 │   │                              │   │                                │
│   agent_map.mmd                 │   │                              │   │                                │
└─────────────────────────────────┘   └──────────────────────────────┘   └────────────────────────────────┘
```

Each phase is independently re-runnable. Session state and artifacts persist in `pipeline_output/{session_id}/`. Phases can be reset individually without losing other phase data.
