# Vireon-HLE-Engine
This project is built specifically to run any LLM through Humanity’s Last Exam (and similar AI-intelligence benchmarks) using the Vireon protocol for multi-path reasoning, verification, calibration, and abstention. It is not officially affiliated with the HLE creators.


# Vireon HLE Engine

**Vireon = how frontier models should take frontier exams.**

This repo wraps *any* chat-style LLM (OpenAI, xAI/Grok, local) with a
Vireon-style reasoning protocol for **Humanity's Last Exam (HLE)** and
HLE-like benchmarks.

Instead of one-shot guessing, Vireon does:

- **V**erification-weighted checking (multi-pass verifier)
- **I**nformation-conscious effort tracking (steps + latency)
- **R**ecursive multi-path reasoning (multiple independent solves)
- **E**ntropy-aware aggregation (disagreement as a signal)
- **O**utcome-calibrated confidence (confidence ≈ reality)
- **N**ull / abstain behavior when uncertainty is high

Goal: **less bullshit, more honest intelligence.**

---

## What this actually does

Given a JSONL file of exam questions like:

```json
{"id": 1,
 "question": "In quantum mechanics, which operator corresponds to energy?",
 "options": [
   "Position operator",
   "Hamiltonian operator",
   "Momentum operator",
   "Angular momentum operator",
   "Number operator"
 ],
 "answer": "B"}
