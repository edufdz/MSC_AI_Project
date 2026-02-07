Phase A: Discovery & Mapping
├─ Code analysis (current)
├─ Tool catalog + dependency graph
├─ Risk surface identification (PII, critical paths)
└─ Success criteria definition ← NEW

Phase B: Test Planning
├─ Persona creation (current)
├─ Scenario library (current)
├─ Coverage goals (tool, intent, edge cases) ← ENHANCED
├─ Sandbox configuration ← NEW
└─ Baseline metrics capture ← NEW

Phase C: Execution
├─ Smoke test (10-20 runs) ← NEW
├─ Full test suite (250/500/1000)
├─ Chaos injection (timeouts, errors, etc.)
└─ Live monitoring

Phase D: Analysis ← NEEDS EXPANSION
├─ Trace collection
├─ Failure clustering ← NEW (this is critical!)
├─ Root cause labeling ← NEW
├─ Pattern detection ← NEW
└─ Dashboard + failure inbox

Phase E: Improvement
├─ Ranked improvement proposals
├─ A/B experiment setup
├─ Regression suite creation ← NEW
└─ Deployment + verification

Phase F: Continuous Loop ← NEW
├─ Regression runs on every code change
├─ Baseline drift detection
└─ Production trace integration (optional)