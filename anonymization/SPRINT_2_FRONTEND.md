# Sprint 2 — Anonymization Frontend

## Goal
Build a simple React web UI where a user uploads conversation TXT files and gets back the anonymized version with a visual before/after comparison.

## Tasks

### 2.1 Project Setup
- [ ] Initialize React + TypeScript + Vite project (`anonymization/frontend/`)
- [ ] Install Tailwind CSS for styling
- [ ] Configure proxy to backend API (default `http://localhost:8000`)

### 2.2 Upload Interface
- [ ] Drag-and-drop zone for TXT file upload
- [ ] Support multiple file upload (batch anonymization)
- [ ] Show file name, size, and upload status
- [ ] "Anonymize" button to trigger processing

### 2.3 Before/After View
- [ ] Side-by-side panel: original text (left) vs anonymized text (right)
- [ ] Highlight replacements in the anonymized text (color-coded by type: names, phones, emails, brands)
- [ ] Show replacement statistics (e.g., "3 names, 2 phones, 1 brand term removed")

### 2.4 Download
- [ ] "Download Anonymized" button — downloads the clean TXT
- [ ] Option to download all files as a ZIP if batch upload was used
- [ ] Copy-to-clipboard for quick use

### 2.5 Configuration Panel (optional, nice-to-have)
- [ ] Toggle which PII categories to anonymize
- [ ] Add custom brand terms to scrub on-the-fly
- [ ] Choose placeholder style (numbered vs generic)

## Done When
- User can upload a TXT, see the before/after diff with highlights, and download the anonymized result.
- The UI is clean, responsive, and works locally against the backend from Sprint 1.
