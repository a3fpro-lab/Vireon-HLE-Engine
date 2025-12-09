"""
run_hle_eval.py

Lightweight, CI-friendly HLE evaluation stub.

- Exposes `run_hle_eval()` so tests can import and call:
    metrics = run_hle_eval.run_hle_eval()

- Returns a metrics dict with the same *shape* as a real HLE run:
    {
        "accuracy": float in [0, 1],
        "n": int (number of questions),
        "calibration_error": float
    }

If `results_path` is provided and points to a JSONL file where each line
has fields like:
    {
        "is_correct": bool,
        "confidence": float in [0, 1]
    }

then we compute simple metrics from that. Otherwise, we fall back to
default stub metrics so CI doesn’t depend on external data or APIs.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Optional

# Default stub metrics used when no results file is provided or parsing fails.
_DEFAULT_METRICS: Dict[str, Any] = {
    "accuracy": 0.0,
    "n": 0,
    "calibration_error": 0.0,
}


def run_hle_eval(results_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Run a minimal HLE evaluation and return metrics.

    Parameters
    ----------
    results_path : Optional[str]
        Optional path to a JSONL file of judged HLE results.
        Each non-empty line should be a JSON object with:
            - "is_correct": bool
            - "confidence": float in [0, 1] (optional; defaults to 0.0)

        If `results_path` is None or invalid, returns stub metrics with
        the correct shape for CI tests.

    Returns
    -------
    Dict[str, Any]
        A metrics dictionary with keys:
            - "accuracy": float in [0, 1]
            - "n": int
            - "calibration_error": float
    """
    # No path given → return stub with correct shape
    if results_path is None:
        return dict(_DEFAULT_METRICS)

    try:
        path = Path(results_path)
        if not path.exists():
            # Missing file → keep CI green with stub metrics
            return dict(_DEFAULT_METRICS)

        n = 0
        n_correct = 0
        calib_errors = []

        with path.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue

                record = json.loads(line)

                is_correct = bool(record.get("is_correct", False))
                # confidence may be missing; treat as 0.0
                confidence = float(record.get("confidence", 0.0))

                n += 1
                if is_correct:
                    n_correct += 1

                # Simple absolute calibration error
                target = 1.0 if is_correct else 0.0
                calib_errors.append(abs(target - confidence))

        if n == 0:
            # Nothing parsed → stub
            return dict(_DEFAULT_METRICS)

        accuracy = n_correct / n
        calibration_error = sum(calib_errors) / n if calib_errors else 0.0

        return {
            "accuracy": float(accuracy),
            "n": int(n),
            "calibration_error": float(calibration_error),
        }

    except Exception:
        # Any parsing / IO / JSON error → safe stub metrics
        return dict(_DEFAULT_METRICS)


def main() -> None:
    """
    CLI entry point.

    For now we just run the stub evaluation with no file and print the
    metrics in a human-readable way. This keeps `python run_hle_eval.py`
    usable while still being CI-safe.
    """
    metrics = run_hle_eval()

    print("*** HLE stub metrics ***")
    print(f"Accuracy: {metrics['accuracy']:.2%} | n = {metrics['n']}")
    print(f"Calibration Error: {metrics['calibration_error']:.3f}")


if __name__ == "__main__":
    main()
