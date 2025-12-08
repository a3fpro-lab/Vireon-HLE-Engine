from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List


@dataclass
class HLEResult:
    num_questions: int
    num_correct: int
    accuracy: float
    meta: Dict[str, Any]


class HLEEngine:
    """
    Minimal Vireon-HLE engine skeleton.

    Right now:
    - Expects each question to have: "id", "answer", "prediction"
    - Computes simple accuracy

    Later:
    - Plug in TRP / entropy / Vireon metrics
    - Add calibration, difficulty, etc.
    """

    def __init__(self, version: str = "0.1.0"):
        self.version = version

    def evaluate(self, questions: List[Dict[str, Any]]) -> HLEResult:
        if not questions:
            return HLEResult(
                num_questions=0,
                num_correct=0,
                accuracy=0.0,
                meta={"version": self.version, "notes": "Empty question set."},
            )

        num_questions = len(questions)
        num_correct = 0

        for q in questions:
            gold = q.get("answer")
            pred = q.get("prediction")
            if gold is not None and pred is not None and gold == pred:
                num_correct += 1

        accuracy = num_correct / num_questions

        return HLEResult(
            num_questions=num_questions,
            num_correct=num_correct,
            accuracy=accuracy,
            meta={
                "version": self.version,
                "notes": "Plain accuracy over (answer, prediction) pairs.",
            },
        )
