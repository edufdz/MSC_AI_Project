# Usage Guide: Running the Agent Debugger

All commands run from the `debugger-platforn/` directory.

```
cd debugger-platforn
```

---

## Pipeline overview

```
Phase A: Analyze    ──>  agent_map.json
Phase B: Generate   ──>  test_suite.json  (+ persona_library.json, scenario_catalog.json)
Phase C: Execute    ──>  test_run_report.json + failure_inbox.json + traces/
Phase D: Diagnose   ──>  diagnosis_report.json
Phase E: Improve    ──>  improvement outputs
```

Each phase takes the output of the previous phase as input. You can run them individually or as a full pipeline.

---

## Phase A: Analyze agent codebase

Scans the agent source code and produces an `agent_map.json` describing its tools, prompts, memory, and risks.

```bash
# Basic (offline, no AI)
python analyze.py /path/to/agent/repo --skip-ai

# With AI semantic analysis (needs ANTHROPIC_API_KEY)
python analyze.py /path/to/agent/repo

# Custom output path
python analyze.py /path/to/agent/repo -o my_agent_map.json
```

**Output:** `agent_map.json`

| Flag | Default | Description |
|------|---------|-------------|
| `--skip-ai` | off | Skip AI analysis (offline mode) |
| `--output, -o` | `agent_map.json` | Output file path |
| `--language, -l` | all | Language filter for scanning |
| `--verbose, -v` | off | Show parse warnings |

> **Note:** For Victoria, the agent map is already created at `agent_map.json`. You can skip this phase.

---

## Phase B: Generate test suite

Creates personas, scenarios, coverage goals, and combines them into a test suite.

```bash
# Offline with tlahuac personas (recommended for Victoria)
python generate_tests.py agent_map.json --use-tlahuac --skip-ai --count 20

# Offline with template personas
python generate_tests.py agent_map.json --skip-ai --count 20

# With AI enrichment
python generate_tests.py agent_map.json --count 250 --persona-count 8 --scenario-count 10

# Custom output directory
python generate_tests.py agent_map.json --use-tlahuac --skip-ai --count 20 -o my_tests/
```

**Output directory** (default `generated/`):
- `test_configuration.json` — coverage goals and sandbox config
- `persona_library.json` — all personas used
- `scenario_catalog.json` — all scenarios and variants
- `test_suite.json` — the executable test cases

| Flag | Default | Description |
|------|---------|-------------|
| `--use-tlahuac` | off | Use only tlahuac personas (see [PERSONAS_GUIDE.md](PERSONAS_GUIDE.md)) |
| `--tlahuac-dir` | auto | Path to tlahuac data directory |
| `--skip-ai` | off | Skip all AI generation |
| `--count, -c` | 250 | Target number of test cases |
| `--persona-count` | 8 | AI-generated personas to add |
| `--scenario-count` | 10 | AI-generated scenarios to add |
| `--variants` | 3 | Variants per base scenario |
| `--output-dir, -o` | `generated` | Output directory |
| `--seed` | random | Random seed |

---

## Phase C: Execute tests

Runs the test suite against the agent, collects traces, and generates a failure inbox.

```bash
# Against victoria-fake (real agent)
python execute_tests.py generated/test_suite.json agent_map.json --ai-personas

# With mock agent (no real agent needed)
python execute_tests.py generated/test_suite.json agent_map.json --mock --ai-personas

# Limit to 10 tests, custom output
python execute_tests.py generated/test_suite.json agent_map.json --ai-personas --count 10 -o results

# Offline persona messages (no API costs)
python execute_tests.py generated/test_suite.json agent_map.json --mock
```

**Output directory** (default `results/`):
- `test_run_report.json` — pass/fail stats, coverage, timing
- `failure_inbox.json` — all failures with context
- `conversations.log` — JSON lines log (for live viewer)
- `traces/` — per-test trace files

| Flag | Default | Description |
|------|---------|-------------|
| `--output, -o` | `results` | Output directory |
| `--workers, -w` | 10 | Parallel workers |
| `--count, -c` | 0 (all) | Limit to first N tests |
| `--mock` | off | Use mock agent (no real agent) |
| `--ai-personas` | off | Use AI for persona messages (costs $) |
| `--traces/--no-traces` | on | Save per-test trace files |
| `--no-monitor` | off | Disable live dashboard in terminal |
| `--fail-rate` | 0.05 | Mock agent failure rate |
| `--language, -l` | auto | Language for persona messages |
| `--seed` | random | Random seed |
| `--diagnose` | off | Auto-run Phase D after execution |
| `--improve` | off | Auto-run Phase D + E after execution |

### Live conversation viewer

While tests run, open a second terminal:

```bash
python live_viewer.py
# Open http://localhost:8080 in browser
```

The viewer auto-detects the most recent `conversations.log` and streams messages in real time.

```bash
# Specific log file
python live_viewer.py results/conversations.log

# Custom port
python live_viewer.py --port 9090
```

---

## Phase D: Diagnose failures

Clusters failures, identifies root causes, generates minimal reproductions, and proposes fixes.

```bash
# AI-powered analysis
python diagnose_failures.py results/failure_inbox.json results/test_run_report.json agent_map.json

# Offline heuristics only
python diagnose_failures.py results/failure_inbox.json results/test_run_report.json agent_map.json --skip-ai

# Custom output
python diagnose_failures.py results/failure_inbox.json results/test_run_report.json agent_map.json -o results/diagnosis.json
```

**Output:** `diagnosis_report.json`

| Flag | Default | Description |
|------|---------|-------------|
| `--output, -o` | `diagnosis_report.json` | Output file |
| `--skip-ai` | off | Offline heuristics only |
| `--use-embeddings` | off | Use embeddings for clustering |
| `--max-retries` | 3 | API retry attempts |

---

## Phase E: Improve agent

Applies fixes from Phase D, runs A/B tests, validates improvements, generates regression tests.

```bash
# Dry run (no files modified)
python improve_agent.py results/diagnosis_report.json agent_map.json generated/test_suite.json

# Apply fixes
python improve_agent.py results/diagnosis_report.json agent_map.json generated/test_suite.json --apply

# With agent source directory
python improve_agent.py results/diagnosis_report.json agent_map.json generated/test_suite.json \
  --apply -d /path/to/agent/src --smoke-limit 20 --full-limit 100
```

**Output directory** (default `improvement/`):
- Applied fixes log
- A/B test results
- Regression test suite
- Deployment package

| Flag | Default | Description |
|------|---------|-------------|
| `--output, -o` | `improvement` | Output directory |
| `--apply` | off | Actually apply fixes (default is dry run) |
| `--agent-dir, -d` | `.` | Agent source directory for patching |
| `--baseline-fail-rate` | 0.05 | Baseline fail rate for A/B |
| `--fixed-fail-rate` | 0.01 | Fixed fail rate for A/B |
| `--smoke-limit` | 10 | Max tests for smoke test |
| `--full-limit` | 50 | Max tests for full test |
| `--workers, -w` | 10 | Parallel workers |

---

## Full pipeline (A through E in one command)

Runs all phases in sequence with a single command.

```bash
# Full pipeline, offline, mock agent
python run_pipeline.py /path/to/agent --mock --skip-ai --test-count 20 --count 10

# Stop after Phase C (no diagnosis/improvement)
python run_pipeline.py /path/to/agent --mock --skip-ai --stop-after c

# Skip Phase A (use existing agent map)
python run_pipeline.py /path/to/agent --agent-map agent_map.json --mock --skip-ai --test-count 20

# Skip Phase A + B (use existing agent map + test suite)
python run_pipeline.py /path/to/agent \
  --agent-map agent_map.json \
  --test-suite generated/test_suite.json \
  --mock --count 10

# Full pipeline with AI
python run_pipeline.py /path/to/agent --test-count 250 --ai-personas
```

| Flag | Default | Description |
|------|---------|-------------|
| `--output-dir, -o` | `pipeline_output` | Base output directory |
| `--skip-ai` | off | Skip all AI calls |
| `--stop-after` | `e` | Stop after phase: `a`, `b`, `c`, `d`, or `e` |
| `--agent-map` | none | Skip Phase A, use this agent map |
| `--test-suite` | none | Skip Phase B, use this test suite |
| `--mock` | off | Use mock agent connector |
| `--test-count` | 250 | Target test cases for Phase B |
| `--count, -c` | 0 (all) | Limit tests to execute in Phase C |
| `--ai-personas` | off | Use AI for persona messages |
| `--apply-fixes` | off | Apply fixes in Phase E |
| `--seed` | random | Random seed |

---

## Common workflows

### Quick smoke test with tlahuac (Victoria)

```bash
python generate_tests.py agent_map.json --use-tlahuac --skip-ai --count 10
python execute_tests.py generated/test_suite.json agent_map.json --ai-personas --count 10 -o results/smoke
```

### Full test run with diagnosis

```bash
python generate_tests.py agent_map.json --use-tlahuac --skip-ai --count 100
python execute_tests.py generated/test_suite.json agent_map.json --ai-personas --diagnose -o results/full
```

### End-to-end with improvement

```bash
python generate_tests.py agent_map.json --use-tlahuac --skip-ai --count 50
python execute_tests.py generated/test_suite.json agent_map.json --ai-personas --improve -o results/full
```

### Reproduce a specific failure

Look at the trace file for the failed test, then re-run with seed:

```bash
python generate_tests.py agent_map.json --use-tlahuac --skip-ai --count 50 --seed 42
python execute_tests.py generated/test_suite.json agent_map.json --ai-personas --count 1 --seed 42
```
