#!/usr/bin/env python
"""
Vireon-HLE Engine — robust runner v0.2

Behavior:
- Tries to load an HLE dataset (JSON/JSONL).
- If present, runs dataset-level evaluation via hle_engine.
- If missing or invalid, falls back to a minimal stub,
  but never crashes (exit code 0).
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

from hle_data import load_hle_questions
from hle_engine import run_dataset_eval


DEFAULT_DATA_CANDIDATES: List[str] = [
    "data/hle_questions.jsonl",
    "data/hle_questions.json",
    "data/hle_questions.example.jsonl",
]


def _find_default_dataset() -> Path | None:
    for name in DEFAULT_DATA_CANDIDATES:
        p = Path(name)
        if p.is_file():
            return p
    return None


def _stub_metrics(note: str, error: str | None = None) -> Dict[str, Any]:
    base: Dict[str, Any] = {
        "engine": "Vireon-HLE",
        "version": "0.2.0",
        "num_questions": 0,
        "accuracy": 0.0,
        "status": "no_data",
        "notes": note,
    }
    if error is not None:
        base["error"] = error
    return base


def run_hle_eval() -> Dict[str, Any]:
    dataset_path = _find_default_dataset()
    if dataset_path is None:
        return _stub_metrics(
            "No HLE dataset found. Place a JSON/JSONL file in data/ to enable full eval."
        )

    try:
        questions = load_hle_questions(dataset_path)
        stats = run_dataset_eval(questions)
    except Exception as e:
        return _stub_metrics(
            f"Failed to load or evaluate HLE dataset at {dataset_path}.", error=str(e)
        )

    # For now, we don't have model responses, so 'accuracy' is a placeholder.
    metrics: Dict[str, Any] = {
        "engine": "Vireon-HLE",
        "version": "0.2.0",
        "status": "ok",
        "notes": f"Dataset-level stats for {dataset_path}",
        "accuracy": 0.0,
    }
    metrics.update(stats)
    return metrics


def main() -> None:
    metrics = run_hle_eval()
    print(json.dumps(metrics, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
