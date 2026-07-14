# Sprint 7 — Dynamic Trace Integration (Langfuse)

## Goal

Add a dynamic-discovery step that ingests **Langfuse observability traces** to augment the statically extracted Agent Map with runtime behaviour: actual tool-call sequences, real decision patterns, and empirical rule violations. Static analysis cannot observe what the agent actually does at runtime — traces close that gap. Grounded in AgentTrace (arXiv 2602.10133), AgentSeer (arXiv 2509.17259), and specification mining literature (k-tail, EFSM inference).

**Depends on**: Sprints 2+3 (needs enriched tool model with preconditions and taxonomy IDs to compare against).

## Why This Matters for Phase B

- **Trace-mined tool sequences** are realistic test scaffolds (vs synthetic combinations)
- **Tools observed in traces but missing from static analysis** expand the tool catalogue
- **Common tool orderings** reveal the agent's actual workflow (vs what the code suggests)
- **Rule violations in traces** are ground-truth failure cases that Phase B should reproduce

## Tasks

### 7.1 Langfuse Client Setup

**File**: `src/traces/langfuse_client.py` (new file)

- [ ] Add `langfuse` to `requirements.txt`
- [ ] Create `LangfuseTraceIngester`:
  ```python
  class LangfuseTraceIngester:
      def __init__(self, public_key: str = None, secret_key: str = None, host: str = None):
          # Reads from env: LANGFUSE_PUBLIC_KEY, LANGFUSE_SECRET_KEY, LANGFUSE_HOST
          # Falls back to parameters
  
      def fetch_traces(self, limit: int = 500, since: datetime = None) -> list[dict]:
          # Fetch recent traces from Langfuse API
  
      def fetch_trace_detail(self, trace_id: str) -> dict:
          # Fetch full trace with all spans/generations/events
  ```

### 7.2 Trace Parser

**File**: `src/traces/trace_parser.py` (new file)

- [ ] Define data structures:
  ```python
  @dataclass
  class TraceToolCall:
      tool_name: str
      arguments: dict
      result: dict | None
      success: bool
      duration_ms: float
      timestamp: datetime

  @dataclass
  class TraceConversation:
      trace_id: str
      tool_calls: list[TraceToolCall]     # ordered by timestamp
      tool_sequence: list[str]            # just the tool names in order
      total_turns: int
      total_duration_ms: float
      outcome: str                        # "success" | "failure" | "unknown"
      user_messages: list[str]
      agent_messages: list[str]

  @dataclass
  class TraceAnalysisResult:
      conversations: list[TraceConversation]
      tool_frequency: dict[str, int]           # tool_name → invocation count
      tool_sequences: list[tuple[list[str], int]]  # (sequence, occurrence_count), sorted by frequency
      tools_not_in_static: list[str]           # tools found in traces but not in static analysis
      tools_not_in_traces: list[str]           # tools in static analysis but never called in traces
      common_first_tools: list[str]            # tools most commonly called first
      common_last_tools: list[str]             # tools most commonly called last
      avg_tools_per_conversation: float
      failure_patterns: list[dict]             # common failure sequences
  ```

- [ ] Create `parse_langfuse_traces(raw_traces: list[dict]) -> list[TraceConversation]`:
  - Extract tool calls from Langfuse spans (type = "generation" or "span" with tool call metadata)
  - Order by timestamp
  - Extract user/agent messages from generation inputs/outputs
  - Determine outcome from final span status

### 7.3 Sequence Mining

**File**: `src/traces/sequence_miner.py` (new file)

- [ ] Create `mine_tool_sequences(conversations: list[TraceConversation]) -> dict`:
  - **Frequent sequences**: find tool-call sequences that appear in >5% of conversations
  - **Mutually exclusive tools**: tools that never appear in the same conversation
  - **Common orderings**: for each tool pair (A, B), which order (A→B or B→A) is more common
  - **Failure-correlated sequences**: tool sequences that correlate with failed outcomes

  Implementation: use n-gram counting (bigrams and trigrams of tool names).

- [ ] Create `mine_decision_patterns(conversations: list[TraceConversation]) -> dict`:
  - **Branching points**: where different conversations diverge in tool selection
  - **Average conversation length** by outcome (success vs failure)
  - **Tool retry patterns**: same tool called multiple times in sequence

### 7.4 Compare Static vs Dynamic

**File**: `src/traces/comparator.py` (new file)

- [ ] Create `compare_static_dynamic(agent_map: dict, trace_result: TraceAnalysisResult) -> dict`:
  - **Missing tools**: tools in traces not found by static analysis → add to agent map
  - **Unused tools**: tools in static analysis never called in traces → flag as potentially dead code
  - **Sequence validation**: do AI-predicted `common_sequences` (from `DependencyAnalysis`) match observed sequences?
  - **Dependency validation**: do AI-predicted tool dependencies match observed orderings?
  - **Workflow validation**: does the AI-predicted `decision_strategy` match the observed branching patterns?

  Return a comparison report:
  ```python
  {
      "tools_only_in_static": [...],
      "tools_only_in_traces": [...],
      "sequence_matches": [...],    # AI predictions confirmed by traces
      "sequence_mismatches": [...], # AI predictions contradicted by traces
      "dependency_validations": [...],
  }
  ```

### 7.5 Integrate into Phase A Pipeline

**File**: `analyze.py` and `web/api/routes/phase_a.py`

- [ ] Add optional Step 4.5 (between Risk Analysis and AI Analysis):
  - Only runs if Langfuse credentials are available
  - Controlled by `--use-traces` CLI flag / `use_traces` API parameter
  - Progress event: `"ingesting_traces"` at 55%

- [ ] Feed trace data into AI analysis:
  - `_build_context_summary()` includes trace-mined sequences as additional context
  - AI analysis can validate its predictions against observed behaviour

### 7.6 Add Trace Data to Agent Map

**File**: `src/graph/builder.py`

- [ ] Add `trace_analysis` section to Agent Map:
  ```json
  "trace_analysis": {
      "traces_ingested": 347,
      "tool_frequency": {"check_order": 234, "search_product": 189, "create_ticket": 45},
      "common_sequences": [
          {"sequence": ["check_order", "process_refund"], "count": 87},
          {"sequence": ["search_product", "check_availability", "create_order"], "count": 52}
      ],
      "mutually_exclusive_tools": [["process_refund", "create_order"]],
      "tools_not_in_static": ["internal_lookup"],
      "tools_not_in_traces": ["delete_account"],
      "failure_patterns": [
          {"sequence": ["check_order", "check_order", "check_order"], "failure_rate": 0.82, "description": "Retry loop"}
      ],
      "comparison": {
          "ai_predictions_confirmed": 5,
          "ai_predictions_contradicted": 1,
          "static_tools_coverage": 0.92
      }
  }
  ```

### 7.7 Enrich Tool Dependency Graph

- [ ] Use trace-mined sequences to add edges to the Agent Map's graph:
  - Common sequence A→B → add edge with `relationship: "commonly_precedes"` and `weight: count`
  - Mutually exclusive tools → add edge with `relationship: "mutually_exclusive"`
  - These edges augment the AI-predicted `dependency_analysis`

## Files Modified

| File | Changes |
|------|---------|
| `src/traces/langfuse_client.py` | **New file**: Langfuse API client |
| `src/traces/trace_parser.py` | **New file**: trace parsing and data structures |
| `src/traces/sequence_miner.py` | **New file**: sequence mining from traces |
| `src/traces/comparator.py` | **New file**: static vs dynamic comparison |
| `requirements.txt` | Add `langfuse` dependency |
| `analyze.py` | Add `--use-traces` flag, integrate trace step |
| `web/api/routes/phase_a.py` | Add `use_traces` parameter |
| `src/graph/builder.py` | Add `trace_analysis` section to Agent Map |

## Done When

- Langfuse traces are fetched and parsed into `TraceConversation` objects
- Tool sequences are mined (frequent patterns, mutually exclusive, failure-correlated)
- Static analysis is compared against dynamic observations
- The Agent Map includes a `trace_analysis` section with mined sequences and comparison results
- The tool dependency graph is enriched with trace-observed edges
- The feature is opt-in (`--use-traces`) and gracefully skips if no Langfuse credentials

## Scope Limitations

- This sprint handles **Langfuse** traces only (not arbitrary observability platforms)
- Sequence mining uses simple n-gram counting, not full FSM inference (that's Sprint 8)
- If trace volume is low (<50 conversations), results may not be statistically meaningful — the sprint should warn about this
