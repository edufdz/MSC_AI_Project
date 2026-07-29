# Phase A — Complete Logic & Output Reference

## What Phase A Does

Phase A is the **analysis stage** of the Agent-Testing Platform. It takes an AI agent's source code as input and produces a structured **Agent Map** (`agent_map.json`) that fully describes the agent's architecture, tools, prompts, risks, guardrails, and behaviour. This Agent Map is the sole input to Phase B (test generation).

**Core thesis**: richer Agent Map → better tests.

## Pipeline Overview

```
repo_path
  │
  ▼
┌─────────────────────────────────────────────────────────────┐
│  Step 1: Ingestion                                          │
│  Discover files, score priorities, detect language & entries │
├─────────────────────────────────────────────────────────────┤
│  Step 2: Static Analysis (Tree-sitter)                      │
│  Parse Python + TypeScript/JavaScript into ASTs             │
│  Extract functions, classes, imports, params, calls          │
├─────────────────────────────────────────────────────────────┤
│  Step 3: Pattern Detection                                  │
│  Framework detection, tool extraction, prompt extraction,   │
│  memory detection, precondition/side-effect analysis        │
├─────────────────────────────────────────────────────────────┤
│  Step 4: Risk Analysis                                      │
│  PII regex, critical actions, OWASP/MITRE taxonomy,         │
│  taint flow analysis, unsafe operation detection            │
├─────────────────────────────────────────────────────────────┤
│  Step 4.5: Trace Ingestion (optional, --use-traces)         │
│  Fetch Langfuse traces, mine tool sequences & failures      │
├─────────────────────────────────────────────────────────────┤
│  Step 5: AI Semantic Analysis (optional, requires API key)  │
│  Goal understanding, tool semantics, workflow analysis,     │
│  dependency analysis, guardrail extraction via LLM          │
├─────────────────────────────────────────────────────────────┤
│  Step 6: Agent Map Assembly                                 │
│  Merge all data, build architecture graph, extract           │
│  guardrail rules, build behavioural model, generate map     │
└─────────────────────────────────────────────────────────────┘
  │
  ▼
agent_map.json  +  agent_map_graph.png  +  agent_map_graph.mmd
```

---

## Step-by-Step Logic

### Step 1 — Ingestion (`src/ingestion/ingestor.py`)

Scans the repository directory and builds a file inventory.

**What it does:**
- Discovers `.py`, `.ts`, `.tsx`, `.js`, `.jsx` files
- Excludes `node_modules/`, `__pycache__/`, `.git/`, test directories
- Scores each file by priority (entry points like `main.py`, `agent.ts` score highest)
- Detects project type (python, typescript, mixed)
- Identifies entry points (files with `main`, `agent`, `run` in name)
- Finds prompt files (`.prompt`, `.jinja`, `.txt` in prompt-like directories)
- Applies optional language filter (`--language python`)

**Output:** `IngestionResult` with file list, entry points, project type, prompt files.

### Step 2 — Static Analysis (`src/analysis/static_analyzer.py`)

Parses every source file into a structured symbol table using tree-sitter ASTs.

**Python parser** (tree-sitter-python):
- Functions: name, parameters with types and defaults, docstring, decorators, body text, function calls
- Classes: name, base classes, methods, class variables, docstring, decorators
- Imports: module path, imported names, aliases
- Variables: name, value text (up to 500 chars, 6000 for tool arrays)

**TypeScript/JavaScript parser** (tree-sitter-typescript/javascript — Sprint 1):
- Same extraction as Python, plus:
- JSDoc comments extracted as docstrings
- TypeScript type annotations on parameters
- Arrow functions, class fields, interfaces, type aliases
- `export` detection, CommonJS `module.exports`
- Regex fallback if tree-sitter fails (graceful degradation)

**Output:** `list[FileSymbols]` — one per file, containing functions, classes, imports, variables, parse errors.

### Step 3 — Pattern Detection (`src/patterns/detector.py`)

Identifies agent framework, tools, prompts, and memory systems from the symbol tables.

**Framework detection:**
- Scores imports, decorators, and class bases against known signatures
- Detects: LangChain, LangGraph, CrewAI, AutoGen, OpenAI native, Anthropic native, custom

**Tool extraction** (6 strategies):
1. **LangChain decorators**: `@tool` decorated functions → full metadata
2. **LangChain classes**: `BaseTool`/`StructuredTool` subclasses
3. **OpenAI/Claude arrays**: variables named `tools`/`functions` with `{name, description}` patterns
4. **Tool file modules**: one-tool-per-file in `tools/`, `skills/` directories
5. **Custom heuristic**: functions with HTTP calls, DB calls, docstrings, typed params
6. **Graph node extraction**: exported functions in `graph/nodes/`, `pipelines/` directories (LangGraph nodes)
7. **Event detector extraction**: objects/functions in `events/`, `detectors/` directories

**Precondition extraction** (Sprint 2):
- Guard clauses: `if not X: raise`, `if X is None: return`
- Validation calls: `validate_`, `check_`, `verify_`, `ensure_`
- Assert statements: `assert isinstance(X, type)`

**Side-effect extraction** (Sprint 2):
- Database writes: INSERT, UPDATE, DELETE, save(), commit()
- HTTP mutations: POST, PUT, PATCH, DELETE
- File writes: write(), open('w'), fs.writeFile
- Notifications: send_email(), send_notification()
- State changes: session[], cache.set(), setState()

**Output:** `PatternResult` with framework, tools (with preconditions/side_effects/state_modifying), prompts, memory systems.

### Step 4 — Risk Analysis (`src/risk/analyzer.py`)

Scans tools and prompts for security risks, maps to taxonomies.

**PII detection:**
- Regex patterns for email, phone, SSN, credit card, IP address, name, address
- Scans tool parameters, descriptions, and code snippets

**Critical action detection:**
- Keywords: payment, refund, delete, transfer, admin, execute, deploy
- Maps to severity levels (critical, high, medium, low)

**Taxonomy mapping** (Sprint 3):
- OWASP LLM Top 10 2025: LLM01–LLM10
- OWASP Agentic Security 2026: ASI01–ASI09
- MITRE ATLAS: AML.T0000-series

**Taint flow analysis** (Sprint 4):
- Source identification: user input parameters, external data
- Sink identification: HTTP calls, database writes, file operations
- Intra-procedural data-flow tracking through assignments and calls

**Unsafe operation detection** (Sprint 3):
- `eval()`, `exec()`, `os.system()`, dynamic code execution

**Output:** `list[RiskFlag]` with tool, risk_type, severity, taxonomy_ids, description, mitigation. Plus `list[TaintFlow]` for data-flow risks.

### Step 4.5 — Trace Ingestion (Optional, `--use-traces`)

Fetches production traces from Langfuse for dynamic analysis.

**What it does:**
- Connects to Langfuse API (paginated, max 100/page)
- Fetches trace details with all spans/generations
- Parses into `TraceConversation` objects with tool sequences
- Mines: tool frequency, common sequences (bigrams/trigrams), failure patterns, decision points
- Compares static tools vs trace-observed tools

**Output:** `TraceAnalysisResult` with tool_frequency, tool_sequences, failure_patterns, tools_not_in_static/traces.

### Step 5 — AI Semantic Analysis (Optional, requires `ANTHROPIC_API_KEY`)

Uses Claude to deeply understand agent purpose, tool semantics, workflow, and guardrails.

**Four LLM analyses:**
1. **Goal understanding**: purpose, domain, capabilities, success criteria
2. **Tool semantics**: per-tool purpose, required inputs, read_only, sensitive data, dependencies, preconditions, postconditions, side_effects
3. **Workflow analysis**: decision strategy, typical flow, error handling, guardrails
4. **Dependency analysis**: tool-to-tool dependencies, mutually exclusive tools, common sequences

**Guardrail extraction** (Sprint 6):
- Sends all prompt content to Claude for structured rule extraction
- Returns rules with category, complexity, scope, target_tools, conditions

**LLM fact validation** (Sprint 5):
- Cross-checks AI claims against static analysis
- Validates read_only claims against code write indicators
- Verifies dependency claims against call graph paths

**Context assembly** (Sprint 5):
- Call-graph-guided hierarchical summarisation
- Budget-aware context selection (prioritises entry points and tool functions)
- Replaces naive 80K-char truncation

**Output:** `SemanticAnalysisResult` with goal, tool_semantics, workflow, dependency_analysis, guardrail_graph.

### Step 6 — Agent Map Assembly (`src/graph/builder.py`)

Merges all analysis results into the final Agent Map JSON.

**Architecture graph construction:**
- Creates NetworkX directed graph with agent → orchestrator → tools hierarchy
- **LangGraph topology extraction**: parses `addNode()`, `addEdge()`, `addConditionalEdges()` from source to build the actual state machine graph (not a flat fan-out)
- Adds memory and retrieval subsystem nodes

**Guardrail extraction** (Sprint 6):
- Pattern-based offline extraction from prompt text (numbered rules, bullet points, imperative verbs)
- Merges with AI-extracted rules (deduplicates)
- Classifies: prohibition, requirement, constraint, escalation, fallback
- Scores complexity 1-5
- Detects guardrail language vs conversation language mismatch

**Behavioural model** (Sprint 8):
- Builds tool dependency graph from: AI dependencies, per-tool dependencies, precondition→postcondition matching, trace-mined sequences
- Analyses graph properties: circular dependencies, bottleneck tools, orphan tools, longest chain, critical paths
- Generates coverage targets for Phase B
- Infers FSM from trace data (k-tail state merging) if traces available

**Language & domain metadata** (Sprint 9):
- Multi-language detection (Spanish, English, Portuguese) with scoring
- Code-switching detection
- Spanish formality (usted/tú)
- Domain, industry, and channel inference from tool names and prompts

---

## Agent Map Output Structure

This is the complete `agent_map.json` schema — every field, what it means, and what Phase B does with it.

### `version` (string)
Map schema version. Currently `"1.0"`.

### `generated_at` (ISO timestamp)
When the analysis ran.

### `agent_id` (UUID)
Unique identifier. Phase B uses this to tie the test suite back to the source agent.

### `metadata` (object)

| Field | Type | Phase B Usage |
|-------|------|---------------|
| `name` | string | Display name |
| `type` | string | Domain type (support, sales, scheduling, etc.) — selects persona/scenario templates |
| `framework` | string | Detected framework (langchain, langgraph, openai_native, etc.) |
| `framework_confidence` | float | 0.0–1.0 |
| `language` | object | Rich language detection (see below) |
| `programming_language` | string | Source language |
| `purpose` | string | What the agent does — injected into persona generation prompts |
| `capabilities` | list[string] | Agent capabilities — context for persona/scenario generation |
| `conversation_language` | string | Primary language — personas and scenarios generated in this language |
| `domain` | object | Domain/industry/channel metadata |

**`metadata.language`** (object):

| Field | Type | Meaning |
|-------|------|---------|
| `conversation_languages` | list[string] | All detected languages |
| `primary_language` | string | Highest-scoring language |
| `guardrail_language` | string | Language of guardrail rules |
| `language_mismatch` | boolean | True if guardrails and conversation differ |
| `code_switching_detected` | boolean | True if 2+ languages each score >= 3 |
| `spanish_formality` | string/null | "usted", "tu", or "mixed" |
| `confidence` | float | 0.0–1.0 |

**`metadata.domain`** (object):

| Field | Type | Meaning |
|-------|------|---------|
| `type` | string | Domain (support, sales, ecommerce, etc.) |
| `industry` | string | Industry (consumer_electronics, finance, etc.) |
| `channel` | string | Channel (whatsapp, email, chat, voice) |

### `components` (object)

#### `components.orchestrator` (object)
| Field | Type | Phase B Usage |
|-------|------|---------------|
| `type` | string | Decision strategy (state-machine, react, plan-and-execute, etc.) |
| `error_handling` | object | How errors are handled |
| `guardrails` | list[string] | Workflow-level guardrails |
| `typical_flow` | list[string] | Expected execution flow |
| `ambiguity_handling` | string | How ambiguity is resolved |

#### `components.tools[]` (list) — **PRIMARY DATA FOR PHASE B**

Each tool object:

| Field | Type | Phase B Usage |
|-------|------|---------------|
| `id` | string | Normalized tool ID |
| `name` | string | Tool name as called by agent |
| `description` | string | What the tool does |
| `parameters` | list[object] | Each param: {name, type, default} |
| `dependencies` | list[string] | Other tools this requires |
| `sandbox_safe` | boolean | Can run in sandbox? |
| `risk_level` | string | critical/high/medium/low — **drives coverage scaling** |
| `read_only` | boolean | No side effects? — **drives sandbox mock/real config** |
| `state_modifying` | boolean | Modifies system state? |
| `handles_sensitive_data` | boolean | PII/financial? — **enables PII detection** |
| `source` | string | How discovered (langchain_decorator, graph_node, event_detector, etc.) |
| `confidence` | float | 0.0–1.0 |
| `location` | object | Source file and line |
| `preconditions` | list[string] | What must be true before calling — **boundary test generation** |
| `postconditions` | list[string] | What becomes true after — **oracle generation** |
| `side_effects` | list[string] | State changes performed — **rollback scenario generation** |

**How Phase B uses tool risk_level for coverage scaling:**

| Risk Level | Min Invocations | Edge-Case Multiplier |
|------------|----------------|---------------------|
| critical | 25 | 2.0x |
| high | 15 | 1.5x |
| medium | 10 | 1.0x |
| low | 5 | 0.8x |

#### `components.memory` (object)
| Field | Type | Meaning |
|-------|------|---------|
| `systems` | list[object] | Each: {type, implementation, location} |
| `conversation_history` | boolean | Has conversation buffer? |
| `persistent_state` | boolean | Has persistent state store? |

#### `components.retrieval` (object)
| Field | Type | Meaning |
|-------|------|---------|
| `systems` | list[object] | Vector stores installed |
| `exists` | boolean | Any retrieval system present? |

#### `components.prompts[]` (list)
| Field | Type | Phase B Usage |
|-------|------|---------------|
| `name` | string | Prompt identifier |
| `type` | string | system_prompt, template, file |
| `content` | string | First 2000 chars — **context for persona/scenario generation** |
| `variables` | list[string] | Template variables |
| `location` | object | Source file and line |

### `success_criteria` (object)
| Field | Type | Phase B Usage |
|-------|------|---------------|
| `task_completion` | list[string] | Success conditions — **test pass/fail criteria** |
| `max_latency_ms` | integer | Latency budget |
| `max_cost_per_conversation` | float | Cost budget — **sandbox cost cap = 10% of this** |
| `max_turns` | integer | Turn limit |

### `guardrails` (object) — Sprint 6

| Field | Type | Phase B Usage |
|-------|------|---------------|
| `rules[]` | list[object] | Numbered policy rules — **each becomes a rule-violation test** |
| `interactions[]` | list[object] | Rule conflicts and co-occurrences |
| `total_rules` | integer | Count |
| `total_complexity` | integer | Sum of all rule complexities |
| `by_category` | object | Counts per category |
| `guardrail_language` | string | Language rules are written in |
| `guardrail_language_matches_conversation` | boolean | Mismatch flag |

Each rule in `guardrails.rules[]`:

| Field | Type | Phase B Usage |
|-------|------|---------------|
| `rule_id` | string | R001, R002, etc. |
| `text` | string | The rule in original wording — **test assertion text** |
| `category` | string | prohibition, requirement, constraint, escalation, fallback |
| `complexity` | integer | 1–5 — **higher complexity = more test variants** |
| `scope` | string | always, conditional, tool_specific |
| `target_tools` | list[string] | Tools this rule applies to |
| `conditions` | list[string] | When this rule applies |
| `source_prompt` | string | Which prompt it came from |
| `language` | string | Language the rule is written in |

### `risk_flags` (object)

| Field | Type | Phase B Usage |
|-------|------|---------------|
| `pii_handling` | boolean | Any PII? — **enables PII detection in sandbox** |
| `critical_actions` | list[string] | Critical tool names — **special handling in tests** |
| `taint_flows[]` | list[object] | Data-flow risks — **informs scenario construction** |
| `all_risks[]` | list[object] | Complete risk inventory (see below) |

Each risk in `risk_flags.all_risks[]`:

| Field | Type | Phase B Usage |
|-------|------|---------------|
| `tool` | string | Which tool |
| `risk_type` | string | pii, critical_action, injection, unsafe_operation, etc. |
| `pii_type` | string | email, phone, credit_card, etc. |
| `severity` | string | critical, high, medium, low — **coverage scaling** |
| `description` | string | Risk description |
| `mitigation` | string | How to mitigate |
| `taxonomy_ids` | list[string] | OWASP LLM (LLM01–10), OWASP Agentic (ASI01–09), MITRE ATLAS |
| `taxonomy_names` | list[string] | Human-readable taxonomy names |

### `risk_summary` (object)
| Field | Type | Meaning |
|-------|------|---------|
| `by_taxonomy` | object | Risk counts per taxonomy ID |
| `highest_severity` | string | Most severe risk found |
| `total_risks` | integer | Total risk count |

### `graph` (object)

| Field | Type | Phase B Usage |
|-------|------|---------------|
| `nodes[]` | list[object] | Agent architecture nodes (agent, orchestrator, tools, memory, graph_nodes) |
| `edges[]` | list[object] | Relationships: contains, invokes, flows_to, routes_to, requires, commonly_precedes |

Edges from LangGraph topology extraction show the actual state machine flow (multi-level), not a flat fan-out.

### `behavioural_model` (object) — Sprint 8

#### `behavioural_model.dependency_graph` (object)
| Field | Type | Phase B Usage |
|-------|------|---------------|
| `edges[]` | list[object] | Tool-to-tool dependencies with type, weight, evidence |
| `properties.circular_dependencies` | list | Cycles — **stress test targets** |
| `properties.bottleneck_tools` | list | High in-degree tools — **priority coverage** |
| `properties.orphan_tools` | list | Independent tools |
| `properties.longest_chain` | list | Longest dependency chain — **end-to-end test path** |
| `properties.critical_paths` | list | Paths through high-risk tools |

#### `behavioural_model.fsm` (object, optional — requires traces)
| Field | Type | Phase B Usage |
|-------|------|---------------|
| `states[]` | list[object] | FSM states with tools_available — **transition coverage** |
| `transitions[]` | list[object] | State transitions with frequency — **path coverage** |

#### `behavioural_model.coverage_targets` (object)
| Field | Type | Phase B Usage |
|-------|------|---------------|
| `transition_coverage` | object | Test every transition at least once |
| `dependency_chain_coverage` | object | Test every chain end-to-end |
| `negative_coverage` | object | Test constraint violations (cycles, mutual exclusion) |
| `path_coverage` | object | Test critical paths through high-risk tools |

### `trace_analysis` (object, optional — requires `--use-traces`)

| Field | Type | Phase B Usage |
|-------|------|---------------|
| `traces_ingested` | integer | Number of conversations analysed |
| `tool_frequency` | object | How often each tool was called — **test ordering** |
| `common_sequences[]` | list | Frequent tool patterns — **scenario templates** |
| `tools_not_in_static` | list | Tools in traces but not in code — **investigation flags** |
| `tools_not_in_traces` | list | Tools in code but never called — **priority coverage** |
| `failure_patterns[]` | list | Common error modes — **failure scenario generation** |
| `avg_tools_per_conversation` | float | Average tool calls per conversation |
| `comparison` | object | Static vs dynamic comparison |

### `source_files` (object)
| Field | Type | Meaning |
|-------|------|---------|
| `analyzed_files` | list[string] | All files scanned |
| `entry_points` | list[string] | Agent entry point files |
| `repository` | string | Repository root path |

---

## Phase B Consumption Flow

```
                          agent_map.json
                               │
          ┌────────────────────┼────────────────────┐
          ▼                    ▼                    ▼
   ┌─────────────┐    ┌──────────────┐    ┌──────────────┐
   │  B1: Coverage │   │ B2: Personas  │   │ B3: Scenarios │
   │  Calculator   │   │ Builder       │   │ Library       │
   └──────┬──────┘    └──────┬───────┘    └──────┬───────┘
          │                  │                   │
          │   Reads:         │   Reads:          │   Reads:
          │   • tools[]      │   • metadata      │   • tools[]
          │   • risk_level   │   • purpose       │   • guardrails.rules[]
          │   • risk_flags   │   • tools[]       │   • prompts[]
          │   • success_     │   • risk_flags    │   • risk_flags
          │     criteria     │   • conv_language │   • dependency_graph
          │                  │                   │
          ▼                  ▼                   ▼
   CoverageGoals       PersonaLibrary      ScenarioCatalog
   SandboxConfig       (3-50 personas)     (5-100 scenarios)
          │                  │                   │
          └────────────────┬─┴───────────────────┘
                           ▼
                  ┌──────────────────┐
                  │ B4: Test Suite    │
                  │ Generator         │
                  │                   │
                  │ Reads:            │
                  │ • coverage goals  │
                  │ • personas        │
                  │ • scenarios       │
                  │ • coverage_targets│
                  │ • tool_frequency  │
                  └────────┬─────────┘
                           ▼
                    TestSuite JSON
                   (20-500 test cases)
```

### What each Phase B step reads:

**B1 — Coverage Configuration:**
- `components.tools[].risk_level` → min invocations per tool (critical=25, high=15, medium=10, low=5)
- `components.tools[].handles_sensitive_data` → enable PII detection
- `components.tools[].read_only` → sandbox mock vs real mode
- `risk_flags.pii_handling` → global PII flag
- `risk_flags.critical_actions` → critical tool list
- `success_criteria` → cost/turn/latency limits for sandbox

**B2 — Persona Generation:**
- `metadata.type` → domain-specific persona templates
- `metadata.purpose` → agent context in generation prompt
- `metadata.conversation_language` → persona language
- `components.tools[].name` → tool-attack personas target specific tools
- `risk_flags.critical_actions` → adversarial personas target critical tools

**B3 — Scenario Generation:**
- `components.tools[]` → required/optional tools per scenario
- `guardrails.rules[]` → each rule becomes a rule-violation test scenario
- `components.prompts[].content` → behaviour context for scenario design
- `risk_flags.all_risks[]` → risk-focused scenarios
- `behavioural_model.dependency_graph` → multi-step chain scenarios

**B4 — Test Suite Assembly:**
- Coverage goals from B1 → allocation strategy across tools
- Personas from B2 → persona selection for each test case
- Scenarios from B3 → scenario selection for each test case
- `behavioural_model.coverage_targets` → high-priority coverage reservations
- `trace_analysis.tool_frequency` → test ordering by observed frequency

---

## TechRepair WhatsApp Agent — Example Output

When run against the TechRepair WhatsApp agent at Pulpoo:

| Metric | Value |
|--------|-------|
| Files analysed | 53 TypeScript files |
| Functions extracted | 108 |
| Imports extracted | 211 |
| Tools detected | 54 (1 custom heuristic, 46 graph nodes, 7 event detectors) |
| Prompts found | 9 (router, status, support, memory, summarisation, verification) |
| Guardrail rules | 62–79 (16–21 prohibitions, 37–45 requirements, 3–5 escalation, 4–7 fallback, 2–5 constraint) |
| Risks | 33 (25 PII, 7 critical actions, 1 excessive agency) |
| Dependency edges | 65 |
| Circular dependencies | 3 |
| Bottleneck tools | routeByIntent, buildHandoffContext, routeAfterSupport |
| Orphan tools | 16 |
| Conversation language | Spanish |
| Guardrail language | English (mismatch flagged) |
| Framework | anthropic_native (LangGraph state machine) |
| Decision strategy | state-machine |
| Graph topology | START → event_detector → router → {status, support, contact_info, delivery_logistics, warranty_answer, pricing_answer, escalation, human_taken_over} → response → END |
