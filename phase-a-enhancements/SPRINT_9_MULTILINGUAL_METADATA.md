# Sprint 9 — Multilingual/Domain Metadata Fields

## Goal

Add structured multilingual and domain metadata to the Agent Map so Phase B can generate **Spanish-native adversarial prompts**, **code-switching attacks**, and **policy-adherence scenarios in the deployment language**. Multiple studies (MrGuard, arXiv 2504.15241; SEALGuard, arXiv 2507.08898) show safety guardrails degrade outside English, with jailbreak success rising as language resource level falls.

**Can run in parallel with**: Any other sprint — this is a small, isolated change touching only `src/graph/builder.py` and `config/framework_signatures.py`.

## Why This Matters for Phase B

The target agent is a **Spanish-language Samsung WhatsApp support agent**. Without explicit language metadata:
- Phase B generates English adversarial prompts by default → misses Spanish-specific jailbreaks
- Code-switching attacks (mixing Spanish + English mid-conversation) aren't generated
- The mismatch between guardrail language and conversation language isn't flagged

## Current State

`src/graph/builder.py` line 24: `_detect_conversation_language(prompts)` exists but only returns `"Spanish"` or `"English"` (binary). It checks for 30 Spanish words and Spanish special characters with a threshold of ≥ 3 matches.

The Agent Map currently has:
- `metadata.conversation_language`: `"Spanish"` or `"English"` — that's it

## Tasks

### 9.1 Expand Language Detection

**File**: `src/graph/builder.py`

- [ ] Expand `_detect_conversation_language()` to return a richer structure:
  ```python
  def _detect_language_metadata(prompts, guardrail_rules=None) -> dict:
      return {
          "conversation_languages": ["Spanish", "English"],    # can be multilingual
          "primary_language": "Spanish",                       # most frequent
          "guardrail_language": "Spanish",                     # language the rules/policies are written in
          "language_mismatch": False,                           # True if guardrails != conversation
          "code_switching_detected": True,                      # True if prompts mix languages
          "spanish_formality": "usted",                        # "tú" | "usted" | "mixed" (relevant for Mexican Spanish)
          "confidence": 0.92
      }
  ```

- [ ] Add Portuguese detection (existing anonymization platform handles Portuguese too):
  - Portuguese words: `obrigado`, `bom dia`, `serviço`, `cliente`, `atendimento`, `consulta`, `agendamento`
  - Portuguese chars: `ã`, `õ`, `ç`

- [ ] Detect code-switching: if both Spanish AND English indicators score ≥ 2, flag `code_switching_detected: True`

### 9.2 Add Domain Metadata

**File**: `src/graph/builder.py`

- [ ] Add `domain` section to Agent Map metadata:
  ```json
  "domain": {
      "type": "customer_support",
      "industry": "consumer_electronics",
      "channel": "whatsapp",
      "brand": null,
      "detected_from": "tool_names_and_prompts"
  }
  ```

- [ ] Detection heuristic — scan tool names and prompt content for:
  - `"customer_support"`: keywords `support`, `ticket`, `complaint`, `helpdesk`, `soporte`, `queja`
  - `"sales"`: keywords `order`, `purchase`, `price`, `product`, `pedido`, `compra`
  - `"scheduling"`: keywords `appointment`, `booking`, `schedule`, `calendar`, `cita`, `reserva`
  - `"whatsapp"`: keywords `whatsapp`, `wa`, `message`, `chat`
  - `"consumer_electronics"`: keywords `device`, `phone`, `laptop`, `warranty`, `dispositivo`, `garantía`

### 9.3 Add Formality Detection (Spanish)

- [ ] Detect Spanish formality level from prompts:
  - `"usted"` form: keywords `usted`, `estimado`, `le informamos`, `sírvase`
  - `"tú"` form: keywords `tú`, `te`, `quieres`, `puedes`
  - `"mixed"`: both detected
  - This matters for Phase B: persona messages should match the expected formality

### 9.4 Update Agent Map Schema

**File**: `src/graph/builder.py`

- [ ] Replace `metadata.conversation_language` (string) with `metadata.language` (object):
  ```json
  "metadata": {
      "language": {
          "conversation_languages": ["Spanish"],
          "primary_language": "Spanish",
          "guardrail_language": "Spanish",
          "language_mismatch": false,
          "code_switching_detected": false,
          "spanish_formality": "usted",
          "confidence": 0.92
      },
      "domain": {
          "type": "customer_support",
          "industry": "consumer_electronics",
          "channel": "whatsapp"
      }
  }
  ```

- [ ] Keep backward compatibility: also set `metadata.conversation_language` as a flat string for Phase B code that reads the old field

### 9.5 Update Framework Signatures

**File**: `config/framework_signatures.py`

- [ ] Add language detection word lists:
  ```python
  SPANISH_INDICATORS = [
      "bienvenido", "hola", "servicio", "cliente", "cita", "reserva",
      "consulta", "agente", "disponible", "horario", "gracias", "ayuda",
      "problema", "solución", "pedido", "factura", "devolución", "garantía",
      "reparación", "técnico", "soporte", "atención", "información",
      "confirmar", "cancelar", "modificar", "estado", "seguimiento", "envío", "pago",
  ]
  PORTUGUESE_INDICATORS = [
      "obrigado", "bom dia", "serviço", "cliente", "atendimento",
      "consulta", "agendamento", "disponível", "horário", "ajuda",
      "problema", "solução", "pedido", "fatura", "devolução", "garantia",
  ]
  DOMAIN_INDICATORS = {
      "customer_support": ["support", "ticket", "complaint", "helpdesk", "soporte", "queja", "atención"],
      "sales": ["order", "purchase", "price", "product", "pedido", "compra", "precio"],
      "scheduling": ["appointment", "booking", "schedule", "calendar", "cita", "reserva", "agenda"],
  }
  CHANNEL_INDICATORS = {
      "whatsapp": ["whatsapp", "wa_", "wamid"],
      "web_chat": ["webchat", "livechat", "chat_widget"],
      "email": ["email", "inbox", "smtp"],
  }
  ```

## Files Modified

| File | Changes |
|------|---------|
| `src/graph/builder.py` | Expand language detection, add domain detection, update Agent Map schema |
| `config/framework_signatures.py` | Add language, domain, and channel indicator word lists |

## Done When

- Agent Map `metadata.language` is a rich object with primary language, guardrail language, mismatch flag, code-switching detection, and formality level
- Agent Map `metadata.domain` includes type, industry, and channel
- Portuguese is detected alongside Spanish and English
- Code-switching (mixed-language prompts) is flagged
- Backward compatibility maintained: `metadata.conversation_language` still exists as a flat string
- Phase B can read these fields to generate language-appropriate adversarial tests
