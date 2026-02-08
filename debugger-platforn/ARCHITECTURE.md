# Agent Debugger Platform — System Architecture

## 1. High-Level Pipeline

```
 AGENT SOURCE CODE                                                              DEPLOYMENT PACKAGE
      |                                                                                ^
      v                                                                                |
 ┌─────────┐     ┌──────────────┐     ┌──────────────┐     ┌──────────────┐     ┌─────────────┐
 │ PHASE A  │     │   PHASE B    │     │   PHASE C    │     │   PHASE D    │     │   PHASE E   │
 │ Analyze  │────▶│   Generate   │────▶│   Execute    │────▶│  Diagnose    │────▶│  Improve    │
 │          │     │              │     │              │     │              │     │             │
 │ Scan     │     │ B1 Coverage  │     │ Run tests    │     │ Cluster      │     │ Apply fixes │
 │ Parse    │     │ B2 Personas  │     │ Mock / Live  │     │ Root cause   │     │ A/B test    │
 │ Detect   │     │ B3 Scenarios │     │ Monitor      │     │ Reproduce    │     │ Validate    │
 │ Map      │     │ B4 Suite     │     │ Aggregate    │     │ Propose fix  │     │ Regress     │
 │          │     │              │     │              │     │ Rank         │     │ Package     │
 └────┬─────┘     └──────┬───────┘     └──────┬───────┘     └──────┬───────┘     └──────┬──────┘
      │                  │                    │                    │                    │
      v                  v                    v                    v                    v
 agent_map.json    test_suite.json     test_run_report.json  diagnosis_report.json  improvement/
                   persona_library.json failure_inbox.json                          applied_fixes.json
                   scenario_catalog.json traces/                                   ab_test_results.json
                   test_configuration.json                                         regression_tests.json
                                                                                   deployment/
```

## 2. CLI Entry Points & Orchestration

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          ORCHESTRATION LAYER                                │
│                                                                             │
│   run_pipeline.py    ─────── Full A → B → C → D → E pipeline               │
│     --stop-after a|b|c|d|e   (control how far to run)                       │
│     --agent-map PATH         (skip Phase A)                                 │
│     --test-suite PATH        (skip Phase B)                                 │
│                                                                             │
│   generate_tests.py  ─────── Unified Phase B  (B1 → B2 → B3 → B4)         │
│                                                                             │
│   execute_tests.py   ─────── Phase C  (+D with --diagnose)                  │
│                                       (+D+E with --diagnose --improve)      │
│                                                                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                        STANDALONE PHASE CLIs                                │
│                                                                             │
│   analyze.py            Phase A   repo_path → agent_map.json                │
│   coverage_builder.py   Phase B1  agent_map → test_configuration.json       │
│   persona_builder.py    Phase B2  agent_map → persona_library.json          │
│   scenario_builder.py   Phase B3  agent_map → scenario_catalog.json         │
│   testsuite_builder.py  Phase B4  all B1-B3 → test_suite.json              │
│   diagnose_failures.py  Phase D   inbox+report+map → diagnosis_report.json  │
│   improve_agent.py      Phase E   diag+map+suite → improvement/             │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

## 3. Data Flow: Artifacts Between Phases

```
               ┌─────────────────────────────────────────────────┐
               │              agent_map.json                      │
               │  metadata.type          "support"                │
               │  metadata.framework     "langchain"              │
               │  components.tools[]     [{name, desc, risk}]     │
               │  components.prompts[]   [{name, content}]        │
               │  risk_flags             {pii, critical_actions}  │
               │  graph                  {nodes[], edges[]}       │
               └──┬──────────┬──────────┬──────────┬─────────────┘
                  │          │          │          │
         ┌────────┘    ┌─────┘    ┌─────┘          │
         v             v          v                 │
  ┌────────────┐ ┌──────────┐ ┌──────────────┐     │
  │ Coverage   │ │ Persona  │ │  Scenario    │     │
  │ Goals      │ │ Library  │ │  Catalog     │     │
  │            │ │          │ │              │     │
  │ tool_cov:  │ │ personas:│ │ scenarios:   │     │
  │  min_invoc │ │  traits  │ │  type        │     │
  │  combos    │ │  style   │ │  difficulty  │     │
  │ edge_case: │ │  edge_   │ │  tools       │     │
  │  ambiguous │ │  behav.  │ │  chaos_cfg   │     │
  │ stressor:  │ │  messages│ │  success/    │     │
  │  timeout   │ │          │ │  failure cnd │     │
  │ sandbox:   │ │          │ │  variants    │     │
  │  tool_cfgs │ │          │ │              │     │
  └─────┬──────┘ └────┬─────┘ └──────┬───────┘     │
        │              │              │              │
        └──────────────┼──────────────┘              │
                       v                             │
               ┌───────────────┐                     │
               │  test_suite   │                     │
               │  .json        │                     │
               │               │                     │
               │ test_cases[]: │                     │
               │  scenario     │                     │
               │  persona      │                     │
               │  coverage_goal│                     │
               │  target_tool  │                     │
               │  difficulty   │                     │
               │  exec_config  │                     │
               │               │                     │
               │ summary:      │                     │
               │  by_difficulty │                     │
               │  by_goal      │                     │
               │  tool_counts  │                     │
               └───────┬───────┘                     │
                       │                             │
                       v                             │
               ┌───────────────────┐                 │
               │  Phase C Engine   │◀────────────────┘
               │                   │
               │  MockConnector    │
               │     or            │
               │  APIConnector     │
               │                   │
               │  async runner     │
               │  event_queue      │
               │  monitor          │
               │  aggregator       │
               └──┬──────────┬─────┘
                  │          │
                  v          v
    ┌──────────────┐  ┌──────────────┐
    │test_run_     │  │failure_      │
    │report.json   │  │inbox.json    │
    │              │  │              │
    │ pass_rate    │  │ failures[]:  │
    │ passed/failed│  │  test_id     │
    │ tool_coverage│  │  scenario    │
    │ by_difficulty│  │  persona     │
    │ by_goal      │  │  reason      │
    │ cost         │  │  trace_file  │
    │ duration     │  │  chaos_evts  │
    └──────┬───────┘  └──────┬───────┘
           │                 │
           └────────┬────────┘
                    v
            ┌───────────────┐
            │  Phase D      │
            │  Diagnosis    │
            │               │
            │  Cluster      │
            │  Root cause   │
            │  Reproduce    │
            │  Fix propose  │
            │  Priority rank│
            └───────┬───────┘
                    v
            ┌────────────────┐
            │ diagnosis_     │
            │ report.json    │
            │                │
            │ clusters[]:    │
            │  root_cause    │
            │  severity      │
            │  affected_tools│
            │  reproduction  │
            │                │
            │ fix_proposals[]│
            │  fix_type      │
            │  changes       │
            │  est_fix_rate  │
            │  effort/risk   │
            │                │
            │ priority_rank[]│
            └───────┬────────┘
                    │
                    v
            ┌───────────────────┐
            │  Phase E          │
            │  Improvement      │
            │                   │
            │  1. Apply fixes   │
            │  2. A/B smoke test│
            │  3. A/B full test │
            │  4. Regression gen│
            │  5. Validate      │
            │  6. Package       │
            └──┬──┬──┬──┬──┬───┘
               │  │  │  │  │
               v  v  v  v  v
  ┌──────────┬──────────┬──────────────┬────────────┬──────────┐
  │applied_  │ab_test_  │improvement_  │regression_ │deployment│
  │fixes.json│results   │report.json   │tests.json  │/         │
  │          │.json     │              │            │          │
  │ status   │ baseline │ pass_rate_   │ test_name  │ version  │
  │ diff     │ fixed    │  improvement │ root_cause │ changelog│
  │ rollback │ p_value  │ ready_deploy │ priority   │ rollback │
  └──────────┴──────────┴──────────────┴────────────┴──────────┘
```

## 4. Internal Module Architecture

```
src/
├── ingestion/                          ┌─────────────────────────────────┐
│   └── ingestor.py                     │        Phase A Internals        │
│       ingest_directory()─────────────▶│                                 │
│       → IngestionResult               │  ingest_directory()             │
│         .files[]                      │       │                         │
│         .entry_points[]               │       v                         │
│         .prompt_files[]               │  analyze_files()                │
│                                       │       │  (Tree-sitter AST)      │
├── analysis/                           │       v                         │
│   └── static_analyzer.py              │  detect_patterns()              │
│       analyze_files()────────────────▶│       │  (framework sigs)       │
│       → List[FileSymbols]             │       v                         │
│         .functions[]                  │  analyze_risks()                │
│         .classes[]                    │       │  (PII, critical acts)    │
│         .imports[]                    │       v                         │
│                                       │  run_semantic_analysis()        │
├── patterns/                           │       │  (Claude API, optional) │
│   └── detector.py                     │       v                         │
│       detect_patterns()──────────────▶│  generate_agent_map()           │
│       → PatternResult                 │       │                         │
│         .framework                    │       v                         │
│         .tools[]                      │  agent_map.json                 │
│         .prompts[]                    └─────────────────────────────────┘
│         .memory_systems[]
│
├── risk/
│   └── analyzer.py
│       analyze_risks()
│
├── ai_analyzer/
│   ├── analyzer.py
│   │   run_semantic_analysis()
│   └── prompts.py
│
├── graph/
│   └── builder.py
│       generate_agent_map()
│
├── config/
│   └── framework_signatures.py
│       FRAMEWORK_SIGNATURES            ┌─────────────────────────────────┐
│         langchain                     │        Phase B Internals        │
│         langgraph                     │                                 │
│         openai_native                 │  build_test_configuration()     │
│         anthropic_native              │       │                         │
│         crewai                        │       v                         │
│         autogpt                       │  PersonaBuilder                 │
│                                       │    .load_templates()            │
├── coverage/                           │    .generate_personas()         │
│   ├── models.py                       │    .export_library()            │
│   │   TestConfiguration               │       │                         │
│   │     .coverage_goals               │       v                         │
│   │     .sandbox_config               │  ScenarioLibrary               │
│   └── calculator.py ────────────────▶│    .load_templates()            │
│       build_test_configuration()      │    .generate_variants()         │
│       calculate_coverage_goals()      │    .export_catalog()            │
│       generate_sandbox_config()       │       │                         │
│                                       │       v                         │
├── personas/                           │  TestSuiteGenerator             │
│   ├── models.py                       │    .generate(count)             │
│   │   Persona, PersonaLibrary         │       │                         │
│   ├── builder.py ───────────────────▶│       v                         │
│   │   PersonaBuilder                  │  test_suite.json                │
│   └── templates.py                    └─────────────────────────────────┘
│
├── scenarios/
│   ├── models.py
│   │   Scenario, ScenarioCatalog       ┌─────────────────────────────────┐
│   ├── library.py                      │        Phase C Internals        │
│   │   ScenarioLibrary                 │                                 │
│   └── templates.py                    │  TestExecutionEngine            │
│                                       │    .run_all()  [async]          │
├── generator/                          │       │                         │
│   ├── models.py                       │       │ max_workers semaphore   │
│   │   TestCase, TestSuite             │       │                         │
│   └── test_suite.py ────────────────▶│       ├─── _run_single() ──┐   │
│       TestSuiteGenerator              │       ├─── _run_single()   │   │
│                                       │       ├─── _run_single()   │   │
├── execution/                          │       └─── _run_single()   │   │
│   ├── models.py                       │                            │   │
│   │   TestStatus (enum)               │  ConversationSimulator     │   │
│   │   TestResult                      │    .run_conversation()◀────┘   │
│   │   TestRunReport                   │       │                         │
│   ├── agent_connector.py ───────────▶│       v                         │
│   │   MockAgentConnector              │  AgentConnector                 │
│   │   APIAgentConnector               │    .send_message()              │
│   ├── runner.py                       │       │                         │
│   │   TestExecutionEngine             │  event_queue ──▶ Monitor        │
│   ├── conversation_simulator.py       │       │         (live dashboard)│
│   ├── monitor.py                      │       v                         │
│   │   RealTimeMonitor                 │  ResultsAggregator              │
│   └── aggregator.py                   │    .save_report()               │
│       ResultsAggregator               │    .save_failure_inbox()        │
│                                       └─────────────────────────────────┘
├── diagnosis/
│   ├── models.py
│   │   RootCauseType (enum)            ┌─────────────────────────────────┐
│   │   Severity (enum)                 │        Phase D Internals        │
│   │   FailureCluster                  │                                 │
│   │   FixProposal                     │  DiagnosisEngine.diagnose()     │
│   │   DiagnosisReport                 │       │                         │
│   ├── engine.py ────────────────────▶│       v                         │
│   │   DiagnosisEngine                 │  FailureClusterer               │
│   ├── clustering.py                   │    .cluster_failures()          │
│   │   FailureClusterer                │    (TF-IDF or embeddings)       │
│   ├── root_cause_analyzer.py          │       │                         │
│   │   RootCauseAnalyzer               │       v                         │
│   ├── minimal_reproducer.py           │  RootCauseAnalyzer              │
│   │   MinimalReproducer               │    .analyze() per cluster       │
│   ├── fix_generator.py                │       │                         │
│   │   FixProposalGenerator            │       v                         │
│   ├── priority_ranker.py              │  MinimalReproducer              │
│   │   PriorityRanker                  │    .reproduce() per cluster     │
│   └── retry.py                        │       │                         │
│       RetryConfig                     │       v                         │
│                                       │  FixProposalGenerator           │
└── improvement/                        │    .generate_fixes()            │
    ├── models.py                       │       │                         │
    │   FixStatus (enum)                │       v                         │
    │   AppliedFix                      │  PriorityRanker.rank()          │
    │   ABTestRun                       │       │                         │
    │   RegressionTest                  │       v                         │
    │   ImprovementReport               │  diagnosis_report.json          │
    │   DeploymentPackage               └─────────────────────────────────┘
    ├── engine.py
    │   ImprovementEngine               ┌─────────────────────────────────┐
    ├── fix_applicator.py               │        Phase E Internals        │
    │   FixApplicationEngine            │                                 │
    ├── ab_testing.py                   │  ImprovementEngine.run_async()  │
    │   ABTestingFramework              │       │                         │
    ├── regression_generator.py         │       v                         │
    │   RegressionTestGenerator         │  FixApplicationEngine           │
    ├── validator.py                    │    .apply_fixes(dry_run?)       │
    │   ImprovementValidator            │       │                         │
    └── deployment_packager.py          │       v                         │
        DeploymentPackageBuilder        │  ABTestingFramework             │
                                        │    .run_smoke_test()            │
                                        │    .run_full_test()             │
                                        │       │  (if smoke passes)      │
                                        │       v                         │
                                        │  RegressionTestGenerator        │
                                        │    .generate()                  │
                                        │       │                         │
                                        │       v                         │
                                        │  ImprovementValidator           │
                                        │    .validate()                  │
                                        │       │                         │
                                        │       v  (if ready_to_deploy)   │
                                        │  DeploymentPackageBuilder       │
                                        │    .build()                     │
                                        └─────────────────────────────────┘
```

## 5. Chaining Modes

```
MODE 1: Full Pipeline (run_pipeline.py)
═══════════════════════════════════════════════════════════════════════════

  run_pipeline.py /path/to/agent --mock --skip-ai

  ┌───┐   ┌───┐   ┌───┐   ┌───┐   ┌───┐
  │ A │──▶│ B │──▶│ C │──▶│ D │──▶│ E │    --stop-after controls cutoff
  └───┘   └───┘   └───┘   └───┘   └───┘

  --stop-after a:  A ■
  --stop-after b:  A → B ■
  --stop-after c:  A → B → C ■
  --stop-after d:  A → B → C → D ■
  --stop-after e:  A → B → C → D → E ■  (default)

  --agent-map f:      [skip A] → B → C → D → E
  --test-suite f:     [skip A] → [skip B] → C → D → E
  --agent-map + --test-suite:   C → D → E


MODE 2: Phase C with chaining (execute_tests.py)
═══════════════════════════════════════════════════════════════════════════

  execute_tests.py suite.json map.json --mock

  No flags:              C ■
  --diagnose:            C → D ■
  --improve:             C → D → E ■     (--improve implies --diagnose)
  --improve --apply:     C → D → E ■     (fixes applied for real)


MODE 3: Standalone Phases
═══════════════════════════════════════════════════════════════════════════

  analyze.py repo/                               → agent_map.json
  generate_tests.py agent_map.json               → generated/test_suite.json
  execute_tests.py suite.json map.json           → results/
  diagnose_failures.py inbox.json report.json    → diagnosis_report.json
  improve_agent.py diag.json map.json suite.json → improvement/


MODE 4: Individual B-phase scripts (manual)
═══════════════════════════════════════════════════════════════════════════

  coverage_builder.py  agent_map.json   → test_configuration.json
  persona_builder.py   agent_map.json   → persona_library.json
  scenario_builder.py  agent_map.json   → scenario_catalog.json
  testsuite_builder.py map.json personas.json scenarios.json config.json → test_suite.json
```

## 6. Data Model Relationships

```
                              ┌────────────────────┐
                              │    agent_map.json   │
                              │                     │
                              │  metadata           │
                              │  components.tools[] │
                              │  components.prompts│
                              │  risk_flags         │
                              │  graph              │
                              └──────────┬──────────┘
                                         │
             ┌───────────────────────────┼──────────────────────────┐
             │                           │                          │
             v                           v                          v
    ┌─────────────────┐      ┌────────────────────┐    ┌────────────────────┐
    │  TestConfig      │      │   PersonaLibrary   │    │  ScenarioCatalog   │
    │                  │      │                    │    │                    │
    │  CoverageGoals   │      │   Persona[]        │    │   Scenario[]       │
    │  ├ ToolCoverage  │      │   ├ traits         │    │   ├ category       │
    │  │  min_invoc/   │      │   │  patience 1-10 │    │   ├ difficulty     │
    │  │  tool         │      │   │  clarity 1-10  │    │   ├ type           │
    │  │  combos       │      │   │  tech 1-10     │    │   │  happy_path    │
    │  ├ EdgeCase      │      │   ├ style          │    │   │  error_path    │
    │  │  ambiguous    │      │   │  tone          │    │   │  edge_case     │
    │  │  incomplete   │      │   │  formality     │    │   ├ required_tools │
    │  │  change_mind  │      │   │  typo_rate     │    │   ├ success_cond   │
    │  ├ Stressor      │      │   ├ edge_behaviors │    │   ├ failure_cond   │
    │  │  timeout      │      │   │  rage_quits    │    │   ├ chaos_config   │
    │  │  malformed    │      │   │  changes_mind  │    │   │  timeout_rate  │
    │  │  conflict     │      │   │  off_topic     │    │   │  malformed_rate│
    │  SandboxConfig   │      │   └ messages[]     │    │   │  conflict_rate │
    │  ├ tool_configs  │      └─────────┬──────────┘    │   ├ variant_type   │
    │  ├ cost_limits   │                │               │   └ source         │
    │  └ safety        │                │               └─────────┬──────────┘
    └────────┬─────────┘                │                         │
             │                          │                         │
             └──────────────────────────┼─────────────────────────┘
                                        │
                                        v
                              ┌────────────────────┐
                              │     TestSuite       │
                              │                     │
                              │  TestCase[]         │
                              │  ├ scenario ────────│──▶ Scenario (embedded)
                              │  ├ persona ─────────│──▶ Persona  (embedded)
                              │  ├ coverage_goal    │    tool_coverage
                              │  │                  │    edge_case_coverage
                              │  │                  │    stressor_coverage
                              │  │                  │    scenario_coverage
                              │  ├ target_tool      │
                              │  ├ difficulty       │
                              │  └ exec_config      │
                              │                     │
                              │  TestSuiteSummary   │
                              │  ├ by_difficulty     │
                              │  ├ by_coverage_goal  │
                              │  ├ by_persona       │
                              │  └ tool_invoc_counts │
                              └──────────┬──────────┘
                                         │
                                         v
                              ┌────────────────────┐
                              │    TestResult[]     │
                              │                     │
                              │  test_id            │
                              │  status ────────────│──▶ PASSED|FAILED|ERROR|TIMEOUT
                              │  turns[]            │
                              │  ├ role             │    user | agent
                              │  ├ message          │
                              │  ├ tool_calls[]     │
                              │  └ duration_ms      │
                              │  chaos_events[]     │
                              │  failure_reason     │
                              │  cost_usd           │
                              └──────────┬──────────┘
                                         │
                          ┌──────────────┴──────────────┐
                          v                              v
               ┌──────────────────┐           ┌──────────────────┐
               │  TestRunReport   │           │  FailureInbox    │
               │                  │           │                  │
               │  pass_rate       │           │  total_failures  │
               │  tool_coverage   │           │  failures[]      │
               │  by_difficulty   │           │  ├ test_id       │
               │  by_goal         │           │  ├ scenario      │
               │  cost            │           │  ├ persona       │
               └──────────┬───────┘           │  ├ failure_reason│
                          │                   │  └ trace_file    │
                          └─────────┬─────────┘
                                    │
                                    v
                         ┌────────────────────┐
                         │  DiagnosisReport   │
                         │                    │
                         │  FailureCluster[]  │
                         │  ├ root_cause_type │──▶ prompt_issue
                         │  │                 │   tool_selection_error
                         │  │                 │   hallucination
                         │  │                 │   timeout_handling
                         │  │                 │   service_unavailable
                         │  │                 │   ... (12 types)
                         │  ├ severity ───────│──▶ low|medium|high|critical
                         │  ├ affected_tools  │
                         │  └ reproduction    │
                         │                    │
                         │  FixProposal[]     │
                         │  ├ fix_type ───────│──▶ prompt_patch
                         │  │                 │   code_change
                         │  │                 │   validation_rule
                         │  │                 │   config_change
                         │  ├ changes{}       │
                         │  ├ est_fix_rate    │
                         │  └ effort/risk     │
                         │                    │
                         │  priority_ranking[]│
                         └──────────┬─────────┘
                                    │
                                    v
                   ┌────────────────────────────────┐
                   │       ImprovementEngine         │
                   │                                 │
                   │  AppliedFix[]                   │
                   │  ├ status ──────────────────────│──▶ pending|applied|failed
                   │  ├ before / after / diff        │   |skipped|rolled_back
                   │  └ rollback_instructions        │
                   │                                 │
                   │  ABTestRun[]                    │
                   │  ├ baseline_results             │
                   │  ├ fixed_results                │
                   │  ├ p_value                      │
                   │  └ recommendation ──────────────│──▶ deploy|rollback|need_more_data
                   │                                 │
                   │  ImprovementReport              │
                   │  ├ pass_rate_improvement         │
                   │  ├ ready_to_deploy ─────────────│──▶ bool
                   │  └ deployment_risk ─────────────│──▶ low|medium|high
                   │                                 │
                   │  RegressionTest[]               │
                   │  ├ root_cause                   │
                   │  └ priority                     │
                   │                                 │
                   │  DeploymentPackage (if ready)    │
                   │  ├ version                      │
                   │  ├ changelog                    │
                   │  └ rollback_instructions        │
                   └─────────────────────────────────┘
```

## 7. Enum Reference

```
TestStatus           PENDING | RUNNING | PASSED | FAILED | ERROR | TIMEOUT
FixStatus            PENDING | APPLIED | FAILED | SKIPPED | ROLLED_BACK
Severity             LOW | MEDIUM | HIGH | CRITICAL
Difficulty           easy | medium | hard
ScenarioType         happy_path | error_path | edge_case
CoverageGoal         tool_coverage | edge_case_coverage | stressor_coverage | scenario_coverage
FixType              prompt_patch | code_change | validation_rule | config_change
SandboxMode          mock | real | capture
VariantType          ambiguity | missing_info | interruption | constraint | error
Recommendation       deploy | rollback | need_more_data
DeploymentRisk       low | medium | high
PersonaTone          polite | neutral | frustrated | angry
Formality            formal | casual | slang
EmojiUse             none | rare | moderate | frequent
AbbreviationUse      low | medium | high

RootCauseType        prompt_issue | tool_selection_error | tool_schema_mismatch
                     missing_guardrail | retry_logic_bug | hallucination
                     timeout_handling | error_handling | state_management
                     validation_missing | edge_case_unhandled | service_unavailable

Frameworks           langchain | langgraph | openai_native | anthropic_native
                     crewai | autogpt | custom
```

## 8. File Map

```
debugger-platforn/
├── run_pipeline.py             ◀── Master orchestrator (A→B→C→D→E)
├── generate_tests.py           ◀── Unified Phase B (B1→B2→B3→B4)
├── execute_tests.py            ◀── Phase C (+D +E chaining)
├── analyze.py                  ◀── Phase A standalone
├── coverage_builder.py         ◀── Phase B1 standalone
├── persona_builder.py          ◀── Phase B2 standalone
├── scenario_builder.py         ◀── Phase B3 standalone
├── testsuite_builder.py        ◀── Phase B4 standalone
├── diagnose_failures.py        ◀── Phase D standalone
├── improve_agent.py            ◀── Phase E standalone
├── run_ai_validation.py        ◀── Offline vs AI comparison tool
├── pyproject.toml              ◀── Dependencies & project config
├── README.md                   ◀── Usage documentation
├── ARCHITECTURE.md             ◀── This file
│
├── config/
│   ├── __init__.py
│   └── framework_signatures.py     Framework patterns (langchain, crewai, ...)
│
├── src/
│   ├── __init__.py
│   ├── ingestion/                  Codebase scanning
│   │   └── ingestor.py
│   ├── analysis/                   Tree-sitter AST parsing
│   │   └── static_analyzer.py
│   ├── patterns/                   Framework & tool detection
│   │   └── detector.py
│   ├── risk/                       Risk assessment
│   │   └── analyzer.py
│   ├── ai_analyzer/                Claude-powered semantic analysis
│   │   ├── analyzer.py
│   │   └── prompts.py
│   ├── graph/                      Agent map builder
│   │   └── builder.py
│   ├── coverage/                   Coverage goals & sandbox config
│   │   ├── models.py
│   │   └── calculator.py
│   ├── personas/                   Persona generation
│   │   ├── models.py
│   │   ├── builder.py
│   │   └── templates.py
│   ├── scenarios/                  Scenario generation
│   │   ├── models.py
│   │   ├── library.py
│   │   └── templates.py
│   ├── generator/                  Test suite generation
│   │   ├── models.py
│   │   └── test_suite.py
│   ├── execution/                  Test execution runtime
│   │   ├── models.py
│   │   ├── agent_connector.py
│   │   ├── runner.py
│   │   ├── conversation_simulator.py
│   │   ├── monitor.py
│   │   └── aggregator.py
│   ├── diagnosis/                  Failure analysis
│   │   ├── models.py
│   │   ├── engine.py
│   │   ├── clustering.py
│   │   ├── root_cause_analyzer.py
│   │   ├── minimal_reproducer.py
│   │   ├── fix_generator.py
│   │   ├── priority_ranker.py
│   │   └── retry.py
│   └── improvement/                Improvement & validation
│       ├── models.py
│       ├── engine.py
│       ├── fix_applicator.py
│       ├── ab_testing.py
│       ├── regression_generator.py
│       ├── validator.py
│       └── deployment_packager.py
│
└── tests/
    ├── __init__.py
    ├── test_diagnosis.py           Phase D unit tests (6 tests)
    ├── test_improvement.py         Phase E unit tests (6 tests)
    ├── test_pipeline.py            Pipeline integration tests (3 tests)
    └── sample_agent/               LangChain test agent
        ├── main.py                   AgentExecutor + 4 tools
        └── tools.py                  track_order, search_kb, escalate, refund
```
