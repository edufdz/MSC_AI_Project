# Sprint 3 — OWASP/MITRE Risk Taxonomy Mapping

## Goal

Map every detected risk to authoritative taxonomy identifiers: **OWASP Top 10 for LLM Applications 2025**, **OWASP Top 10 for Agentic Applications 2026**, and **MITRE ATLAS**. Currently, risks are labelled with ad-hoc types (`"pii"`, `"critical_action"`, `"data_modification"`) and severities. This sprint replaces those with standardised, citable identifiers that Phase B can use to prioritise adversarial scenarios.

**Can run in parallel with**: Sprint 1 (tree-sitter) or Sprint 2 (preconditions) — this sprint modifies `RiskFlag`, `framework_signatures.py`, and `risk/analyzer.py`, which the other sprints don't touch.

## Why This Matters for Phase B

Taxonomy-aligned risks give Phase B a **priority vocabulary**: an `LLM06 Excessive Agency` risk generates privilege-escalation scenarios; an `ASI02 Tool Misuse` risk generates tool-abuse scenarios. Without standard labels, Phase B treats all risks equally.

## Taxonomy Reference

### OWASP Top 10 for LLM Applications 2025

| ID | Name | Code-Detectable? |
|----|------|-------------------|
| LLM01 | Prompt Injection | Partially (missing input sanitisation) |
| LLM02 | Sensitive Information Disclosure | Yes (PII flows, logging of sensitive data) |
| LLM03 | Supply Chain Vulnerabilities | Partially (dependency analysis) |
| LLM04 | Data and Model Poisoning | No (runtime concern) |
| LLM05 | Improper Output Handling | Partially (missing output validation) |
| LLM06 | Excessive Agency | Yes (over-privileged tools, missing confirmation gates) |
| LLM07 | System Prompt Leakage | Partially (prompt exposure patterns) |
| LLM08 | Vector and Embedding Weaknesses | No (runtime concern) |
| LLM09 | Misinformation | No (runtime concern) |
| LLM10 | Unbounded Consumption | Partially (missing rate limits, token caps) |

### OWASP Top 10 for Agentic Applications 2026

| ID | Name | Code-Detectable? |
|----|------|-------------------|
| ASI01 | Agent Goal Hijack | Partially (weak system prompt guardrails) |
| ASI02 | Tool Misuse and Exploitation | Yes (tools without input validation) |
| ASI03 | Identity and Privilege Abuse | Yes (over-scoped tool permissions) |
| ASI04 | Agentic Supply Chain Vulnerabilities | Partially (MCP server trust) |
| ASI05 | Unexpected Code Execution | Yes (eval, exec, subprocess calls) |
| ASI06 | Memory and Context Poisoning | Partially (unvalidated memory writes) |
| ASI07 | Insecure Inter-Agent Communication | Partially (unencrypted agent-to-agent calls) |
| ASI08 | Cascading Failures | Partially (missing error handling in tool chains) |
| ASI09 | Human-Agent Trust Exploitation | No (design concern) |
| ASI10 | Rogue Agents | No (runtime concern) |

## Tasks

### 3.1 Define Taxonomy Constants

**File**: `config/framework_signatures.py` (after line 112)

- [ ] Add OWASP LLM 2025 identifiers:
  ```python
  OWASP_LLM_2025 = {
      "LLM01": "Prompt Injection",
      "LLM02": "Sensitive Information Disclosure",
      "LLM03": "Supply Chain Vulnerabilities",
      "LLM04": "Data and Model Poisoning",
      "LLM05": "Improper Output Handling",
      "LLM06": "Excessive Agency",
      "LLM07": "System Prompt Leakage",
      "LLM08": "Vector and Embedding Weaknesses",
      "LLM09": "Misinformation",
      "LLM10": "Unbounded Consumption",
  }
  ```

- [ ] Add OWASP Agentic 2026 identifiers:
  ```python
  OWASP_AGENTIC_2026 = {
      "ASI01": "Agent Goal Hijack",
      "ASI02": "Tool Misuse and Exploitation",
      "ASI03": "Identity and Privilege Abuse",
      "ASI04": "Agentic Supply Chain Vulnerabilities",
      "ASI05": "Unexpected Code Execution",
      "ASI06": "Memory and Context Poisoning",
      "ASI07": "Insecure Inter-Agent Communication",
      "ASI08": "Cascading Failures",
      "ASI09": "Human-Agent Trust Exploitation",
      "ASI10": "Rogue Agents",
  }
  ```

- [ ] Add mapping from current risk types to taxonomy IDs:
  ```python
  RISK_TO_TAXONOMY = {
      # PII risks
      ("pii", "email"): ["LLM02", "ASI03"],
      ("pii", "phone"): ["LLM02", "ASI03"],
      ("pii", "ssn"): ["LLM02", "ASI03"],
      ("pii", "credit_card"): ["LLM02", "ASI03"],
      ("pii", "address"): ["LLM02", "ASI03"],
      # Critical action risks
      ("critical_action", "financial"): ["LLM06", "ASI02"],
      ("critical_action", "data_modification"): ["LLM06", "ASI02"],
      ("critical_action", "user_management"): ["LLM06", "ASI03"],
      ("critical_action", "communication"): ["LLM06", "ASI02"],
      # Code execution risks
      ("unsafe_operation", "eval"): ["ASI05", "LLM01"],
      ("unsafe_operation", "exec"): ["ASI05", "LLM01"],
      ("unsafe_operation", "subprocess"): ["ASI05"],
  }
  ```

### 3.2 Extend the `RiskFlag` Dataclass

**File**: `src/risk/analyzer.py` (lines 16-23)

- [ ] Add taxonomy fields to `RiskFlag`:
  ```python
  @dataclass
  class RiskFlag:
      # ... existing fields ...
      taxonomy_ids: list[str] = field(default_factory=list)       # e.g., ["LLM06", "ASI02"]
      taxonomy_names: list[str] = field(default_factory=list)     # e.g., ["Excessive Agency", "Tool Misuse and Exploitation"]
      taxonomy_source: str = ""                                    # "OWASP_LLM_2025" | "OWASP_AGENTIC_2026" | "MITRE_ATLAS"
  ```

### 3.3 Add Unsafe Operation Detection

**File**: `src/risk/analyzer.py`

Currently the risk analyzer only checks PII and critical actions. Add detection for code-execution risks:

- [ ] Create `detect_unsafe_operations(tools) -> list[RiskFlag]`:
  - Scan tool `code_snippet` and `body_text` for: `eval(`, `exec(`, `subprocess.`, `os.system(`, `os.popen(`, `__import__(`
  - Severity: `"critical"`
  - Taxonomy: `["ASI05", "LLM01"]`

- [ ] Create `detect_excessive_agency(tools, prompts) -> list[RiskFlag]`:
  - Flag tools with no input validation (no guard clauses in code)
  - Flag state-modifying tools without confirmation gates (no `confirm`, `approve`, `verify` in call chain)
  - Flag if tool count > 10 with no permission scoping
  - Severity: `"high"`
  - Taxonomy: `["LLM06"]`

### 3.4 Apply Taxonomy Labels to All Risks

**File**: `src/risk/analyzer.py`

- [ ] In `analyze_risks()` (line 126), after collecting all risks, apply taxonomy mapping:
  ```python
  for risk in all_risks:
      key = (risk.risk_type, risk.pii_type or risk.risk_type)
      if key in RISK_TO_TAXONOMY:
          risk.taxonomy_ids = RISK_TO_TAXONOMY[key]
          risk.taxonomy_names = [OWASP_LLM_2025.get(tid) or OWASP_AGENTIC_2026.get(tid, tid) for tid in risk.taxonomy_ids]
  ```

### 3.5 Update Agent Map Risk Output

**File**: `src/graph/builder.py`

- [ ] In `generate_agent_map()`, include taxonomy fields in `risk_flags.all_risks[]`:
  ```json
  {
    "tool": "payment_tool",
    "risk_type": "critical_action",
    "severity": "critical",
    "taxonomy_ids": ["LLM06", "ASI02"],
    "taxonomy_names": ["Excessive Agency", "Tool Misuse and Exploitation"],
    "description": "Financial operation: payment",
    "mitigation": "Require user confirmation before execution"
  }
  ```

- [ ] Add a `risk_summary` section to the Agent Map:
  ```json
  "risk_summary": {
      "by_taxonomy": {
          "LLM06": {"count": 3, "name": "Excessive Agency"},
          "ASI02": {"count": 2, "name": "Tool Misuse and Exploitation"},
          "LLM02": {"count": 5, "name": "Sensitive Information Disclosure"}
      },
      "highest_severity": "critical",
      "total_risks": 10
  }
  ```

### 3.6 Update CLI Summary

**File**: `analyze.py`

- [ ] In `_print_risk_summary()` (line 82), show risks grouped by taxonomy ID instead of just raw type/severity

## Files Modified

| File | Changes |
|------|---------|
| `config/framework_signatures.py` | Add taxonomy constants and mapping dict |
| `src/risk/analyzer.py` | Extend `RiskFlag`, add new detectors, apply taxonomy labels |
| `src/graph/builder.py` | Include taxonomy fields in Agent Map output |
| `analyze.py` | Update CLI risk summary display |

## Done When

- Every `RiskFlag` carries `taxonomy_ids` and `taxonomy_names` mapped to OWASP/MITRE
- New detectors catch unsafe operations (`eval`/`exec`/`subprocess`) and excessive agency
- The Agent Map `risk_flags.all_risks[]` includes taxonomy identifiers
- A new `risk_summary.by_taxonomy` section aggregates risks by taxonomy ID
- Phase B can read `taxonomy_ids` to prioritise scenario generation (backward compatible — new fields are additive)
