# Anonymization Platform — Context

## What This Is

A standalone anonymization platform that takes raw customer-support conversation transcripts (TXT files) and automatically strips all personally identifiable information (PII) and brand-confidential terms, producing clean anonymized output ready for research use.

## Why It Exists

This platform is part of an MSC AI research project at Imperial College London. The research requires analysis of real production conversations from a Spanish-language WhatsApp customer support agent (operated by Pulpoo for TechRepair). Before any analysis can happen, conversations must be fully anonymized to:

1. Comply with ethics requirements (Imperial ethics board submission)
2. Remove all customer PII (names, phones, emails, addresses, account numbers)
3. Scrub brand-confidential information (product names, internal codes)
4. Preserve the conversational substance needed for failure analysis research

## The Data

- **Source**: Production WhatsApp support conversations in Spanish
- **Format**: TXT files containing multi-turn conversations between customers and an AI agent
- **Volume**: Potentially hundreds or thousands of conversations
- **Language**: Primarily Spanish (Mexican Spanish)
- **Content**: Customer queries about devices, orders, complaints, troubleshooting

## What the Platform Does

### Two-Pass Anonymization Pipeline

**Pass 1 — Regex PII**: Pattern-based detection and replacement of:
- Phone numbers (Mexican, international formats)
- Email addresses
- Order IDs / ticket numbers
- Account numbers
- Physical addresses
- URLs with user-specific paths

**Pass 2 — NER PII**: Named Entity Recognition (spaCy/Presidio) to catch:
- Person names (Spanish naming conventions)
- Location entities that represent personal addresses
- Any PII the regex pass missed

**Brand Generalization**: Replace brand/product terms with generic placeholders:
- Brand names → `[BRAND]`
- Device/product names → `[DEVICE]`
- Internal service names → `[SERVICE]`

### Output

Each piece of PII is replaced with a typed, numbered placeholder (e.g., `[PHONE_1]`, `[PERSON_2]`) so:
- The conversation remains readable and structurally intact
- You can tell that two mentions refer to the same entity
- No real data leaks

## Architecture

```
anonymization/
├── backend/          # Python (FastAPI)
│   ├── app.py        # FastAPI application + endpoints
│   ├── pipeline.py   # Orchestrates the full anonymization flow
│   ├── regex_pass.py # Pass 1: pattern-based PII detection
│   ├── ner_pass.py   # Pass 2: NER-based PII detection
│   ├── brand_scrub.py# Brand term replacement
│   └── config.py     # Configurable patterns, brand dictionaries
│
├── frontend/         # React + TypeScript + Vite + Tailwind
│   └── src/
│       ├── App.tsx           # Upload UI
│       ├── components/       # Upload zone, before/after viewer, download
│       └── api/              # Client calls to backend
│
└── tests/            # pytest
    ├── fixtures/     # Synthetic conversations with planted PII
    └── test_*.py     # PII-must-not-survive + content-must-be-preserved
```

## Tech Stack

| Layer | Technology |
|-------|------------|
| Backend | Python 3.10+, FastAPI, spaCy (es_core_news_lg), Presidio, uvicorn |
| Frontend | React 18, TypeScript, Vite, Tailwind CSS |
| Testing | pytest |
| Language model | spaCy Spanish NER (no LLM needed for anonymization itself) |

## Key Constraints

1. **Spanish language** — NER model must handle Spanish names, addresses, and patterns
2. **No false negatives** — PII must NOT leak through. Over-anonymizing is preferable to under-anonymizing.
3. **Preserve signal** — The conversational content (intent, questions, agent responses, tool usage context) must remain intact for downstream research analysis
4. **Configurable** — Brand terms and regex patterns should be easy to update via config files
5. **Human verification** — Must support side-by-side before/after view for manual spot-checking

## How to Use This Document

Feed this file plus the relevant sprint file into Claude to get implementation started:

- `CONTEXT.md` + `SPRINT_1_BACKEND.md` → Build the Python anonymization pipeline
- `CONTEXT.md` + `SPRINT_2_FRONTEND.md` → Build the React upload UI
- `CONTEXT.md` + `SPRINT_3_TESTING.md` → Build the test suite
