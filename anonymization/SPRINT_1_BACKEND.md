# Sprint 1 — Anonymization Backend

## Goal
Build the Python anonymization pipeline that takes raw conversation text and strips all PII and brand-confidential terms.

## Tasks

### 1.1 Project Setup
- [ ] Create Python package structure (`anonymization/backend/`)
- [ ] Pin dependencies in `requirements.txt` (FastAPI, spaCy, presidio-analyzer, uvicorn)
- [ ] Create `.env.example` for any config (e.g., spaCy model name)
- [ ] Download spaCy Spanish model (`es_core_news_lg`) for NER on Spanish-language conversations

### 1.2 Pass 1 — Regex PII Removal
- [ ] Phone numbers (international formats, Mexican/Spanish mobile patterns)
- [ ] Email addresses
- [ ] Order IDs / ticket numbers (configurable pattern)
- [ ] Account numbers
- [ ] Physical addresses (street + number patterns)
- [ ] URLs containing user-specific paths
- [ ] Replace each match with a typed placeholder: `[PHONE_1]`, `[EMAIL_1]`, etc. (numbered for traceability)

### 1.3 Pass 2 — NER PII Removal
- [ ] Run spaCy/Presidio NER to catch person names the regex missed
- [ ] Catch location entities that look like personal addresses
- [ ] Replace with `[PERSON_1]`, `[LOCATION_1]`, etc.
- [ ] Handle Spanish-language names and patterns

### 1.4 Brand Generalisation
- [ ] Define a configurable dictionary of brand/product terms to scrub
- [ ] Replace with generic placeholders: `[BRAND]`, `[DEVICE]`, `[PRODUCT]`, `[SERVICE]`
- [ ] Support loading custom term lists from a JSON/YAML config file

### 1.5 FastAPI Endpoint
- [ ] `POST /api/anonymize` — accepts a TXT file upload, returns anonymized text
- [ ] `POST /api/anonymize/preview` — returns both original and anonymized for side-by-side comparison
- [ ] Include metadata in response: count of replacements by category

## Done When
- A raw conversation TXT goes in, and all PII + brand terms come out replaced with typed placeholders.
- The conversational substance (questions, answers, intent) is fully preserved.
- The API is runnable locally with `uvicorn`.
