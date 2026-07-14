# Phase A Enhancement Programme — Context

## What This Is

A series of enhancements to **Phase A (Analyze)** of the Plavio Agent Debugger platform. Phase A is the foundational analysis stage that scans an AI agent's source code and produces a structured **Agent Map** (`agent_map.json`) describing the agent's architecture, tools, prompts, memory systems, risks, and behaviour.

## Why These Enhancements Exist

This work is part of an MSC AI research project. A literature review identified that **downstream test-scenario quality is bounded by the richness and accuracy of the model fed to the test generator** (Phase B). The current Phase A produces a flat feature extraction rather than a behavioural model, which limits what Phase B can generate. The enhancements are grounded in peer-reviewed findings:

- Inozemtseva & Holmes (ICSE 2014): coverage maximisation is the wrong target; model richness matters more
- IntellAgent (Levi & Kadar, ICML 2025): richer extracted models yield more diverse, complexity-graded scenarios
- PyCG study (arXiv 2410.00603): structured static analysis achieves 84.9% completeness vs 60.3% for LLMs
- AgentArmor (arXiv 2508.01249): data-flow modelling reduces attack success rate from 41% to 3%
- OWASP LLM 2025 / OWASP Agentic 2026 / MITRE ATLAS: authoritative risk taxonomies for agents

## The Codebase

**Platform**: Plavio Agent Debugger — an end-to-end AI-powered platform for testing, debugging, and certifying conversational AI agents.

**Root directory**: `debugger-platforn/` (note the typo in the directory name — it is intentional, do not rename)

**Phase A pipeline** (6 sequential steps):

```
repo_path → [Ingestion] → [Static Analysis] → [Pattern Detection] → [Risk Analysis] → [AI Semantic Analysis] → [Agent Map Generation]
```

### Key Source Files

| Module | Path | Purpose |
|--------|------|---------|
| CLI entry | `analyze.py` | Click CLI, orchestrates the 6 steps |
| API route | `web/api/routes/phase_a.py` | FastAPI endpoint, WebSocket progress |
| Ingestor | `src/ingestion/ingestor.py` | File discovery, priority scoring |
| Static Analyzer | `src/analysis/static_analyzer.py` | Tree-sitter (Python) + regex (TS/JS) |
| Pattern Detector | `src/patterns/detector.py` | Framework, tool, prompt, memory detection |
| Risk Analyzer | `src/risk/analyzer.py` | PII regex + critical action keywords |
| AI Analyzer | `src/ai_analyzer/analyzer.py` | Claude semantic analysis (4 sub-analyses) |
| AI Prompts | `src/ai_analyzer/prompts.py` | LLM prompt templates |
| Graph Builder | `src/graph/builder.py` | Agent Map assembly + NetworkX graph |
| Visualizer | `src/graph/visualizer.py` | PNG + Mermaid diagram generation |
| Framework Sigs | `config/framework_signatures.py` | Framework signatures, PII patterns, critical action keywords |

### Key Data Structures (distributed across files)

| Structure | Defined in | Fields |
|-----------|-----------|--------|
| `FileInfo` | `src/ingestion/ingestor.py:48` | path, relative_path, language, size_bytes, is_entry_point, priority |
| `IngestionResult` | `src/ingestion/ingestor.py:58` | root_path, project_type, files, entry_points, total_files_scanned, prompt_files |
| `FunctionInfo` | `src/analysis/static_analyzer.py:32` | name, params, docstring, decorators, body_text, location, is_async, calls |
| `ClassInfo` | `src/analysis/static_analyzer.py:44` | name, bases, docstring, methods, decorators, location, class_variables |
| `FileSymbols` | `src/analysis/static_analyzer.py:70` | file_path, language, functions, classes, imports, variables, parse_errors |
| `ToolDefinition` | `src/patterns/detector.py:24` | id, name, description, parameters, source, location, confidence, risk_level, sandbox_safe, code_snippet |
| `PromptDefinition` | `src/patterns/detector.py:38` | name, type, content, variables, location |
| `MemorySystem` | `src/patterns/detector.py:47` | type, implementation, location |
| `PatternResult` | `src/patterns/detector.py:54` | framework, framework_confidence, tools, prompts, memory_systems |
| `RiskFlag` | `src/risk/analyzer.py:16` | location, tool, risk_type, pii_type, severity, description, mitigation |
| `GoalAnalysis` | `src/ai_analyzer/analyzer.py:37` | purpose, domain, capabilities, success_criteria, confidence |
| `ToolSemanticInfo` | `src/ai_analyzer/analyzer.py:46` | name, purpose, required_inputs, output, read_only, handles_sensitive_data, dependencies, risk_level |
| `WorkflowAnalysis` | `src/ai_analyzer/analyzer.py:59` | decision_strategy, typical_flow, error_handling, guardrails, ambiguity_handling |
| `DependencyAnalysis` | `src/ai_analyzer/analyzer.py:68` | dependencies, mutually_exclusive, common_sequences, circular_dependency_risks |
| `SemanticAnalysisResult` | `src/ai_analyzer/analyzer.py:76` | goal, tool_semantics, workflow, dependency_analysis |

### Current Dependencies (relevant)

```
tree-sitter>=0.23.0
tree-sitter-python>=0.23.0
anthropic>=0.40.0
networkx>=3.0
matplotlib>=3.8.0
```

Note: **No `tree-sitter-typescript` or `tree-sitter-javascript`** — TS/JS parsing uses regex fallback.

### Current Limitations (what the sprints fix)

1. **TS/JS parsing is regex-based** (`static_analyzer.py:387-486`): misses parameter types, decorators, JSDoc, nested functions, re-exports
2. **PII detection is naive regex** (`risk/analyzer.py:26-76`, `framework_signatures.py:86-94`): cannot follow data through assignments/calls — no taint tracking
3. **Risk labels are ad-hoc** (`risk/analyzer.py:98-123`): no mapping to OWASP LLM 2025, OWASP Agentic 2026, or MITRE ATLAS
4. **Tools lack preconditions/postconditions** (`detector.py:24-34`): `ToolDefinition` has no `preconditions`, `postconditions`, `side_effects` fields
5. **AI context is hard-capped at 80K chars** (`ai_analyzer/analyzer.py:33,145`): silently truncates large repos
6. **No guardrail/policy rule extraction**: prompts are captured but rules within them aren't parsed into numbered testable assertions
7. **No dynamic trace integration**: no Langfuse or runtime trace ingestion
8. **Agent Map is a containment/invocation graph, not a behavioural model**: no FSM, no tool-dependency graph with mutually-exclusive edges
9. **Multilingual fields are minimal**: only `conversation_language` (Spanish/English), no guardrail-language or domain tag

### Agent Map Output Structure (current)

The final `agent_map.json` contains:
- `version`, `generated_at`, `agent_id`
- `metadata`: name, type, framework, framework_confidence, language, purpose, capabilities, conversation_language
- `components`: orchestrator, tools[], memory, retrieval, prompts[]
- `success_criteria`: task_completion, max_latency_ms, max_cost_per_conversation, max_turns
- `risk_flags`: pii_handling, critical_actions[], all_risks[]
- `graph`: nodes[], edges[]
- `source_files`: analyzed_files, entry_points, repository

### How Phase B Consumes the Agent Map

Phase B reads `agent_map.json` and uses it to:
- Generate **coverage goals** from the tool inventory and risk levels
- Build **personas** targeting specific tools (tool-attack personas) and flows (flow-attack personas)
- Create **scenarios** that exercise required_tools, test success/failure conditions, and inject chaos
- Assemble the **test suite** with coverage guarantees

Every new field added to the Agent Map directly enables richer test generation. This is the core thesis: **richer Agent Map → better tests**.

## Sprint Overview

| Sprint | Name | Effort | Can Parallelize With |
|--------|------|--------|---------------------|
| 1 | Tree-sitter TS/JS AST parsing | Medium | Sprint 3 |
| 2 | Per-tool preconditions/postconditions/side-effects | Medium | Sprint 3 |
| 3 | OWASP/MITRE risk taxonomy mapping | Small | Sprints 1, 2 |
| 4 | Intra-procedural taint/data-flow analysis | Large | Sprint 6 |
| 5 | Hierarchical code summarisation (replace 80K cap) | Large | — |
| 6 | Guardrail/policy rule extraction | Medium | Sprint 4 |
| 7 | Dynamic trace integration (Langfuse) | Large | — |
| 8 | Behavioural model layer (FSM + dependency graph) | Large | — |
| 9 | Multilingual/domain metadata fields | Small | Any sprint |
| T | Testing sprint (end-to-end validation) | Medium | After all others |

### Parallelisation Guide

These sprints can run as **simultaneous agents**:

- **Parallel group 1**: Sprint 1 (tree-sitter) + Sprint 3 (OWASP taxonomy) — they touch different files entirely
- **Parallel group 2**: Sprint 2 (preconditions) + Sprint 3 (OWASP taxonomy) — Sprint 2 modifies `ToolDefinition` and AI prompts; Sprint 3 modifies `RiskFlag` and `framework_signatures.py`
- **Parallel group 3**: Sprint 4 (taint analysis) + Sprint 6 (guardrail extraction) — Sprint 4 adds a new module; Sprint 6 modifies AI prompts and adds extraction logic
- **Sprint 9** (multilingual fields) is so small it can pair with any sprint

**Sequential dependencies**:
- Sprint 5 (hierarchical summarisation) depends on Sprint 1 (needs complete AST for all languages)
- Sprint 7 (Langfuse traces) depends on Sprints 2+3 (needs enriched tool model to compare against)
- Sprint 8 (behavioural model) depends on Sprints 2+7 (needs preconditions and trace data)
- Sprint T (testing) runs after all others
