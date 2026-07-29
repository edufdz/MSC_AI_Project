# Investigation Package — Real vs Simulated Agent Failures

**Assembled 2026-07-24.** Self-contained package for the real-vs-simulated
failure investigation: data, scripts, results, and the LaTeX report.
Everything here is anonymised — the raw PII-bearing export is deliberately
excluded.

## Contents

| Path | What it is |
|---|---|
| `01_methodology/REAL_VS_SIM_COMPARISON_PLAN.md` | Pre-registered design: three comparison layers, reachability, statistics, validity threats |
| `01_methodology/TECH_REPAIR_LIVE_SIMULATION.md` | How the verbatim live-agent simulation works |
| `02_data/real/tech_repair-conversations-anonymized.json` | The real corpus: 1,299 anonymised production conversations |
| `02_data/simulated/run_v4_40tests.json` | 40-test live run (generated_tech_repair suite) |
| `02_data/simulated/run_web_150tests.json` | 150-test run launched from the web platform |
| `02_data/simulated/run_200tests_recovered.json` | 200-test CLI run (recovered from git commit 420f116 traces) |
| `02_data/simulated/scale_batches/N0010…N1000/` | The 7 independent scale-study batches: conversations.json + test_run_report.json + failure_inbox.json each |
| `03_analysis_scripts/compare_real_vs_sim.py` | Scorer-parity comparison (adapter + JSD + reachability + report) |
| `03_analysis_scripts/scale_curves.py` | Scale-study curves and tables |
| `03_analysis_scripts/gen_scale_suites.py` | Regenerates the tiled suites byte-identically (seed 42+N) |
| `04_results/comparison/` | Fixed-scale comparison: real_vs_sim.json, REPORT.md, category chart |
| `04_results/scale_study/` | Scale study: scale_curves.json, SCALE_REPORT.md, curves chart |
| `05_report/report.tex` / `report.pdf` | The in-depth LaTeX report (compiled with tectonic) |

## Headline numbers

- Real: 376/1,299 failures (28.9%) · Sim (pooled 390): 82 failures (21.0%) — identical rule-based scorer, min_score=3.
- **5/7 reachable real failure categories reproduced (71%)**; loop/stall dominates both corpora (68% real / 81% sim).
- **Coverage saturates at N≈50** and never grows through N=1000 (or the 2,560-conversation pool).
- comprehension + data_gap (jointly >50% of real failures) are **structurally unreachable**: personas never repeat verbatim; the fake customer's data is complete.
- JSD(real, sim) ≈ 0.24 bits at every scale (noise floor 0.005) — scale buys precision, not correspondence.

## Reproduce

```bash
cd 03_analysis_scripts
python3 compare_real_vs_sim.py --real ../02_data/real/tech_repair-conversations-anonymized.json \
    --sim ../02_data/simulated/run_v4_40tests.json [--sim ...] -o out/
python3 scale_curves.py --real ../02_data/real/tech_repair-conversations-anonymized.json \
    --batches ../02_data/simulated/scale_batches -o out/scale/
```

(The scripts import `src/` from `debugger-platforn/`; run them from there, or
keep this package inside the repo.)

## Caveats that must accompany any citation

1. Ground-truth labels are rule-based; the **human annotation pass (Cohen's κ)
   is still pending** (`run_validation.py annotate`).
2. Saturation at 5 categories is a joint property of the simulator AND the
   150-test suite; feedback-seeded suites may shift the plateau.
3. Simulated failure *frequencies* over-represent adversarial boundaries
   (escalation_failure, premature_exit) by suite design — not production forecasts.
