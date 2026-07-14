# Sprint 3 — Anonymization Testing & Verification

## Goal
Prove the anonymization pipeline is correct: no PII leaks through, and no useful conversational content is destroyed.

## Tasks

### 3.1 Synthetic PII Test Fixtures
- [ ] Create test conversations (Spanish language) with known planted PII:
  - Person names (Spanish naming conventions: first + two surnames)
  - Phone numbers (Mexican, Spanish, international formats)
  - Email addresses
  - Order/ticket IDs
  - Physical addresses
  - Brand/product terms
- [ ] Store as fixtures in `tests/fixtures/`

### 3.2 PII-Must-Not-Survive Tests
- [ ] For each fixture, run the full pipeline and assert zero PII remains in output
- [ ] Test edge cases: PII embedded mid-sentence, PII split across lines, PII in unusual formats
- [ ] Test that numbered placeholders are consistent (same entity gets same number)

### 3.3 Content-Must-Be-Preserved Tests
- [ ] Assert that non-PII conversational content (greetings, questions, instructions, agent responses) passes through unchanged
- [ ] Assert sentence structure and meaning remain intact
- [ ] Assert conversation turn boundaries are preserved

### 3.4 Brand Scrubbing Tests
- [ ] Load a custom brand dictionary and assert all terms are replaced
- [ ] Assert that partial matches don't over-scrub (e.g., "galaxy" in non-brand context)

### 3.5 Manual Spot-Check Affordance
- [ ] Script that outputs a side-by-side HTML report for N random conversations
- [ ] Checklist template for human reviewer to sign off on a batch
- [ ] Record spot-check results in a log file

### 3.6 Regression Suite
- [ ] Any PII that slips through in spot-checks gets added as a new test case
- [ ] CI-ready: `pytest tests/` runs the full suite

## Done When
- `pytest` passes with zero PII leakage on all synthetic fixtures.
- A human spot-check on a real (small) batch confirms the pipeline works on production-like data.
- The test suite is repeatable and can catch regressions.
