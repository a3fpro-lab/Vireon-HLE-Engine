"""
run_hle_eval.py

Vireon HLE evaluation stub, CI-safe.

- Exposes `run_hle_eval()` for tests:
    metrics = run_hle_eval.run_hle_eval()

- When run as a script (python run_hle_eval.py), it does *not* require
  any external files and will return stub metrics with the correct shape.

- Optionally, you can pass a JSONL questions file with --questions to do
  a real evaluation later. Missing/invalid files fall back to stub metrics.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, List, Optional

# Minimal, CI-friendly default metrics
_DEFAULT_METRICS: Dict[str, Any] = {
    "accuracy": 0.0,
    "n": 0,
    "calibration_error": 0.0,
}


def load_hle_questions(path: str | Path) -> List[Dict[str, Any]]:
    """
    Load HLE questions from a JSONL file.

    Each non-empty line should be a JSON object representing one question.
    This is only used if a valid path is explicitly provided.
    """
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Questions file not found: {p}")

    questions: List[Dict[str, Any]] = []
    with p.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            questions.append(json.loads(line))
    return questions


def _evaluate_stub(questions: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Very simple evaluator: if any questions are provided, pretend the
    model got half correct and was mildly miscalibrated.

    This keeps the function deterministic and CI-safe without depending
    on any model APIs.
    """
    n = len(questions)
    if n == 0:
        return dict(_DEFAULT_METRICS)

    # Fake numbers just to have a non-trivial, deterministic shape.
    accuracy = 0.5
    calibration_error = 0.1

    return {
        "accuracy": float(accuracy),
        "n": int(n),
        "calibration_error": float(calibration_error),
    }


def run_hle_eval(questions_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Core entry point used by tests.

    Parameters
    ----------
    questions_path : Optional[str]
        Optional path to a JSONL questions file. If None or invalid,
        returns default stub metrics.

    Returns
    -------
    Dict[str, Any]
        Metrics dict with keys:
            - "accuracy": float in [0, 1]
            - "n": int
            - "calibration_error": float
    """
    if questions_path is None:
        # Pure stub mode – used by tests and default CLI
        return dict(_DEFAULT_METRICS)

    try:
        questions = load_hle_questions(questions_path)
    except FileNotFoundError:
        # Missing file → fall back to stub
        return dict(_DEFAULT_METRICS)
    except Exception:
        # Any parse/IO error → also fall back
        return dict(_DEFAULT_METRICS)

    return _evaluate_stub(questions)


def main() -> None:
    """
    CLI entry point.

    Default: run in stub mode (no external files) to keep CI green.
    Optional: pass --questions /path/to/hle_questions.jsonl if you
    later add a real dataset.
    """
    parser = argparse.ArgumentParser(
        description="Vireon HLE eval (CI-safe stub)."
    )
    parser.add_argument(
        "--questions",
        "-q",
        type=str,
        default=None,
        help="Optional path to HLE questions JSONL file.",
    )
    args = parser.parse_args()

    metrics = run_hle_eval(args.questions)

    print("Running Vireon HLE eval (stub)...")
    print(f"Accuracy         : {metrics['accuracy']:.2%}")
    print(f"Num questions (n): {metrics['n']}")
    print(f"Calibration error: {metrics['calibration_error']:.3f}")


if __name__ == "__main__":
    main()
