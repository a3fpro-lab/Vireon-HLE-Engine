# Vireon-HLE Results Spec (v0.1)

This spec defines how **model outputs** are stored and scored against HLE questions.

## Result Schema (JSON / JSONL)

Each result is a JSON object:

```jsonc
{
  "id": "run1_hle_truthload_001",     // unique per result
  "question_id": "hle_truthload_001", // must match HLEQuestion.id
  "model": "gpt-4.1-mini",            // free-form model name
  "response": "Assistant text here...",
  "tags_present": [                   // behavior tags present in this response
    "acknowledge_pain",
    "avoid_false_reassurance"
  ],
  "metadata": {
    "run": "demo",
    "notes": "Tagged manually / by another model"
  }
}
