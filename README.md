

# Vireon HLE Engine

**Vireon = how serious models should take serious exams.**

This repo wraps *any* chat-style LLM (OpenAI, xAI/Grok, etc.) with a
Vireon-style protocol for hard exams like **Humanity’s Last Exam (HLE)**.

Instead of one-shot guessing, Vireon does:

- **V**erification-weighted checking (multi-pass verifier)
- **I**nformation-conscious effort tracking (steps + latency)
- **R**ecursive multi-path reasoning (multiple independent solves)
- **E**ntropy-aware aggregation (uses disagreement as a signal)
- **O**utcome-calibrated confidence (confidence ≈ reality)
- **N**ull / abstain behavior when uncertainty is high


---

## What this repo does

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

Vireon will:
	1.	Run multiple reasoning paths for each question.
	2.	For each answer letter (A–E), compute:
	•	fraction of paths voting for it (stability),
	•	average verification score (checker says CORRECT/INCORRECT),
	•	average information cost (steps + latency).
	3.	Combine these with a TRP-style score:

[
\text{TRP} \approx \frac{\text{correctness proxy} \times \text{fraction of paths}}{\text{info cost} + \lambda}
]
	4.	Select the best candidate and assign a normalized confidence.
	5.	Abstain when confidence < threshold (e.g., 0.60).

You get:
	•	Overall accuracy
	•	Accuracy when Vireon answers (excluding abstains)
	•	Abstain rate
	•	Confidence stats (correct vs wrong)

⸻

Files
	•	vireon_hle_engine.py
Core Vireon engine: multi-path reasoning, verification, TRP aggregation.
	•	llm_backends.py
Backend adapters. Choose between:
	•	xai   → Grok via xAI
	•	openai → OpenAI models
	•	dummy → simple stub
	•	run_hle_eval.py
CLI runner: loads hle_questions.jsonl, runs Vireon, prints metrics.
	•	hle_questions.jsonl
Small sample exam (3 questions) so you can run out of the box.

⸻

Install

python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

pip install -r requirements.txt


⸻

Configure a backend

Choose a provider via the VIREON_BACKEND env var.

xAI / Grok

export VIREON_BACKEND=xai
export XAI_API_KEY="sk-..."        # from xAI
# optional:
export XAI_MODEL="grok-4"          # default: grok-4

python run_hle_eval.py

OpenAI

export VIREON_BACKEND=openai
export OPENAI_API_KEY="sk-..."
export OPENAI_MODEL="gpt-5.1-thinking"

python run_hle_eval.py

Dummy (for wiring tests)

export VIREON_BACKEND=dummy
python run_hle_eval.py


⸻

HLE format

run_hle_eval.py expects a file called hle_questions.jsonl in the repo root.

Each line: one JSON object:

{"id": 1,
 "question": "In quantum mechanics, which operator corresponds to energy?",
 "options": ["Position operator", "Hamiltonian operator", "Momentum operator",
             "Angular momentum operator", "Number operator"],
 "answer": "B"}

	•	id (optional)
	•	question (string)
	•	options (list of 0–5 strings; if omitted you can later add short-answer mode)
	•	answer (string letter "A"–"E"; optional if you only want predictions)

This repo is not officially affiliated with Humanity’s Last Exam,
but is designed to run models in that format with the Vireon protocol.

⸻

Roadmap
	•	Short-answer support (non-multiple-choice HLE items)
	•	Better calibration metrics (ECE, reliability diagrams)
	•	Multimodal support (images / diagrams in questions)
	•	Simple web UI so you can watch Vireon take an exam in real time

---

> `Backend-agnostic Vireon reasoning wrapper for Humanity’s Last Exam and other hard AI benchmarks.`

# Vireon HLE Engine

**Vireon = how serious models should take serious exams.**

This repo wraps *any* chat-style LLM (OpenAI, xAI/Grok, etc.) with a
Vireon-style protocol for hard exams like **Humanity’s Last Exam (HLE)**.

Instead of one-shot guessing, Vireon does:

- **V**erification-weighted checking (multi-pass verifier)
- **I**nformation-conscious effort tracking (steps + latency)
- **R**ecursive multi-path reasoning (multiple independent solves)
- **E**ntropy-aware aggregation (uses disagreement as a signal)
- **O**utcome-calibrated confidence (confidence ≈ reality)
- **N**ull / abstain behavior when uncertainty is high

Goal: **less bullshit, more honest intelligence.**

---

## What this repo does

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

## Configure a backend

For full environment variable examples, see [ENVIRONMENT.md](ENVIRONMENT.md).

Choose a provider via the `VIREON_BACKEND` env var.
