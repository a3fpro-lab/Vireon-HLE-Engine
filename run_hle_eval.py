#!/usr/bin/env python
"""
Vireon-HLE Engine — dataset + behavior scoring runner v0.3

Behavior:
- Try to load an HLE dataset (JSON/JSONL).
- Compute dataset-level stats (categories, fragility, tags).
- Try to load tagged results and compute behavior scores.
- On any data error, fall back to a safe stub without crashing.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

from hle_data import load_hle_questions
from hle_engine import run_dataset_eval
from hle_scoring import load_hle_results, score_results


DEFAULT_DATA_CANDIDATES: List[str] = [
    "data/hle_questions.jsonl",
    "data/hle_questions.json",
    "data/hle_questions.example.jsonl",
]

DEFAULT_RESULTS_CANDIDATES: List[str] = [
    "data/hle_results.jsonl",
    "data/hle_results.json",
    "data/hle_results.example.jsonl",
]


def _find_first_existing(candidates: List[str]) -> Path | None:
    for name in candidates:
        p = Path(name)
        if p.is_file():
            return p
    return None


def _stub_metrics(note: str, error: str | None = None) -> Dict[str, Any]:
    base: Dict[str, Any] = {
        "engine": "Vireon-HLE",
        "version": "0.3.0",
        "status": "no_data",
        "notes": note,
        "num_questions": 0,
        "accuracy": 0.0,
    }
    if error is not None:
        base["error"] = error
    return base


def run_hle_eval() -> Dict[str, Any]:
    dataset_path = _find_first_existing(DEFAULT_DATA_CANDIDATES)
    if dataset_path is None:
        return _stub_metrics(
            "No HLE dataset found. Place a JSON/JSONL file in data/ to enable full eval."
        )

    try:
        questions = load_hle_questions(dataset_path)
        dataset_stats = run_dataset_eval(questions)
    except Exception as e:
        return _stub_metrics(
            f"Failed to load or evaluate HLE dataset at {dataset_path}.", error=str(e)
        )

    metrics: Dict[str, Any] = {
        "engine": "Vireon-HLE",
        "version": "0.3.0",
        "status": "ok",
        "notes": f"Dataset-level stats for {dataset_path}",
        "accuracy": 0.0,  # placeholder until we define a model-level accuracy notion
    }
    metrics.update(dataset_stats)

    # Try to load and score model results if available
    results_path = _find_first_existing(DEFAULT_RESULTS_CANDIDATES)
    if results_path is not None:
        try:
            results = load_hle_results(results_path)
            scores = score_results(questions, results)
            metrics["results_path"] = str(results_path)
            metrics["behavior_scores"] = scores
        except Exception as e:
            # Do not crash the whole eval; just attach the error.
            metrics["results_error"] = str(e)

    return metrics


def main() -> None:
    metrics = run_hle_eval()
    print(json.dumps(metrics, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
