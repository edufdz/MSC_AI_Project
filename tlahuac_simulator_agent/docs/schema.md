# Dataset Schema Specification

## Version
v1

## Overview
This schema defines the structure for the customer simulator chatbot dataset. All conversations are stored in a unified JSON format with strict privacy controls - PII is sanitized and replaced with placeholders.

## Root Schema

```json
{
  "dataset_version": "v1",
  "generated_at": "2026-01-28T00:00:00Z",
  "conversations": []
}
```

### Root Fields

- `dataset_version` (string, required): Version identifier for the schema. Currently "v1".
- `generated_at` (string, required): ISO8601 timestamp of when the dataset was generated.
- `conversations` (array, required): Array of conversation objects.

## Conversation Schema

```json
{
  "conversation_id": "conv_0001",
  "source": {
    "system": "whatsapp",
    "file": "extracted_texts/Chat de WhatsApp con +52 222 347 8074_from_00000359-Chat de WhatsApp con +52 222 347 8074.txt"
  },
  "language": "es",
  "messages": [],
  "meta": {
    "dealer_id": null,
    "channel": "whatsapp"
  }
}
```

### Conversation Fields

- `conversation_id` (string, required): Unique identifier for the conversation. Format: `conv_XXXX` where XXXX is zero-padded number.
- `source` (object, required): Source information for traceability.
  - `system` (string, required): Source system type. Values: `"whatsapp"`, `"zendesk"`, `"crm"`.
  - `file` (string, required): Original filename/path of the source data.
- `language` (string, required): Language code (ISO 639-1). Currently `"es"` for Spanish.
- `messages` (array, required): Array of message objects. Must contain at least 2 messages.
- `meta` (object, required): Additional metadata.
  - `dealer_id` (string|null, optional): Dealer identifier if available.
  - `channel` (string, required): Communication channel. Values: `"whatsapp"`, `"email"`, `"phone"`, etc.

## Message Schema

```json
{
  "idx": 0,
  "ts": "2025-07-16T10:02:00-06:00",
  "speaker_raw": "+52 222 347 8074",
  "role": "customer",
  "text_raw": "¡Hola! Busco auto Suzuki Swift sport de seminuevos",
  "text": "¡Hola! Busco auto Suzuki Swift sport de seminuevos",
  "pii": {
    "has_pii": false,
    "types": []
  },
  "confidence": {
    "role": 0.92
  }
}
```

### Message Fields

- `idx` (integer, required): Zero-based index of the message within the conversation. Must be strictly increasing (0, 1, 2, ...).
- `ts` (string|null, required): ISO8601 timestamp of the message. Null if timestamp could not be parsed.
- `speaker_raw` (string, required): Original sender name/number as it appeared in the source data.
- `role` (string, required): Role classification. Values: `"customer"`, `"dealership"`, `"unknown"`.
- `text_raw` (string, required): Original message text before any sanitization. Preserves all original content including PII.
- `text` (string, required): Sanitized message text with PII replaced by placeholders. Must never contain real PII.
- `pii` (object, required): PII detection information.
  - `has_pii` (boolean, required): True if any PII was detected in the message.
  - `types` (array, required): Array of PII types detected. Values: `"PHONE"`, `"EMAIL"`, `"PLATE"`, `"VIN"`, `"ADDRESS"`, `"ORDER_ID"`, `"CASE_ID"`, `"NAME"`.
- `confidence` (object, required): Confidence scores for classifications.
  - `role` (float, required): Confidence score for role classification. Range: [0.0, 1.0].

## PII Placeholders

When PII is detected, it is replaced with the following placeholders in the `text` field:

- `<PHONE>` - Phone numbers
- `<EMAIL>` - Email addresses
- `<PLATE>` - License plates
- `<VIN>` - Vehicle Identification Numbers
- `<ADDRESS>` - Street addresses
- `<ORDER_ID>` - Order/folio numbers
- `<CASE_ID>` - Case/ticket IDs
- `<NAME>` - Personal names (optional)

## Privacy Rules

1. **Never store real PII**: The `text` field must never contain actual phone numbers, emails, plates, VINs, addresses, or other PII.
2. **Preserve original**: The `text_raw` field preserves the original message for traceability but should not be used for embeddings or model training.
3. **Consistent placeholders**: All PII must be replaced with standardized placeholders.
4. **Detection tracking**: The `pii` object tracks what was detected without storing the actual values.

## Example

```json
{
  "dataset_version": "v1",
  "generated_at": "2026-01-28T12:00:00Z",
  "conversations": [
    {
      "conversation_id": "conv_0001",
      "source": {
        "system": "whatsapp",
        "file": "extracted_texts/chat_001.txt"
      },
      "language": "es",
      "messages": [
        {
          "idx": 0,
          "ts": "2025-07-16T10:02:00-06:00",
          "speaker_raw": "+52 222 347 8074",
          "role": "customer",
          "text_raw": "Mi auto es Spark 2021 placas 32 BGV",
          "text": "Mi auto es Spark 2021 placas <PLATE>",
          "pii": {
            "has_pii": true,
            "types": ["PLATE"]
          },
          "confidence": {
            "role": 0.95
          }
        },
        {
          "idx": 1,
          "ts": "2025-07-16T10:03:00-06:00",
          "speaker_raw": "Chevrolet Calidad Tlahuac",
          "role": "dealership",
          "text_raw": "Gracias, le confirmo su cita para mañana",
          "text": "Gracias, le confirmo su cita para mañana",
          "pii": {
            "has_pii": false,
            "types": []
          },
          "confidence": {
            "role": 0.98
          }
        }
      ],
      "meta": {
        "dealer_id": null,
        "channel": "whatsapp"
      }
    }
  ]
}
```

## Validation Rules

1. Each conversation must have at least 2 messages.
2. Message `idx` must be strictly increasing (0, 1, 2, ...) with no gaps or duplicates.
3. `text` field must not be empty after normalization.
4. `text_raw` field must not be empty.
5. `role` must be one of: `"customer"`, `"dealership"`, `"unknown"`.
6. `text` field must not contain any real PII (validated via regex patterns).
7. If `pii.has_pii` is true, `text` must contain at least one placeholder.
8. `confidence.role` must be in range [0.0, 1.0].
9. `conversation_id` must be unique across all conversations.
10. `ts` must be valid ISO8601 format or null.
