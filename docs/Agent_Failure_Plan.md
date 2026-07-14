# Samsung Agent Failure Analysis System — Plan

## Context

We have **1,299 historical WhatsApp conversations** (24,537 messages) between Samsung customers and our AI agent stored in Supabase. The agent handles service order inquiries, delivery logistics, pricing, and general support for Samsung Polanco's repair center.

The goal is to build a system that identifies every situation where the agent failed, classifies the failure type, and produces actionable insights to improve the agent's prompt, tools, and graph logic.

---

## Current Data Landscape

### What we have per conversation

| Field | Usefulness |
|-------|-----------|
| `status` | `escalated` / `closed` / `expired` / `active` — escalated = explicit failure |
| `escalation_reason` | Free-text reason why the agent escalated |
| `is_human_handling` | Whether a moderator took over |
| `taken_over_at` / `taken_over_by_user_id` | When and who took over |
| `conversation_summary` | AI-generated summary (only 3 conversations have this — mostly empty) |
| `current_graph_node` | Last LangGraph node the conversation was in |
| `tags` | Rarely used (only 6 tagged conversations) |
| `message_count` | Total messages — high counts signal loops |
| `active_service_order_id` | Whether a GSPN order was linked |

### What we have per message

| Field | Usefulness |
|-------|-----------|
| `source` | `customer` / `ai_agent` / `human_agent` / `system` |
| `ai_intent_detected` | What the agent thought the customer meant |
| `ai_confidence_score` | How confident the agent was (0-1) |
| `ai_tool_calls` | Tools the agent invoked (all logged as "unknown" name — needs fix) |
| `status` | `delivered` / `read` / `failed` — failed = message never reached customer |
| `error_code` / `error_message` | Why delivery failed |
| `graph_node` | Which LangGraph node processed this message |
| `text_body` | The actual message content |

### Current numbers (snapshot from 2026-06-28 export)

| Metric | Value |
|--------|-------|
| Total conversations | 1,299 |
| Total messages | 24,537 |
| Avg messages/conversation | 18.9 |
| Escalated conversations | 291 (22.4%) |
| "Hablar con agente" escalations | 219 (75% of escalations) |
| Incomplete GSPN data escalations | 48 |
| Conversations with unknown intent | 297 |
| Low confidence messages (<0.5) | 178 |
| Customer repeated themselves | 376 times |
| Long conversations (>40 msgs) | 287 |
| Failed message delivery | 239 |
| Frustration detected | 16 conversations |
| Human takeovers | 39 |

### Message source breakdown

| Source | Count | % |
|--------|-------|---|
| Customer | 11,696 | 47.7% |
| AI agent | 8,133 | 33.1% |
| Human agent | 2,303 | 9.4% |
| Templates | 2,405 | 9.8% |

### AI response times

| Percentile | Seconds |
|------------|---------|
| p50 | 3.4s |
| p90 | 6.1s |
| p99 | 13.5s |
| max | 32.7s |

---

## Failure Taxonomy

Every failed conversation should be classified into one or more of these categories:

### 1. Comprehension Failure

The agent did not understand what the customer was asking.

**Signals:**
- `ai_intent_detected = "unknown"` (545 messages across 297 conversations)
- `ai_confidence_score < 0.5` (178 messages)
- Customer repeats the same message (376 occurrences)
- Customer rephrases immediately after an AI response

**What to look for in the transcript:**
- Agent responds to the wrong topic
- Agent gives a generic "how can I help you" after the customer already stated their need
- Agent asks for information the customer already provided

### 2. Resolution Failure

The agent understood the intent but could not resolve the issue. The customer gave up and asked for a human.

**Signals:**
- `escalation_reason` contains "hablar con un agente" (219 conversations)
- `escalation_reason` contains "explicit_human_request"
- Customer sends messages like "agente", "hablar con alguien", "persona real"

**What to look for in the transcript:**
- Agent gives correct but insufficient information
- Agent loops through the same responses without progressing
- Agent cannot perform an action the customer needs (e.g., reschedule, cancel)

### 3. Data Gap Failure

The agent had the right logic but the underlying data (GSPN, order system) was incomplete or unavailable.

**Signals:**
- `escalation_reason` contains "sin datos completos" (48 conversations)
- `escalation_reason` mentions warranty or cost data missing
- Tool calls that return empty/null results

**What to look for in the transcript:**
- Agent says "no encontré información" or similar
- Agent escalates immediately after a tool call
- Customer provides a valid order number but agent can't find it

### 4. Loop / Stall Failure

The conversation went in circles without making progress. The agent kept asking the same questions or giving the same answers.

**Signals:**
- `message_count > 40` (287 conversations)
- Repeated AI responses with similar content
- Conversation lasted many days without resolution
- Same `graph_node` appears in consecutive messages

**What to look for in the transcript:**
- Agent asks for the order number multiple times
- Agent repeats the same status update
- Conversation oscillates between two graph nodes

### 5. Delivery / Infrastructure Failure

The message never reached the customer due to WhatsApp API issues.

**Signals:**
- `status = "failed"` (239 messages)
- `error_code = "131026"` (message undeliverable — 237 of 239)
- `error_code = "131049"` (rate limit)
- `error_code = "130472"` (media error)

**What to look for:**
- Customer's WhatsApp window expired (24h rule) but agent tried to send
- Phone number format issues
- Multiple failed messages in a row

### 6. Missed Escalation

The customer expressed frustration, confusion, or explicitly asked for help, but the agent did not escalate or change behavior.

**Signals:**
- `ai_intent_detected = "complaint_or_frustration"` (17 messages across 16 conversations)
- Conversations with frustration intent that were NOT escalated
- Customer uses strong negative language without triggering escalation

**What to look for in the transcript:**
- Customer says something angry and agent responds cheerfully
- Multiple frustration signals before escalation finally happens
- Customer threatens to complain on social media / regulatory bodies

### 7. Silent Abandonment

The customer stopped responding without resolution. No escalation, no closure — the conversation just died.

**Signals:**
- `status = "expired"` (188 conversations)
- Last message is from `ai_agent` with no customer reply
- Conversation has < 5 messages total
- No escalation reason, not closed as resolved

**What to look for:**
- Agent's last message was unhelpful or confusing
- Agent asked a question the customer didn't know how to answer
- Agent sent information but customer may not have understood it

### 8. Hallucination / Wrong Information

The agent provided incorrect information (wrong price, wrong status, wrong process).

**Signals:**
- No direct structured signal — requires transcript analysis
- Conversations where human agent contradicts the AI agent's prior message
- Conversations where customer pushes back ("that's not what they told me", "eso no es correcto")

**What to look for in the transcript:**
- AI gives a price or timeline that the human agent later corrects
- AI describes a process that doesn't exist
- AI confuses one service order with another

---

## Analysis Pipeline

### Phase 1: Structured Signal Scoring (automated)

Score every conversation using available structured data. No LLM needed.

**Input:** Raw conversation + messages from Supabase.

**Failure score formula:**

```
score = 0
if (escalated)                          score += 3
if (customer requested human)           score += 5
if (has unknown intents)                score += 2 * (unknown_count / total_ai_msgs)
if (min confidence < 0.5)              score += 2 * (1 - min_confidence)
if (customer repeated messages)         score += 1 * repeat_count
if (message_count > 40)                score += 2
if (has failed deliveries)             score += 1
if (frustration detected)              score += 3
if (expired without resolution)        score += 2
if (human took over)                   score += 4
```

**Output:** Each conversation gets a `failure_score` (0 = likely fine, 10+ = definitely failed) and a list of triggered failure categories.

Sort all conversations by score descending. The top ones are the worst failures.

### Phase 2: LLM Classification (semi-automated)

Take the top ~200 highest-scored conversations and pass each transcript to Claude with a classification prompt.

**What the LLM should evaluate per conversation:**

1. **Did the agent fail?** (yes/no/partial)
2. **Failure categories** (from the taxonomy above — can be multiple)
3. **Root cause** — what specifically went wrong (free text, 1-2 sentences)
4. **Severity** — minor (customer inconvenienced), major (customer unserved), critical (wrong information given)
5. **Fixable by prompt change?** — yes / needs tool change / needs data fix / needs graph restructure
6. **Key quote** — the specific exchange where the failure happened

**The LLM prompt should include:**
- The full message history (text_body, source, direction, timestamp)
- The conversation metadata (status, escalation reason, tags)
- Instructions to be critical — look for subtle failures, not just obvious ones
- The failure taxonomy definitions for consistent labeling

**Important:** The LLM should NOT be asked to score or rank — it should only classify. Ranking comes from Phase 1 scores combined with Phase 2 severity.

### Phase 3: Pattern Aggregation

Group Phase 2 results by:

1. **Failure category** — which types are most common?
2. **Customer intent** — which intents have the worst success rate?
3. **Graph node** — which part of the agent flow produces the most failures?
4. **Time period** — are failures increasing or decreasing over time?
5. **Root cause cluster** — group similar root causes (e.g., "GSPN timeout", "wrong warranty logic", "can't handle Spanish slang")

This produces a prioritized list of agent improvements.

---

## Concrete Outputs

### Output 1: Failure Report

A summary document with:

- Total failure rate (% of conversations with score > X)
- Breakdown by failure category
- Top 10 worst conversations with links/IDs
- Trend over time (weekly or monthly)

### Output 2: Root Cause List

A ranked list of specific, actionable root causes:

```
Example:
1. GSPN missing cost data (48 escalations) → Add fallback: "cost pending, call for details"
2. Agent can't handle "quiero hablar con alguien" variations (219 escalations) → Improve intent detection for human request
3. Agent loops on order status when GSPN returns stale data (est. ~30 conversations) → Add staleness check + different response path
```

### Output 3: Golden Test Dataset

The 50-100 most informative failure conversations, each annotated with:

- **Input:** customer message sequence
- **Expected behavior:** what the agent should have done
- **Actual behavior:** what it did
- **Category:** failure type

This becomes the regression test suite. Every prompt or tool change should be tested against these cases before deployment. This can feed into the existing Langfuse auto-regression system.

### Output 4: Improved Instrumentation Recommendations

Based on gaps found in the data:

- **Tool call names are all "unknown"** — fix the logging so `ai_tool_calls` records the actual tool name and arguments. Without this, we can't tell which tools fail.
- **Only 3 conversations have summaries** — if `conversation_summary` were populated consistently, Phase 2 LLM analysis could be cheaper (summarize first, classify from summary).
- **Tags are almost unused** (6 conversations) — either remove the field or start using it for manual labeling.
- **`graph_node` on messages is mostly null** — instrumenting which LangGraph node processed each message would make Phase 3 graph-level analysis possible.

---

## Priority Order

1. **Fix tool call logging** — without knowing which tools are called, we're blind to a whole class of failures.
2. **Run Phase 1 scoring** on the full export — this is cheap (pure computation, no LLM) and immediately surfaces the worst conversations.
3. **Run Phase 2 classification** on the top 200 scored conversations — this requires LLM cost but produces the root cause list.
4. **Build the golden test dataset** from Phase 2 results — this has compounding value over time.
5. **Build the dashboard** — only after we have the data pipeline producing results.

---

## Data Sources

- **Primary:** `whatsapp_conversations` and `whatsapp_messages` tables in Supabase (Samsung project: `jfiezisbitkmamirxopq`)
- **Export script:** `connect/cores/samsung-next/scripts/extract-conversations.ts` — extracts all conversations + messages to a local JSON file
- **Export location:** `connect/cores/samsung-next/samsung-conversations-export.json` (34MB, gitignored)
- **Existing evaluation infra:** Langfuse auto-regression system (see `server/services/evaluation/auto-regression.ts`)
