# run_hle_eval.py
# Self-contained HLE evaluation script (no external hle_scoring module).

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple


# -------------------------
# Loading questions & results
# -------------------------

def load_hle_questions(path: str | Path) -> List[Dict[str, Any]]:
    """
    Load HLE questions from a JSON or JSONL file.

    Supports:
    - JSONL: one JSON object per line
    - JSON array: `[ {...}, {...}, ... ]`
    - Ignores blank lines in JSONL mode.
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Questions file not found: {path}")

    text = path.read_text(encoding="utf-8")
    stripped = text.lstrip()

    # JSON array
    if stripped.startswith("["):
        try:
            data = json.loads(text)
        except json.JSONDecodeError as e:
            raise ValueError(f"Failed to parse questions JSON array at {path}: {e}") from e
        if not isinstance(data, list):
            raise ValueError(f"Questions file {path} must contain a JSON array.")
        return data

    # JSONL
    data: List[Dict[str, Any]] = []
    for line in text.splitlines():
        if not line.strip():
            continue
        try:
            obj = json.loads(line)
        except json.JSONDecodeError as e:
            raise ValueError(
                f"Failed to parse questions JSONL line in {path!s}: {e}"
            ) from e
        data.append(obj)
    return data


def load_hle_results(path: str | Path) -> Dict[str, Dict[str, Any]]:
    """
    Load model results from a JSON or JSONL file.

    We try to be forgiving:
    - Accept JSONL (one JSON object per line)
    - Or a single JSON array of objects
    - Ignore blank lines

    Each row is expected to have some question identifier:
    one of: 'question_id', 'id', 'qid', or 'index'.
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Results file not found: {path}")

    text = path.read_text(encoding="utf-8")
    stripped = text.lstrip()

    # JSON array
    if stripped.startswith("["):
        try:
            items = json.loads(text)
        except json.JSONDecodeError as e:
            raise ValueError(f"Failed to parse results JSON array at {path}: {e}") from e
        if not isinstance(items, list):
            raise ValueError(f"Results file {path} must contain a JSON array.")
    else:
        # JSONL
        items: List[Dict[str, Any]] = []
        for line in text.splitlines():
            if not line.strip():
                continue
            try:
                items.append(json.loads(line))
            except json.JSONDecodeError as e:
                raise ValueError(
                    f"Failed to parse results JSONL line in {path!s}: {e}"
                ) from e

    data: Dict[str, Dict[str, Any]] = {}
    for row in items:
        qid = (
            row.get("question_id")
            or row.get("id")
            or row.get("qid")
            or row.get("index")
        )
        if qid is None:
            raise KeyError(
                "Result row missing question id field; expected one of "
                "'question_id', 'id', 'qid', or 'index'. "
                f"Row was: {row}"
            )
        data[str(qid)] = row

    return data


# -------------------------
# Scoring
# -------------------------

def _extract_correct_and_confidence(result: Dict[str, Any]) -> Tuple[bool, float]:
    """
    Extract (is_correct, confidence) from a single result row.

    Supported correctness keys:
      - 'is_correct' (bool)
      - 'correct'   (bool)
      - 'score'     (float; >0.5 => correct)

    Supported confidence keys:
      - 'confidence'
      - 'prob'
    Default confidence is 1.0 if missing.
    """
    # correctness
    if "is_correct" in result:
        correct = bool(result["is_correct"])
    elif "correct" in result:
        correct = bool(result["correct"])
    elif "score" in result:
        try:
            correct = float(result["score"]) > 0.5
        except (TypeError, ValueError):
            correct = False
    else:
        raise KeyError(
            "Result row missing correctness indicator; expected one of "
            "'is_correct', 'correct', or 'score'. "
            f"Row was: {result}"
        )

    # confidence
    if "confidence" in result:
        try:
            conf = float(result["confidence"])
        except (TypeError, ValueError):
            conf = 1.0
    elif "prob" in result:
        try:
            conf = float(result["prob"])
        except (TypeError, ValueError):
            conf = 1.0
    else:
        conf = 1.0

    # Clamp into [0, 1]
    if conf < 0.0:
        conf = 0.0
    elif conf > 1.0:
        conf = 1.0

    return correct, conf


def score_results(
    questions: Iterable[Dict[str, Any]],
    results: Dict[str, Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Compute simple accuracy and Expected Calibration Error (ECE).

    Returns:
        {
            "n": int,
            "accuracy": float,
            "ece": float,
        }
    """
    y_true: List[bool] = []
    y_conf: List[float] = []

    for q in questions:
        qid = (
            q.get("question_id")
            or q.get("id")
            or q.get("qid")
            or q.get("index")
        )
        if qid is None:
            # Skip malformed questions instead of crashing
            continue

        key = str(qid)
        if key not in results:
            # No prediction for this question → skip
            continue

        correct, conf = _extract_correct_and_confidence(results[key])
        y_true.append(correct)
        y_conf.append(conf)

    n = len(y_true)
    if n == 0:
        return {"n": 0, "accuracy": 0.0, "ece": 0.0}

    # Accuracy
    accuracy = sum(1 for v in y_true if v) / n

    # Simple ECE with 10 uniform bins over [0,1]
    num_bins = 10
    bin_totals = [0] * num_bins
    bin_correct = [0] * num_bins

    for truth, conf in zip(y_true, y_conf):
        idx = int(conf * num_bins)
        if idx == num_bins:
            idx = num_bins - 1
        bin_totals[idx] += 1
        if truth:
            bin_correct[idx] += 1

    ece = 0.0
    for i in range(num_bins):
        if bin_totals[i] == 0:
            continue
        acc_i = bin_correct[i] / bin_totals[i]
        conf_i = (i + 0.5) / num_bins  # bin center
        ece += abs(acc_i - conf_i) * (bin_totals[i] / n)

    return {"n": n, "accuracy": accuracy, "ece": ece}


# -------------------------
# CLI
# -------------------------

def main(argv: List[str] | None = None) -> None:
    """
    Command-line entry point.

    We accept both --hle_path and --questions_path for flexibility.
    """
    parser = argparse.ArgumentParser(description="Evaluate HLE results.")
    parser.add_argument(
        "--hle_path",
        type=str,
        default=None,
        help="Path to HLE questions file (JSON/JSONL). Alias for --questions_path.",
    )
    parser.add_argument(
        "--questions_path",
        type=str,
        default=None,
        help="Path to HLE questions file (JSON/JSONL).",
    )
    parser.add_argument(
        "--results_path",
        type=str,
        default="hle_results.jsonl",
        help="Path to model results file (JSON/JSONL).",
    )

    args = parser.parse_args(argv)

    questions_path = args.questions_path or args.hle_path or "hle_questions.jsonl"
    results_path = args.results_path

    questions = load_hle_questions(questions_path)
    results = load_hle_results(results_path)
    metrics = score_results(questions, results)

    # Stable key order for tests
    print(json.dumps(metrics, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
