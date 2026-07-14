# Project Context — Debugging Agent Project

## About
Eduardo Fernandez Salazar, Imperial College London MSc AI. Individual project (dissertation), 2026.

Developer of the agent testing platform (the "debugging agent project") — an automated adversarial testing system for conversational AI agents with a four-phase pipeline (A: agent-map analysis, B: persona/scenario generation, C: test execution, D: failure diagnosis). Also operates the Samsung WhatsApp customer-support agent at Pulpoo, which is the production validation target.

---

## Title
"Closing the Loop Between Synthetic Agent Testing and Production Reality"
Subtitle: A Production-Feedback System for Predictive Agent Reliability Testing, Validated on a Live Deployed Call-Centre Agent

## Core Research Question
*Does synthetic adversarial testing predict the failures that occur in production, and does grounding the test-generation process in real production failures make it measurably better at predicting future failures than testing generated without that grounding?*

## Four Sub-Questions (RQs)
1. **Predictive validity** — Do synthetic failures match real production failures? (precision/recall over shared failure taxonomy)
2. **Coverage gaps** — Which real failure categories does synthetic testing systematically miss? (long-horizon, tool-integration, rare intents)
3. **Production feedback** — Does seeding generation with real failures improve held-out recall vs blind generation?
4. **Generation method** — Which strategy (template/persona, naive LLM, GAN-style generator-critic) achieves highest real-failure recall per testing budget?

## Three Contributions
1. **Engineering**: Agent testing platform extended with production-feedback subsystem (sandbox bridge, shared taxonomy, projection layer, measurement engine)
2. **Research**: Production-feedback loop method (ingest real failures -> reproducible test scenarios -> re-seed generation)
3. **Empirical**: First measurement of predictive validity of synthetic testing against independently-logged real production failures

## The Three Systems
1. **Agent testing platform / debugging agent project** (this repo: `debugger-platforn/`) — Phases A-D pipeline, enhanced during project
2. **Deployed Samsung WhatsApp agent** (Pulpoo) — real production agent handling Spanish-language customer support
3. **Langfuse observability** — production traces in Langfuse Cloud, self-hosted instance stood up for synthetic traces

## Current Status (updated 2026-07-14 — post Background Report)
- All three systems exist and run independently
- Platform Phases A-D enhanced substantially
- Langfuse production observability integration is live
- **DESIGN CHANGE**: no direct connection between the Samsung production
  system and the simulator. Conversations are extracted once, anonymised,
  and compared offline against simulation results.
- **BUILT** (see docs/RESEARCH_WORKFLOW.md):
  - Batch anonymisation of the export (`anonymize_export.py` + `anonymization/` 3-pass backend)
  - Production ingestion + ground truth from human-process signals (`src/production/`)
  - Frozen shared failure taxonomy, 16 categories (`src/evaluation/taxonomy.py`, v1.0-frozen-2026-07-14)
  - Projection layer, both sources → shared taxonomy (`src/evaluation/projection.py`)
  - Measurement engine: per-category P/R, recall-vs-budget, bootstrap CIs, permutation tests (`src/evaluation/measurement.py`)
  - Production-feedback loop with chronological-holdout leakage guard (`src/feedback/`)
  - Sandbox bridge: offline simulation endpoint + replay/fidelity comparator (`src/sandbox/`, `sandbox_bridge.py`)
  - RQ1–RQ4 experiment runner with charts + markdown report (`run_experiments.py`)
  - Web integration: `/api/research/*` routes + Research dashboard page

## Central Open Problem
Integration of the three systems into one closed measurement loop. Key pieces needed:
- **Sandbox bridge**: wrap deployed agent with mock tools behind HTTP endpoint so synthetic tests exercise the real agent without touching live customers
- **Shared failure taxonomy**: frozen taxonomy mapping both synthetic (Phase D) and production failure signals
- **Projection layer**: maps failures from different sources onto the shared taxonomy
- **Measurement engine**: computes precision, recall, per-category breakdowns, recall-vs-budget curves
- **Production-feedback loop**: converts real failures into reproducible test scenarios, re-seeds generation
- **Anonymisation pipeline**: strips PII from production conversations

## Eight-Week Plan
| Week | Focus | Milestone |
|------|-------|-----------|
| 1 | Repo setup, data extraction, anonymisation, self-hosted Langfuse, ethics | Verified-clean anonymised conversations |
| 2 | Sandbox bridge, mock tool layer, failure injection | Platform can talk to sandboxed agent end-to-end |
| 3 | Replay harness, frozen taxonomy, projection layer | Defensible fidelity score, frozen taxonomy |
| 4 | Measurement engine, blind arm | First end-to-end blind synthetic failure set |
| 5 | Train/held-out time split | Headline predictive-validity result (RQ1, RQ2) |
| 6 | Production-feedback loop | Feedback vs blind recall with significance (RQ3) |
| 7 | Template/naive-LLM/GAN generators, budget sweeps | All four RQs answered (RQ4) |
| 8 | Final charts, tables, assemble chapters | Complete draft, reproducible results |

**Fallback**: Weeks 1-5 alone produce a complete publishable study (RQ1+RQ2). Weeks 6-7 are additive.

## Key Methodological Decisions
- Ground truth is constructed from **independent human-process signals** (escalations, complaints, QA flags), NOT from LLM-as-a-judge scores — this avoids circularity
- All testing runs against a **sandboxed copy** of the Samsung agent, never the live production system
- Synthetic and production data kept in **separate Langfuse instances** (self-hosted vs cloud)
- A negative result (low predictive validity) is explicitly designed to be as valuable as a positive one

## Repo Structure
- `debugger-platforn/` — the debugging agent project (agent testing platform), Python
- `tlahuac_simulator_agent/` — scripts related to simulation
- `fake-car-dealership-agent/` — TypeScript test agent (tools, prompts, mock data)
- `victoria-fake/` — another test target
- `docs/` — documentation
- `poster/` — poster materials

## Key Literature Context
Positioned against: AgentBench, WebArena, tau-bench (curated benchmarks), AgentDojo, ToolFuzz (adversarial testers), LangSmith/AgentOps/Langfuse (observability), MAD-GAN/MALLM-GAN (generator-critic frameworks). None combine predictive validity measurement with production-feedback grounding.
