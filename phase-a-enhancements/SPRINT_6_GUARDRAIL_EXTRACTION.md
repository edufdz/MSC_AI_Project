# Sprint 6 — Guardrail/Policy Rule Extraction

## Goal

Extract explicit, numbered rules from system prompts and policy documents so each rule becomes a testable assertion in Phase B. Grounded in IntellAgent (Levi & Kadar, ICML 2025), which builds a **policy graph** from system prompts — nodes are policies with complexity scores, edges are co-occurrence likelihoods — and generates scenarios by weighted random walks. Also motivated by the OWASP LLM07 finding that system prompts are suggestions, not controls, so rule-adherence must be explicitly tested.

**Can run in parallel with**: Sprint 4 (taint analysis) — this sprint modifies AI prompts and adds extraction logic; Sprint 4 adds a new taint module.

## Why This Matters for Phase B

Currently Phase A captures prompt **content** (up to 2000 chars) but doesn't parse the rules within. Phase B has no structured list of "rules the agent must follow." With numbered rules:

- Each rule becomes a **rule-violation test**: "Does the agent follow rule #3 when the user asks X?"
- Rules can be **scored by complexity** (simple yes/no vs multi-condition logic)
- Rules can be **combined** to test interaction effects (rule #2 + rule #5 together)
- The project's existing rule-violation ground-truth signal gets an explicit target list

## Tasks

### 6.1 Define Rule Data Model

**File**: `src/patterns/detector.py` (or new `src/patterns/rule_extractor.py`)

- [ ] Define data structures:
  ```python
  @dataclass
  class PolicyRule:
      rule_id: str                    # "R001", "R002", etc.
      text: str                       # original rule text
      category: str                   # "constraint" | "requirement" | "prohibition" | "fallback" | "escalation"
      complexity: int                 # 1-5 (1=simple boolean, 5=multi-condition with exceptions)
      scope: str                      # "always" | "conditional" | "tool_specific"
      target_tools: list[str]         # tools this rule applies to (empty = all)
      conditions: list[str]           # conditions under which rule applies
      source_prompt: str              # which prompt this was extracted from
      source_location: dict           # {file, line}
      language: str                   # "English" | "Spanish" (language the rule is written in)

  @dataclass
  class PolicyGraph:
      rules: list[PolicyRule]
      edges: list[dict]               # [{from: "R001", to: "R003", type: "co-occurrence", weight: 0.8}]
      total_complexity: int           # sum of all rule complexities
  ```

### 6.2 Pattern-Based Rule Extraction (Offline)

**File**: `src/patterns/rule_extractor.py` (new file)

- [ ] Create `extract_rules_from_text(text: str, language: str = "English") -> list[PolicyRule]`:

  **Rule indicators to detect**:
  - Numbered rules: `1.`, `2.`, `1)`, `2)`, `- Rule 1:`, `Rule #1`
  - Bullet points followed by imperative verbs: `- Never`, `- Always`, `- Do not`, `- Must`, `- Should`
  - Spanish equivalents: `- Nunca`, `- Siempre`, `- No debes`, `- Debes`, `- Es obligatorio`
  - Conditional rules: `If... then...`, `When... you must...`, `Si... entonces...`
  - Prohibition markers: `never`, `do not`, `forbidden`, `prohibited`, `must not`, `nunca`, `prohibido`
  - Escalation markers: `escalate`, `transfer`, `human agent`, `supervisor`, `escalar`, `agente humano`
  - Fallback markers: `if unsure`, `when in doubt`, `default to`, `si no estás seguro`

  **Category classification**:
  - `"prohibition"`: contains `never`, `do not`, `must not`, `forbidden`
  - `"requirement"`: contains `must`, `always`, `required`, `shall`
  - `"constraint"`: contains `only`, `limited to`, `maximum`, `no more than`
  - `"escalation"`: contains `escalate`, `transfer`, `human`
  - `"fallback"`: contains `if unsure`, `default`, `otherwise`

  **Complexity scoring** (1-5):
  - 1: Simple boolean (`"Never share customer data"`)
  - 2: Single condition (`"If customer is upset, apologize first"`)
  - 3: Multi-condition (`"If order > $100 AND customer is premium, offer discount"`)
  - 4: Exception-laden (`"Always verify identity, except for general inquiries about store hours"`)
  - 5: Multi-step with state (`"First check order status, then if refundable and within 30 days, process refund, otherwise escalate"`)

### 6.3 AI-Enhanced Rule Extraction

**File**: `src/ai_analyzer/prompts.py`

- [ ] Add new prompt template `GUARDRAIL_EXTRACTION_PROMPT`:
  ```
  Analyze these system prompts and policy documents from an AI agent.
  Extract every explicit rule, constraint, prohibition, requirement, escalation trigger,
  and fallback behaviour as a numbered list.

  For each rule, determine:
  - text: the rule in its original wording
  - category: constraint | requirement | prohibition | fallback | escalation
  - complexity: 1-5 (1=simple boolean, 5=multi-condition with exceptions)
  - scope: always | conditional | tool_specific
  - target_tools: list of tool names this rule specifically mentions (empty if general)
  - conditions: list of conditions under which this rule applies

  Also identify rule interactions:
  - Which rules might conflict with each other?
  - Which rules tend to apply together in the same scenario?

  Prompts to analyze:
  {prompts}

  Available tools: {tool_names}

  Return JSON:
  {
    "rules": [...],
    "interactions": [{"from": "R001", "to": "R003", "type": "conflict|co-occurrence", "description": "..."}]
  }
  ```

**File**: `src/ai_analyzer/analyzer.py`

- [ ] Add `analyze_guardrails(prompts, tool_names) -> PolicyGraph`:
  - Send all prompt content (not truncated) to Claude
  - Parse response into `PolicyRule` objects
  - Build `PolicyGraph` with rules and interaction edges

### 6.4 Merge Pattern-Based and AI-Extracted Rules

- [ ] Pattern-based extraction runs first (offline, free)
- [ ] AI extraction runs second (if not `skip_ai`)
- [ ] Merge: deduplicate by semantic similarity (if AI rule matches a pattern-extracted rule, keep the AI version as it's richer)
- [ ] Number rules sequentially: `R001`, `R002`, etc.

### 6.5 Add to Agent Map

**File**: `src/graph/builder.py`

- [ ] Add `guardrails` section to Agent Map:
  ```json
  "guardrails": {
      "rules": [
          {
              "rule_id": "R001",
              "text": "Never share customer personal data with third parties",
              "category": "prohibition",
              "complexity": 1,
              "scope": "always",
              "target_tools": [],
              "conditions": [],
              "language": "Spanish"
          },
          {
              "rule_id": "R002",
              "text": "If the customer requests a refund for an order older than 30 days, escalate to a human agent",
              "category": "escalation",
              "complexity": 3,
              "scope": "conditional",
              "target_tools": ["refund_order", "check_order_status"],
              "conditions": ["order is older than 30 days", "customer requests refund"]
          }
      ],
      "interactions": [
          {"from": "R001", "to": "R005", "type": "co-occurrence", "description": "Both apply when handling customer data"}
      ],
      "total_rules": 15,
      "total_complexity": 38,
      "by_category": {"prohibition": 4, "requirement": 5, "constraint": 3, "escalation": 2, "fallback": 1},
      "guardrail_language": "Spanish",
      "guardrail_language_matches_conversation": true
  }
  ```

### 6.6 Language Mismatch Detection

- [ ] Compare `guardrail_language` with `conversation_language` (from `_detect_conversation_language()` in builder.py:24)
- [ ] If they differ, flag it: guardrails written in English but conversations in Spanish means guardrails may not be tested in the deployment language
- [ ] This addresses the multilingual safety gap finding (MrGuard, SEALGuard)

## Files Modified

| File | Changes |
|------|---------|
| `src/patterns/rule_extractor.py` | **New file**: PolicyRule, PolicyGraph, pattern-based extraction |
| `src/ai_analyzer/prompts.py` | New `GUARDRAIL_EXTRACTION_PROMPT` |
| `src/ai_analyzer/analyzer.py` | New `analyze_guardrails()` function |
| `src/graph/builder.py` | Add `guardrails` section to Agent Map |
| `analyze.py` | Update CLI summary with rule count and complexity |

## Done When

- System prompts are parsed into numbered `PolicyRule` objects with categories and complexity scores
- Both pattern-based (offline) and AI-powered extraction work
- The Agent Map contains a `guardrails` section with all extracted rules
- Rule interactions (conflicts, co-occurrences) are identified
- Language mismatch between guardrails and conversations is flagged
- Phase B can read `guardrails.rules[]` and generate one rule-violation test per rule
