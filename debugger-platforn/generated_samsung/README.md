# Phase B output — Samsung WhatsApp agent

Generated 2026-07-23 against `samsung_whatsapp_map.json` (agent_id
`54ccc1bc-dd4c-4c68-b2d0-64af4568220d`), for execution against the
`samsung-live-agent` simulation (see `../agent_endpoints.json`).

```bash
python generate_tests.py samsung_whatsapp_map.json -o generated_samsung \
    --count 40 --seed 42 -l Spanish --evaluate
```

Run stats: 863,010 tokens, ~$2.68, ~3h.

| File | Contents |
|---|---|
| `test_suite.json` | 40 executable test cases (persona + scenario + oracles) |
| `persona_library.json` | AI-generated Spanish personas (MAP-Elites) |
| `scenario_catalog.json.gz` | full catalog, 1,480 scenarios incl. variants + oracles (95MB raw — stored gzipped; `gunzip -k` to restore) |
| `test_configuration.json` | Phase B run configuration |
| `evaluation_report.json` | suite-quality harness results |

Suite quality (evaluation harness): APFD 0.9168 (weighted 0.9202),
214 potential faults, overall diversity 0.3112, tool-pair coverage 0.3279,
taxonomy coverage 0.6875, 194 mutants.

Note: `debugger-platforn/.gitignore` ignores `*.json` — these files are
force-added; use `git add -f` when regenerating.

Execute against the live agent:

```bash
cd ../samsung-live-agent && bun run api   # terminal 1
python execute_tests.py generated_samsung/test_suite.json samsung_whatsapp_map.json --count 10 -o results   # terminal 2
```
