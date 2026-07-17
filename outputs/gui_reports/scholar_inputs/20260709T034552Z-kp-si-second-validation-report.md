# Scholar Input Validation Report

SCHOLAR INPUT — NOT EVIDENCE

This record may seed a research question or retrieval lens, but it is not a source and cannot directly enter verification_queue.

## Report Type
scholar_input_validation_report

## Banner
SCHOLAR INPUT — NOT EVIDENCE

## Flow Warning
This record may seed a research question or retrieval lens, but it is not a source and cannot directly enter verification_queue.

## Record
```json
{
  "record_type": "scholar_input_not_evidence",
  "_note": "This record is scholar input, not evidence.",
  "schema_version": "0.2",
  "scholar_id": "KP-SI-SECOND",
  "source": "desktop_manual",
  "captured_ts": "2026-07-09T09:14:00+05:30",
  "imported_ts": "2026-07-09T09:14:00+05:30",
  "idea": "A second local test idea asks whether map language can seed a retrieval lens for chapter framing.",
  "draft_organ": "Research_Questions",
  "draft_diagnosis": "Possible foil for a chapter argument.",
  "draft_search_plan": "balance of power, central asia, alignment, hedging",
  "supervisor_brief": "Ask whether this should become a retrieval lens for opposing accounts.",
  "raw_notes": "Keep it as a fair strongest-opponent search, not a claim.",
  "voice_transcript": "",
  "tags": "counter-case,foil",
  "confidence": "hunch",
  "project_title": "Eurasian security imaginaries",
  "course_or_context": "PhD chapter 3",
  "status": "under_review",
  "content_sha256": "30d9586d36e82dbfcefd1f6b11c742f672549a1b906c28c36d4fe92b1b1268fc",
  "became_question": null,
  "became_queue_id": null,
  "decided_by": null,
  "decided_ts": null,
  "rejection_reason": null,
  "block_no": null
}
```

## Validation
```json
[
  {
    "level": "valid",
    "field": "record",
    "message": "Required v0.2 checks passed."
  },
  {
    "level": "valid",
    "field": "schema_version",
    "message": "Value is 0.2."
  },
  {
    "level": "valid",
    "field": "record_type",
    "message": "Value is scholar_input_not_evidence."
  },
  {
    "level": "valid",
    "field": "idea",
    "message": "Non-empty text present."
  },
  {
    "level": "valid",
    "field": "source",
    "message": "Value is allowed: desktop_manual."
  },
  {
    "level": "valid",
    "field": "status",
    "message": "Value is allowed: under_review."
  },
  {
    "level": "valid",
    "field": "captured_ts",
    "message": "Timestamp parses as ISO-8601."
  },
  {
    "level": "valid",
    "field": "imported_ts",
    "message": "Timestamp parses as ISO-8601."
  },
  {
    "level": "valid",
    "field": "draft_organ",
    "message": "Frozen organ value: Research_Questions."
  },
  {
    "level": "valid",
    "field": "content_sha256",
    "message": "Hash matches UI canonical content."
  }
]
```
