# TechRepair WhatsApp Agent — Reference

## Location

```
/Users/eduardo7/Documents/GitHub/pulpoo-final/connect/cores/tech_repair-next/server/services/agents/whatsapp/
```

## Parent Repository

```
/Users/eduardo7/Documents/GitHub/pulpoo-final/connect/
```

## Key Files

| File | Purpose |
|------|---------|
| `agent.ts` | Main orchestrator (30s timeout, context validation, LangGraph execution) |
| `config.ts` | Zod-validated config (OpenAI, Anthropic, Supabase, GSPN settings) |
| `models.ts` | Type definitions (IntentType, MessageType, ConversationStatus) |
| `graph/builder.ts` | LangGraph state machine builder |
| `graph/state.ts` | Agent state management |
| `graph/nodes/` | Graph nodes: router, status, warranty, pricing, support, escalation |
| `tools/` | Order lookup, warranty tools |
| `prompts/` | System prompts: router, status, support, memory extraction |
| `events/` | Event detection: payment receipts, order received, address changes |
| `post-processors/` | Output style guide enforcement |
| `llm-factory.ts` | LLM instantiation (Claude Haiku/Sonnet, GPT-4o-mini) |
| `lane-selector.ts` | ROCKET multi-lane routing logic |
| `context-summarizer.ts` | Message history summarization |

## Stack

- **Language**: TypeScript
- **Framework**: LangGraph
- **LLMs**: Claude Haiku/Sonnet (Anthropic), GPT-4o-mini (OpenAI)
- **Channel**: WhatsApp (via Pulpoo platform)
- **Domain**: TechRepair customer support (order status, warranty, pricing, escalation)
- **Conversation language**: Spanish

## Sibling Agents (same parent directory)

| Agent | Path | Stack |
|-------|------|-------|
| Inbound voice | `../inbound/` | LiveKit Agents v1.x |
| Outbound voice | `../outbound/` | LiveKit Agents |
| Shared utilities | `../shared/` | Dynamic config, signal detection |

## Analyzer Command

```bash
# WhatsApp agent only
python analyze.py /Users/eduardo7/Documents/GitHub/pulpoo-final/connect/cores/tech_repair-next/server/services/agents/whatsapp/ --skip-ai -o tech_repair_whatsapp_map.json

# All three agents
python analyze.py /Users/eduardo7/Documents/GitHub/pulpoo-final/connect/cores/tech_repair-next/server/services/agents/ --skip-ai -o tech_repair_all_agents_map.json
```
