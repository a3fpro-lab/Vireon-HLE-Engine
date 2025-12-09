# hle_scoring.py
# Simple scoring utilities for HLE-style results.
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple


def load_hle_results(path: str | Path) -> Dict[str, Dict[str, Any]]:
    """
    Load model results from a JSON or JSONL file.

    We try to be forgiving:
    - Accept JSONL (one JSON object per line)
    - Or a single JSON array of objects
    - Ignore blank lines

    Each row is expected to have some kind of question identifier:
    one of: 'question_id', 'id', 'qid', or 'index'.
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Results file not found: {path}")

    text = path.read_text(encoding="utf-8")
    stripped = text.lstrip()

    # Decide whether this is JSONL or a JSON array
    if stripped.startswith("["):
        try:
            items = json.loads(text)
        except json.JSONDecodeError as e:
            raise ValueError(f"Failed to parse results JSON array at {path}: {e}") from e
    else:
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


def _extract_correct_and_confidence(result: Dict[str, Any]) -> Tuple[bool, float]:
    """
    Extract (is_correct, confidence) from a single result row.

    We support a few common field names so the runner can evolve
    without breaking this module:
      - correctness: 'is_correct' | 'correct' | 'score' (score>0.5)
      - confidence: 'confidence' | 'prob' (else default 1.0)
    """
    # correctness
    if "is_correct" in result:
        correct = bool(result["is_correct"])
    elif "correct" in result:
        correct = bool(result["correct"])
    elif "score" in result:
        # Treat scores on [0,1] as probability-like
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
        # If we don't have an explicit confidence, assume fully confident.
        conf = 1.0

    # Clamp into [0,1] so calibration math behaves
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
    Compute simple accuracy and a basic Expected Calibration Error (ECE).

    Parameters
    ----------
    questions:
        Iterable of HLE question dicts. Each is expected to have some
        identifier like 'question_id', 'id', 'qid', or 'index'.

    results:
        Mapping from question-id-as-string to model result dicts.

    Returns
    -------
    A dict like:
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
            # Skip malformed question entries instead of crashing
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
        # conf in [0,1] → bin index 0..9
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
