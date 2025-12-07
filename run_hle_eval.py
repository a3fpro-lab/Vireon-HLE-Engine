# run_hle_eval.py

from typing import List, Optional

from vireon_hle_engine import VireonHLEEngine, VireonConfig


# ============================================================
# Built-in sample questions (no JSON file needed for CI)
# ============================================================
SAMPLE_QUESTIONS: List[dict] = [
    {
        "id": 1,
        "question": "In quantum mechanics, which operator corresponds to the observable of energy?",
        "options": [
            "Position operator",
            "Hamiltonian operator",
            "Momentum operator",
            "Angular momentum operator",
            "Number operator",
        ],
        "answer": "B",
    }
]


# ============================================================
# Very simple built-in dummy backend (no network, no API keys)
# ============================================================
def dummy_llm_call(system_prompt: str, user_prompt: str, temperature: float) -> str:
    """
    Dummy backend used for CI and local wiring tests.

    It always answers 'B' so that VireonHLEEngine can parse a valid option.
    """
    return (
        "This is the built-in dummy backend. "
        "No external API was called.\n\n"
        "Final answer: B"
    )


# ============================================================
# Main evaluation loop
# ============================================================
def main():
    questions = SAMPLE_QUESTIONS

    # Vireon HLE configuration – good starting defaults
    cfg = VireonConfig(
        n_paths=6,
        temperature=0.6,
        n_verifications=3,
        trp_lambda=0.12,
        min_confidence=0.60,
        mc_options="ABCDE",
    )

    # For CI and basic usage we use the internal dummy backend.
    llm_call = dummy_llm_call

    engine = VireonHLEEngine(llm_call=llm_call, config=cfg)

    total = correct = abstain = 0
    confidences: List[float] = []
    conf_correct: List[float] = []
    conf_incorrect: List[float] = []

    print(f"Loaded {len(questions)} questions. Starting Vireon HLE evaluation...\n")

    for q in questions:
        qtext: str = q["question"]
        options: Optional[List[str]] = q.get("options")
        gold: Optional[str] = q.get("answer")  # may be None if you only want preds

        total += 1
        print(f"\n=== Question {q.get('id', total)} ===")
        print(qtext)
        if options:
            letters = cfg.mc_options
            for i, opt in enumerate(options):
                if i < len(letters):
                    print(f"  {letters[i]}. {opt}")

        result = engine.answer_question(qtext, options)

        print("Vireon answer:", result.final_answer or "ABSTAIN")
        print("Confidence:", f"{result.confidence:.4f}")
        print("Reason:", result.reason[:500] + ("..." if len(result.reason) > 500 else ""))

        if result.final_answer is None:
            abstain += 1
            continue

        confidences.append(result.confidence)

        if gold is not None:
            if result.final_answer == gold:
                correct += 1
                conf_correct.append(result.confidence)
            else:
                conf_incorrect.append(result.confidence)

    # =================== Summary metrics ======================
    print("\n" + "=" * 50)
    print("                FINAL RESULTS")
    print("=" * 50)
    print(f"Total questions          : {total}")
    print(f"Answered                 : {total - abstain}")
    print(f"Abstained                : {abstain}")

    acc_overall = correct / total if total > 0 else 0.0
    answered = total - abstain
    acc_conditional = correct / answered if answered > 0 else 0.0

    print(f"Accuracy (overall)       : {acc_overall:.4f}")
    print(f"Accuracy (when answered) : {acc_conditional:.4f}")

    if confidences:
        avg_conf = sum(confidences) / len(confidences)
        avg_conf_cor = sum(conf_correct) / len(conf_correct) if conf_correct else 0.0
        avg_conf_inc = sum(conf_incorrect) / len(conf_incorrect) if conf_incorrect else 0.0

        print(f"Avg confidence (answered): {avg_conf:.4f}")
        print(f"Avg confidence (correct) : {avg_conf_cor:.4f}")
        print(f"Avg confidence (wrong)   : {avg_conf_inc:.4f}")


if __name__ == "__main__":
    main()
