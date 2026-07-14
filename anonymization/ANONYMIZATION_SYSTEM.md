# Anonymization System — Technical Documentation

## Table of Contents

1. [Overview](#overview)
2. [System Architecture](#system-architecture)
3. [The 3-Pass Anonymization Pipeline](#the-3-pass-anonymization-pipeline)
4. [Pass 1: Regex-Based PII Detection](#pass-1-regex-based-pii-detection)
5. [Pass 2: NER-Based PII Detection](#pass-2-ner-based-pii-detection)
6. [Pass 3: Brand Scrubbing](#pass-3-brand-scrubbing)
7. [Placeholder Tracker](#placeholder-tracker)
8. [Backend API](#backend-api)
9. [Frontend Application](#frontend-application)
10. [Data Flow](#data-flow)
11. [Supported Input Formats](#supported-input-formats)
12. [Entity Types Reference](#entity-types-reference)
13. [Configuration](#configuration)
14. [Testing Infrastructure](#testing-infrastructure)
15. [Architectural Decisions](#architectural-decisions)
16. [Deployment & Operation](#deployment--operation)

---

## Overview

The Anonymization System is a full-stack platform designed to strip **personally identifiable information (PII)** and **brand-confidential terms** from Spanish-language customer-support conversation transcripts. It was built as part of the MSC AI Research Project at Imperial College London, processing real WhatsApp support conversations from Pulpoo for Samsung.

**Key Principles:**

- **Over-anonymization preferred** — false positives (scrubbing non-PII) are acceptable; false negatives (missing PII) are not
- **Stateless processing** — no original text or de-anonymization mappings are stored
- **One-way transformation** — anonymization is irreversible by design (no de-anonymization key)
- **Spanish-first** — patterns, NER models, and test data are optimized for Mexican Spanish

**Technology Stack:**

| Layer | Technology |
|-------|------------|
| Backend | Python 3.10+, FastAPI, uvicorn |
| NLP | spaCy (`es_core_news_lg`), Presidio Analyzer |
| Frontend | React 18, TypeScript, Vite, Tailwind CSS |
| Testing | pytest (50+ test cases) |
| Utilities | jszip (batch downloads), python-dotenv |

---

## System Architecture

### High-Level Architecture Diagram

```
┌──────────────────────────────────────────────────────────────────┐
│                        FRONTEND (React + Vite)                   │
│                        http://localhost:5174                      │
│                                                                  │
│  ┌─────────────┐  ┌──────────┐  ┌─────────────┐  ┌───────────┐ │
│  │ UploadZone  │  │ FileList │  │ ConfigPanel │  │  StatsBar  │ │
│  │ (drag-drop) │  │ (status) │  │ (settings)  │  │  (counts)  │ │
│  └──────┬──────┘  └────┬─────┘  └──────┬──────┘  └─────┬─────┘ │
│         │              │               │                │       │
│         └──────────────┴───────┬───────┘                │       │
│                                │                        │       │
│                          ┌─────┴──────┐          ┌──────┴─────┐ │
│                          │ DiffViewer │          │DownloadBar │ │
│                          │(before/    │          │(txt / zip) │ │
│                          │ after)     │          └────────────┘ │
│                          └────────────┘                         │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                    API Client Layer                        │   │
│  │   previewFile() ──► POST /api/anonymize/preview           │   │
│  │   anonymizeFile() ─► POST /api/anonymize                  │   │
│  └────────────────────────────┬─────────────────────────────┘   │
└───────────────────────────────┼──────────────────────────────────┘
                                │  Vite proxy: /api → :8000
                                ▼
┌──────────────────────────────────────────────────────────────────┐
│                    BACKEND (FastAPI + uvicorn)                    │
│                     http://localhost:8000                         │
│                                                                  │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │                      app.py (FastAPI)                       │ │
│  │                                                             │ │
│  │  POST /api/anonymize ──────► _read_file() ──► anonymize()  │ │
│  │  POST /api/anonymize/preview ► _read_file() ──► anonymize()│ │
│  │  GET  /api/health ──────────► { status: "ok" }             │ │
│  │                                                             │ │
│  │  _read_file()  ──► UTF-8 decode ──► JSON detection         │ │
│  │  _extract_text_from_json() ──► format auto-detection       │ │
│  └────────────────────────────┬───────────────────────────────┘ │
│                               │                                  │
│  ┌────────────────────────────▼───────────────────────────────┐ │
│  │                  pipeline.py (Orchestrator)                 │ │
│  │                                                             │ │
│  │   PlaceholderTracker (shared across all 3 passes)           │ │
│  │           │                                                 │ │
│  │           ├──► Pass 1: regex_anonymize()   [regex_pass.py]  │ │
│  │           ├──► Pass 2: ner_anonymize()     [ner_pass.py]    │ │
│  │           └──► Pass 3: brand_anonymize()   [brand_scrub.py] │ │
│  │                                                             │ │
│  │   Returns: AnonymizationResult                              │ │
│  │     { original_text, anonymized_text, replacement_counts }  │ │
│  └─────────────────────────────────────────────────────────────┘ │
│                                                                  │
│  ┌─────────────────────┐  ┌──────────────────────────────────┐  │
│  │     config.py       │  │      brand_terms.json            │  │
│  │ • PII_PATTERNS      │  │ • brands: [Samsung, Galaxy, …]   │  │
│  │ • CATEGORY_ORDER    │  │ • devices: [Galaxy S24, …]       │  │
│  │ • BRAND_CATEGORY_MAP│  │ • products: [Samsung Care+, …]   │  │
│  │ • PlaceholderTracker│  │ • services: [SmartThings, …]     │  │
│  └─────────────────────┘  └──────────────────────────────────┘  │
│                                                                  │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │                  NLP Engine (Lazy Singleton)                 │ │
│  │                                                             │ │
│  │  spaCy (es_core_news_lg) ──► Presidio AnalyzerEngine       │ │
│  │  Loaded once at startup via lifespan context manager        │ │
│  └─────────────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────────┘
```

### Directory Structure

```
anonymization/
├── backend/
│   ├── app.py                  # FastAPI app, endpoints, file parsing
│   ├── pipeline.py             # 3-pass pipeline orchestrator
│   ├── regex_pass.py           # Pass 1: pattern-based PII detection
│   ├── ner_pass.py             # Pass 2: NER-based entity detection
│   ├── brand_scrub.py          # Pass 3: brand term replacement
│   ├── config.py               # Patterns, constants, PlaceholderTracker
│   ├── brand_terms.json        # Configurable brand/device/product/service terms
│   ├── requirements.txt        # Python dependencies
│   └── .env.example            # Environment variable template
│
├── frontend/
│   ├── src/
│   │   ├── App.tsx             # Main component, state management
│   │   ├── main.tsx            # React entry point
│   │   ├── index.css           # Tailwind CSS styles
│   │   ├── components/
│   │   │   ├── UploadZone.tsx  # Drag-and-drop file upload
│   │   │   ├── FileList.tsx    # File list with status indicators
│   │   │   ├── DiffViewer.tsx  # Side-by-side before/after comparison
│   │   │   ├── StatsBar.tsx    # PII replacement count badges
│   │   │   ├── DownloadBar.tsx # Download single/batch/copy buttons
│   │   │   └── ConfigPanel.tsx # Category toggles + brand term config
│   │   ├── api/
│   │   │   ├── types.ts        # TypeScript interfaces
│   │   │   └── client.ts       # Backend API fetch calls
│   │   └── utils/
│   │       ├── highlights.ts   # Color-coded segment builder
│   │       └── download.ts     # File + ZIP download utilities
│   ├── vite.config.ts          # Vite config with API proxy
│   ├── package.json            # Node dependencies
│   └── tsconfig.json           # TypeScript config
│
├── tests/
│   ├── conftest.py             # pytest fixtures
│   ├── fixtures/
│   │   ├── conversation_with_pii.txt       # Planted PII test data
│   │   ├── conversation_edge_cases.txt     # Edge case scenarios
│   │   └── conversation_no_pii.txt         # Clean text (negative test)
│   ├── test_regex_pass.py              # ~15 regex pattern tests
│   ├── test_ner_pass.py                # ~8 NER tests
│   ├── test_brand_scrub.py             # ~8 brand scrubbing tests
│   ├── test_pipeline_integration.py    # ~13 end-to-end tests
│   └── test_spot_check.py             # HTML report generator
│
├── ANONYMIZATION_SYSTEM.md     # This document
├── README.md                   # User guide + setup
├── CONTEXT.md                  # Project context
├── SPRINT_1_BACKEND.md         # Backend specifications
├── SPRINT_2_FRONTEND.md        # Frontend specifications
└── SPRINT_3_TESTING.md         # Testing specifications
```

---

## The 3-Pass Anonymization Pipeline

The core of the system is a **sequential 3-pass pipeline** where each pass targets a different class of sensitive information. All three passes share a single `PlaceholderTracker` instance, ensuring consistent placeholder numbering and preventing double-anonymization.

```
                    ┌─────────────────────────┐
                    │      Input Text          │
                    │  (raw conversation)      │
                    └───────────┬──────────────┘
                                │
                    ┌───────────▼──────────────┐
                    │   PlaceholderTracker      │
                    │   (shared state)          │
                    └───────────┬──────────────┘
                                │
               ┌────────────────▼────────────────┐
               │  PASS 1: Regex Pattern Matching  │
               │  (regex_pass.py)                 │
               │                                  │
               │  Detects: phones, emails, CURP,  │
               │  RFC, order IDs, account nums,   │
               │  addresses, URLs                 │
               │                                  │
               │  Method: Compiled regex patterns  │
               │  with overlap resolution          │
               └────────────────┬────────────────┘
                                │
               ┌────────────────▼────────────────┐
               │  PASS 2: NER Entity Detection    │
               │  (ner_pass.py)                   │
               │                                  │
               │  Detects: person names,          │
               │  locations                       │
               │                                  │
               │  Method: spaCy es_core_news_lg   │
               │  + Presidio AnalyzerEngine       │
               │  with placeholder avoidance      │
               └────────────────┬────────────────┘
                                │
               ┌────────────────▼────────────────┐
               │  PASS 3: Brand Term Scrubbing    │
               │  (brand_scrub.py)                │
               │                                  │
               │  Detects: brand names, devices,  │
               │  products, services              │
               │                                  │
               │  Method: Dictionary-based with   │
               │  compound term priority           │
               └────────────────┬────────────────┘
                                │
                    ┌───────────▼──────────────┐
                    │   AnonymizationResult     │
                    │  { anonymized_text,       │
                    │    replacement_counts }   │
                    └──────────────────────────┘
```

### Pipeline Orchestrator (`pipeline.py`)

```python
def anonymize(text: str) -> AnonymizationResult:
    tracker = PlaceholderTracker()             # Shared across all passes
    result = regex_anonymize(text, tracker)    # Pass 1
    result = ner_anonymize(result, tracker)    # Pass 2
    result = brand_anonymize(result, tracker)  # Pass 3
    return AnonymizationResult(
        original_text=text,
        anonymized_text=result,
        replacement_counts=tracker.get_summary()
    )
```

---

## Pass 1: Regex-Based PII Detection

**File:** `regex_pass.py`
**Function:** `regex_anonymize(text: str, tracker: PlaceholderTracker) -> str`

This pass uses compiled regular expressions to detect structured PII patterns. It is the first pass because regex patterns are precise and fast, establishing a baseline of protected regions that subsequent passes can skip.

### Processing Order

Patterns are evaluated in a strict order from **most specific to most broad** to minimize false positives:

```
1. CURP            (18-char alphanumeric — very specific)
2. RFC             (13-char alphanumeric — very specific)
3. ORDER_ID        (keyword + pattern — specific)
4. ACCOUNT_NUMBER  (IMEI, CLABE, card numbers — medium specificity)
5. EMAIL           (contains @ — specific)
6. ADDRESS         (street keywords — medium specificity)
7. URL             (http/https — specific)
8. PHONE           (10-digit sequences — MOST BROAD, processed last)
```

### PII Patterns Detected

| Category | Pattern Examples | Placeholder Format |
|----------|------------------|--------------------|
| **PHONE** | `+52 55 1234 5678`, `5512345678`, `+34 612 345 678` | `[PHONE_N]` |
| **EMAIL** | `user@domain.com`, `test+tag@domain.org` | `[EMAIL_N]` |
| **CURP** | `GALO850315HDFRRL09` (Mexican national ID) | `[CURP_N]` |
| **RFC** | `GALO850315AB1` (Mexican tax ID) | `[RFC_N]` |
| **ORDER_ID** | `ORD-2024-78543`, `TKT-001`, `folio MX-99001` | `[ORDER_ID_N]` |
| **ACCOUNT_NUMBER** | IMEI `356938035643809`, CLABE `012...`, card `4521-8834-9912-0045` | `[ACCOUNT_NUMBER_N]` |
| **ADDRESS** | `Calle Reforma 234, Col. Centro, CP 06000` | `[ADDRESS_N]` |
| **URL** | `https://support.example.com/user/123` | `[URL_N]` |

### Key Algorithms

**Match Collection (`_collect_matches`):**
- Iterates through all categories in order
- For each category, runs all associated regex patterns
- Collects tuples: `(start, end, category, matched_text)`

**Overlap Resolution (`_resolve_overlaps`):**
- When two matches overlap in character positions, the **longer match wins**
- Example: if ADDRESS regex matches "Calle Reforma 234, Col. Centro" and PHONE matches "234", the full address is kept

**Right-to-Left Replacement:**
- Matches sorted by start position descending
- Replacements applied from end of string backward
- This preserves character positions for earlier matches

---

## Pass 2: NER-Based PII Detection

**File:** `ner_pass.py`
**Function:** `ner_anonymize(text: str, tracker: PlaceholderTracker, analyzer: AnalyzerEngine) -> str`

This pass uses machine learning (spaCy's Spanish NER model wrapped by Microsoft Presidio) to detect named entities that regex patterns cannot reliably capture — primarily **person names** and **locations**.

### NLP Stack

```
┌──────────────────────────────────┐
│       Presidio AnalyzerEngine    │
│  (orchestration + entity mapping)│
├──────────────────────────────────┤
│       SpacyNlpEngine             │
│  (NLP pipeline wrapper)          │
├──────────────────────────────────┤
│       spaCy es_core_news_lg      │
│  (Spanish large NER model)       │
│  ~560 MB, trained on Spanish     │
│  news corpus                     │
└──────────────────────────────────┘
```

### Entity Mapping

| Presidio Entity | Maps to Category | Placeholder |
|-----------------|------------------|-------------|
| `PERSON` | `PERSON` | `[PERSON_N]` |
| `LOCATION` | `LOCATION` | `[LOCATION_N]` |
| `PHONE_NUMBER` | `PHONE` | `[PHONE_N]` |
| `EMAIL_ADDRESS` | `EMAIL` | `[EMAIL_N]` |
| `NRP` (nationality/religious/political) | `PERSON` | `[PERSON_N]` |

### Key Mechanisms

**1. Lazy Singleton Analyzer:**
```python
_analyzer: AnalyzerEngine | None = None

def get_analyzer() -> AnalyzerEngine:
    global _analyzer
    if _analyzer is None:
        # Load spaCy model + create Presidio engine
        _analyzer = AnalyzerEngine(nlp_engine=..., supported_languages=["es"])
    return _analyzer
```
The model is loaded once at server startup via FastAPI's lifespan context manager, avoiding repeated ~2-3 second load times.

**2. Large Text Chunking (`_split_into_chunks`):**
- spaCy has a maximum text length limit (~1M characters)
- Texts exceeding 500K characters are split at newline boundaries
- Each chunk is analyzed independently
- Results are mapped back to original text offsets by adding chunk start position

**3. Placeholder Avoidance:**
Before running NER, the system scans for existing `[PLACEHOLDER]` tokens from Pass 1:
- Builds a set of character positions that are inside existing placeholders
- Any NER detection overlapping these positions is discarded
- Prevents double-anonymization (e.g., NER detecting "[PHONE_1]" as an entity)

**4. Confidence Threshold:**
- `NER_SCORE_THRESHOLD = 0.4` (40% minimum confidence)
- Detections below this threshold are discarded
- Threshold is intentionally low to favor recall over precision (over-anonymization preference)

---

## Pass 3: Brand Scrubbing

**File:** `brand_scrub.py`
**Function:** `brand_anonymize(text: str, tracker: PlaceholderTracker, brand_terms: dict) -> str`

This pass replaces brand-specific terminology with category placeholders, ensuring that anonymized conversations do not reveal which company or products are being discussed.

### Brand Categories

| JSON Key | Placeholder | Examples |
|----------|-------------|----------|
| `brands` | `[BRAND_N]` | Samsung, Galaxy, Pulpoo |
| `devices` | `[DEVICE_N]` | Galaxy S24, Galaxy S23, Galaxy Tab S9 |
| `products` | `[PRODUCT_N]` | Samsung Care+, Samsung Members |
| `services` | `[SERVICE_N]` | SmartThings, Samsung Pay, Bixby |

### Key Mechanisms

**1. Compound Term Priority:**
All terms from all categories are merged into a single list and **sorted by length descending**. This ensures that multi-word terms are matched before their substrings:
```
"Galaxy S24 Ultra"  →  matched first as [DEVICE_1]
"Galaxy S24"        →  not matched (already consumed)
"Galaxy"            →  not matched (already consumed)
```

**2. Bracket Safety:**
Before replacing a match, the system checks if the match position falls inside an existing `[PLACEHOLDER]`:
- Counts open/close brackets in the text preceding the match
- If the bracket count indicates the match is inside a placeholder, replacement is skipped

**3. Case-Insensitive, Word-Boundary Matching:**
- `re.IGNORECASE` handles "Samsung", "samsung", "SAMSUNG"
- `\b` word boundaries prevent partial matches (e.g., "Galaxying" won't match "Galaxy")
- `re.escape()` handles special characters in terms (e.g., "Care+" is escaped properly)

---

## Placeholder Tracker

**File:** `config.py`
**Class:** `PlaceholderTracker`

The tracker is the central state object shared across all three pipeline passes. It ensures:

1. **Consistent numbering** — the same entity always gets the same placeholder number
2. **Cross-pass awareness** — entities detected in Pass 1 are tracked when Pass 2/3 run
3. **Summary statistics** — category counts for the frontend stats display

### Internal Data Structures

```python
@dataclass
class PlaceholderTracker:
    _counters: dict[str, int]     # {"PHONE": 3, "PERSON": 2, ...}
    _seen: dict[str, str]         # {"PHONE:+52 55 1234 5678": "[PHONE_1]", ...}
```

### Placeholder Assignment Algorithm

```
get_placeholder(category="PHONE", raw_value="+52 55 1234 5678"):
    1. Normalize: "+52 55 1234 5678" → "+52 55 1234 5678" (strip + lowercase)
    2. Build key: "PHONE:+52 55 1234 5678"
    3. Lookup in _seen:
       - If found → return cached placeholder (e.g., "[PHONE_1]")
       - If new   → increment _counters["PHONE"], create "[PHONE_2]", store in _seen
    4. Return placeholder string
```

**Result:** If the phone number `+52 55 1234 5678` appears 5 times in a document, all 5 occurrences become `[PHONE_1]`. A different phone number would become `[PHONE_2]`.

---

## Backend API

**File:** `app.py`

### Endpoints

#### `POST /api/anonymize`

Anonymizes a file and returns only the anonymized result.

**Request:** `multipart/form-data`
- `file` — the file to anonymize (`.txt` or `.json`)
- `config` (optional) — JSON string with anonymization options

**Response:**
```json
{
  "anonymized_text": "Cliente: Hola, mi nombre es [PERSON_1]...",
  "replacement_counts": { "PHONE": 2, "PERSON": 1, "BRAND": 3 },
  "total_replacements": 6
}
```

#### `POST /api/anonymize/preview`

Anonymizes a file and returns both original and anonymized text for side-by-side comparison.

**Request:** Same as `/api/anonymize`

**Response:**
```json
{
  "original_text": "Cliente: Hola, mi nombre es María García...",
  "anonymized_text": "Cliente: Hola, mi nombre es [PERSON_1]...",
  "replacement_counts": { "PHONE": 2, "PERSON": 1, "BRAND": 3 },
  "total_replacements": 6
}
```

#### `GET /api/health`

**Response:** `{ "status": "ok" }`

### File Parsing Logic

The backend auto-detects the input format:

```
Input File
    │
    ├── .txt → Direct text passthrough
    │
    └── .json → Auto-detect structure:
        │
        ├── Array of message objects
        │   [{"role": "cliente", "content": "..."}]
        │
        ├── Object with messages key
        │   {"messages": [...], "conversation": [...],
        │    "turns": [...], "data": [...], "chat": [...]}
        │
        └── Multi-conversation export (Samsung/Supabase)
            {"conversations": [{
              "id": "...",
              "customer_name": "...",
              "messages": [{"text_body": "...", "direction": "inbound"}]
            }]}
```

**Message field detection** looks for:
- **Role fields:** `role`, `sender`, `from`, `direction`
- **Content fields:** `content`, `text`, `message`, `body`, `text_body`

---

## Frontend Application

### Component Architecture

```
┌─────────────────────────────────────────────────────┐
│  App.tsx (State Manager)                            │
│                                                     │
│  State:                                             │
│  • files: FileEntry[]                               │
│  • selectedIndex: number                            │
│  • processing: boolean                              │
│  • config: AnonymizeConfig                          │
│                                                     │
│  ┌───────────────┐  ┌────────────────────────────┐ │
│  │  UploadZone   │  │      ConfigPanel           │ │
│  │  • drag-drop  │  │  • PII category toggles    │ │
│  │  • .txt/.json │  │  • Custom brand terms      │ │
│  │  • multi-file │  │  • Placeholder style       │ │
│  └───────┬───────┘  └────────────┬───────────────┘ │
│          │                       │                   │
│  ┌───────▼───────────────────────▼───────────────┐  │
│  │              FileList                          │  │
│  │  • filename, size, status icon                 │  │
│  │  • ⏳ pending │ ⚙️ processing │ ✅ done │ ❌ err│  │
│  │  • Click to select, X to remove               │  │
│  └───────────────────┬───────────────────────────┘  │
│                      │                               │
│  ┌───────────────────▼───────────────────────────┐  │
│  │              StatsBar                          │  │
│  │  PERSON: 2 │ PHONE: 3 │ EMAIL: 1 │ BRAND: 5  │  │
│  │  (color-coded badges per category)            │  │
│  └───────────────────┬───────────────────────────┘  │
│                      │                               │
│  ┌───────────────────▼───────────────────────────┐  │
│  │              DiffViewer                        │  │
│  │  ┌──────────────┐  ┌──────────────────────┐   │  │
│  │  │   Original   │  │    Anonymized         │   │  │
│  │  │              │  │                       │   │  │
│  │  │  María García│  │  [PERSON_1]           │   │  │
│  │  │  highlighted │  │  highlighted          │   │  │
│  │  │  in color    │  │  in matching color    │   │  │
│  │  └──────────────┘  └──────────────────────┘   │  │
│  │  (synchronized scroll)                        │  │
│  └───────────────────┬───────────────────────────┘  │
│                      │                               │
│  ┌───────────────────▼───────────────────────────┐  │
│  │           DownloadBar                          │  │
│  │  [Download TXT] [Copy to Clipboard] [ZIP All] │  │
│  └───────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────┘
```

### Color-Coded Highlighting

The DiffViewer uses CSS classes to color-code different PII categories:

| Category | CSS Class | Visual Color |
|----------|-----------|-------------|
| PERSON | `bg-hl-name` | Blue |
| PHONE | `bg-hl-phone` | Green |
| EMAIL | `bg-hl-email` | Yellow |
| BRAND / DEVICE / PRODUCT / SERVICE | `bg-hl-brand` | Orange |
| All others | `bg-hl-other` | Purple |

The `buildSegments()` function in `highlights.ts` creates an array of segments where each segment is either plain text or a highlighted replacement:

```typescript
// Input: "Hola, soy [PERSON_1], mi tel es [PHONE_1]"
// Output:
[
  { text: "Hola, soy ",   category: null },
  { text: "[PERSON_1]",   category: "PERSON" },    // → blue highlight
  { text: ", mi tel es ", category: null },
  { text: "[PHONE_1]",    category: "PHONE" },      // → green highlight
]
```

### TypeScript Interfaces

```typescript
interface Replacement {
  original: string      // "María García López"
  placeholder: string   // "[PERSON_1]"
  category: string      // "PERSON"
  start: number         // character offset in original
  end: number           // character offset in original
}

interface AnonymizeResponse {
  anonymized_text: string
  original_text: string
  replacements: Replacement[]
  stats: Record<string, number>
}

interface AnonymizeConfig {
  categories?: string[]          // PII categories to enable
  custom_brand_terms?: string[]  // Additional brand terms
  placeholder_style?: 'numbered' | 'generic'
}

type FileStatus = 'pending' | 'processing' | 'done' | 'error'

interface FileEntry {
  file: File
  status: FileStatus
  error?: string
  result?: AnonymizeResponse
}
```

---

## Data Flow

### Complete Request Lifecycle

```
 User Action                    Frontend                         Backend
 ───────────                    ────────                         ───────

 1. Drag files        ──►  handleFilesAdded()
    onto UploadZone        files[] updated with
                           status: "pending"

 2. Click "Anonymize" ──►  handleAnonymize()
                           loops through pending files
                                    │
                           For each file:
                           status → "processing"
                                    │
                           previewFile(file, config)
                                    │
                           FormData + POST ──────────►  /api/anonymize/preview
                                                               │
                                                        _read_file()
                                                        UTF-8 decode
                                                        JSON auto-detect
                                                               │
                                                        pipeline.anonymize(text)
                                                               │
                                                        ┌──────┴──────┐
                                                        │ Pass 1 Regex│
                                                        │ Pass 2 NER  │
                                                        │ Pass 3 Brand│
                                                        └──────┬──────┘
                                                               │
                                                        AnonymizationResult
                                                               │
                           ◄──────────────────────────  JSON Response
                                    │
                           FileEntry updated:
                           status → "done"
                           result → response data
                                    │
 3. View results      ◄── DiffViewer renders
                           buildSegments() creates
                           color-coded view
                                    │
 4. Download          ──►  downloadFile() or
                           downloadZip()
```

---

## Supported Input Formats

### Plain Text (`.txt`)

```
Cliente: Hola, mi nombre es María García y necesito ayuda.
Agente: Buenos días María, ¿en qué puedo ayudarle?
Cliente: Mi teléfono es 55 1234 5678.
```

### JSON — Message Array

```json
[
  {"role": "cliente", "content": "Hola, mi nombre es María García"},
  {"role": "agente", "content": "Buenos días, ¿en qué puedo ayudarle?"}
]
```

### JSON — Object with Messages Key

```json
{
  "messages": [
    {"sender": "customer", "text": "Mi correo es maria@gmail.com"},
    {"from": "agent", "body": "Gracias, lo verifico"}
  ]
}
```

Supported key names: `messages`, `conversation`, `turns`, `data`, `chat`

### JSON — Multi-Conversation Export (Samsung/Supabase)

```json
{
  "conversations": [
    {
      "id": "conv-001",
      "customer_name": "María García",
      "phone_number": "+52 55 1234 5678",
      "conversation_summary": "Reclamo de garantía...",
      "messages": [
        {"text_body": "Hola necesito ayuda", "direction": "inbound"},
        {"text_body": "Buenos días, en qué...", "direction": "outbound"}
      ]
    }
  ]
}
```

For multi-conversation exports, metadata fields (`customer_name`, `phone_number`, `conversation_summary`) are also included in the anonymization pass to scrub embedded PII.

---

## Entity Types Reference

### Complete Entity Coverage

| Category | Detection Pass | Method | Placeholder | Examples |
|----------|---------------|--------|-------------|----------|
| PHONE | Pass 1 (Regex) + Pass 2 (NER) | Regex patterns + Presidio | `[PHONE_N]` | `+52 55 1234 5678`, `5512345678` |
| EMAIL | Pass 1 (Regex) + Pass 2 (NER) | Regex + Presidio | `[EMAIL_N]` | `user@domain.com` |
| CURP | Pass 1 (Regex) | Mexican national ID pattern | `[CURP_N]` | `GALO850315HDFRRL09` |
| RFC | Pass 1 (Regex) | Mexican tax ID pattern | `[RFC_N]` | `GALO850315AB1` |
| ORDER_ID | Pass 1 (Regex) | Keyword + alphanumeric | `[ORDER_ID_N]` | `ORD-2024-78543`, `folio MX-99001` |
| ACCOUNT_NUMBER | Pass 1 (Regex) | IMEI/CLABE/card patterns | `[ACCOUNT_NUMBER_N]` | `356938035643809` |
| ADDRESS | Pass 1 (Regex) | Street keyword patterns | `[ADDRESS_N]` | `Calle Reforma 234, Col. Centro` |
| URL | Pass 1 (Regex) | HTTP/HTTPS patterns | `[URL_N]` | `https://support.example.com/...` |
| PERSON | Pass 2 (NER) | spaCy NER model | `[PERSON_N]` | `María García López` |
| LOCATION | Pass 2 (NER) | spaCy NER model | `[LOCATION_N]` | `Guadalajara`, `Jalisco` |
| BRAND | Pass 3 (Brand) | Dictionary lookup | `[BRAND_N]` | `Samsung`, `Pulpoo` |
| DEVICE | Pass 3 (Brand) | Dictionary lookup | `[DEVICE_N]` | `Galaxy S24`, `Galaxy Tab S9` |
| PRODUCT | Pass 3 (Brand) | Dictionary lookup | `[PRODUCT_N]` | `Samsung Care+` |
| SERVICE | Pass 3 (Brand) | Dictionary lookup | `[SERVICE_N]` | `SmartThings`, `Bixby` |

### What Is NOT Anonymized

- Generic words: "dispositivo", "garantía", "revisión"
- Conversation structure: "Cliente:" and "Agente:" turn labels
- Conversational semantics and intent
- Common abbreviations: "Sr.", "Dra."
- Numbers that don't match PII patterns (e.g., "2 días", "paso 3")

---

## Configuration

### Backend Environment Variables (`.env`)

```bash
SPACY_MODEL=es_core_news_lg      # spaCy model for NER (default: es_core_news_lg)
BRAND_CONFIG_PATH=brand_terms.json # Path to brand terms file
LOG_LEVEL=INFO                     # Logging verbosity
```

### Brand Terms (`brand_terms.json`)

```json
{
  "brands": ["Samsung", "Galaxy", "Pulpoo"],
  "devices": ["Galaxy S24", "Galaxy S23", "Galaxy A15", "Galaxy Tab S9"],
  "products": ["Samsung Care+", "Samsung Members"],
  "services": ["SmartThings", "Samsung Pay", "Bixby"]
}
```

To add new brand terms, simply edit this file and restart the backend. Terms are loaded at startup via `config.load_brand_terms()`.

### Frontend Configuration Panel

The UI provides runtime configuration options:

| Option | Description | Default |
|--------|-------------|---------|
| PII Categories | Checkboxes to enable/disable 8 PII types | All enabled |
| Custom Brand Terms | Comma-separated additional brand terms | Empty |
| Placeholder Style | `numbered` (`[PHONE_1]`) vs `generic` (`[PHONE]`) | Numbered |

### Vite Proxy (`vite.config.ts`)

```typescript
server: {
  port: 5174,
  proxy: {
    '/api': {
      target: 'http://localhost:8000',
      changeOrigin: true
    }
  }
}
```

### CORS Configuration

```python
CORSMiddleware(
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"]
)
```

---

## Testing Infrastructure

### Test Suite Summary

| Test File | Tests | Focus | Requires spaCy |
|-----------|-------|-------|-----------------|
| `test_regex_pass.py` | ~15 | Pattern matching for all 8 regex categories | No |
| `test_ner_pass.py` | ~8 | Person/location detection, placeholder avoidance | Yes |
| `test_brand_scrub.py` | ~8 | Brand/device/product/service replacement | No |
| `test_pipeline_integration.py` | ~13 | Full 3-pass pipeline, content preservation | Yes |
| `test_spot_check.py` | 1 | HTML report generator for manual review | Yes |
| **Total** | **~50+** | **Comprehensive coverage** | |

### Test Fixtures

**`conversation_with_pii.txt`** — Realistic conversation with 14+ planted PII items including names, phones, emails, order IDs, addresses, account numbers, CURP, RFC, URLs, and brand terms.

**`conversation_edge_cases.txt`** — Challenging scenarios: Spanish full names with nicknames (José Antonio → Toño), multiple phone numbers per person, corporate + personal emails, complex addresses with department numbers, duplicate order IDs, IMEI numbers.

**`conversation_no_pii.txt`** — Clean conversation with zero PII. Used to verify the system produces **no false positives** on clean input.

### Key Test Assertions

**PII Removal (test_pipeline_integration.py):**
- All 14 planted PII items must NOT appear in output
- No raw 10+ digit number sequences remain
- No email patterns survive
- All edge case PII removed

**Content Preservation (test_pipeline_integration.py):**
- 8 key conversational phrases preserved ("Hola", "necesito ayuda", etc.)
- Turn count for "Cliente:" and "Agente:" matches original
- Clean text passes through with zero placeholders

**Placeholder Format:**
- All placeholders match `[CATEGORY_N]` pattern
- Per-category numbering starts at 1 with no gaps
- Same entity → same placeholder number

### Spot Check Report (`test_spot_check.py`)

Generates an HTML report at `tests/spot_check_report.html` with:
- Two-column before/after view for each test fixture
- Yellow highlighting on all placeholders
- Manual review checklist:
  - No person names remaining
  - No phone numbers remaining
  - No email addresses remaining
  - No account/order numbers remaining
  - No brand names remaining
  - Conversational meaning preserved
  - Turn structure intact

### Running Tests

```bash
# All tests
pytest tests/ -v

# Individual test suites
pytest tests/test_regex_pass.py -v       # Fast (no spaCy)
pytest tests/test_ner_pass.py -v         # Requires spaCy model
pytest tests/test_brand_scrub.py -v      # Fast (no spaCy)
pytest tests/test_pipeline_integration.py -v  # Full pipeline
pytest tests/test_spot_check.py -v       # Generate HTML report
```

---

## Architectural Decisions

| Decision | Rationale |
|----------|-----------|
| **3-pass sequential pipeline** | Each pass targets a different detection method (regex → ML → dictionary). Sequential ordering allows later passes to skip regions already anonymized. |
| **Shared PlaceholderTracker** | Ensures consistent placeholder numbering across all passes and prevents double-anonymization. |
| **Right-to-left replacement** | Replacing from the end of the string backward preserves character positions for earlier matches, eliminating offset recalculation. |
| **Lazy NER model loading** | The spaCy model (~560 MB) is loaded once at startup and cached. Avoids per-request loading overhead of 2-3 seconds. |
| **Chunked NER processing** | Handles texts exceeding spaCy's maximum length by splitting at newline boundaries and mapping results back to original offsets. |
| **Specific → broad pattern ordering** | Processing CURP/RFC before PHONE prevents a 10-digit substring of a CURP from being matched as a phone number. |
| **Over-anonymization philosophy** | False positives are acceptable; false negatives are not. A wrongly anonymized word is recoverable; leaked PII is not. |
| **No database / stateless** | No original text or de-anonymization mappings are stored. Maximizes privacy by design — nothing to leak. |
| **No LLMs for anonymization** | Purely NER + regex. Deterministic, reproducible, no hallucination risk, no API costs, works offline. |
| **JSON format auto-detection** | Supports multiple JSON structures without requiring user configuration. Reduces friction for different data sources. |
| **Frontend/backend separation** | API-driven architecture enables independent development, testing, and potential future scaling. |

---

## Deployment & Operation

### Starting the System

**Backend:**
```bash
cd anonymization/backend
source venv/bin/activate
python -m uvicorn app:app --reload --port 8000
```

**Frontend:**
```bash
cd anonymization/frontend
npm run dev
```

The application is then available at `http://localhost:5174`.

### Startup Sequence

1. FastAPI app initializes
2. Lifespan context manager calls `get_analyzer()`
3. spaCy `es_core_news_lg` model loads (~2-3 seconds)
4. Presidio AnalyzerEngine wraps spaCy model
5. Server ready for requests

### Performance Characteristics

| Scenario | Expected Latency |
|----------|-----------------|
| First request after startup | ~2-3s (model warm-up) |
| Typical conversation (500-2000 chars) | <1s |
| Large text (50KB+) | 1-5s (NER chunking) |
| Regex-only pass | <100ms |
| Brand scrub pass | <100ms |

### Limitations

- **Single concurrent request**: spaCy operations are synchronous. One request is processed at a time per backend instance.
- **Spanish only**: NER model and regex patterns are optimized for Mexican Spanish. Other languages would require different models and patterns.
- **Irreversible**: No de-anonymization capability. Original text can only be recovered if the user retains the original file.
- **Nickname detection**: Standalone nicknames (e.g., "Toño" for "José Antonio") may not be detected by NER if they appear without full name context.
