#!/usr/bin/env python
"""
Vireon-HLE evaluation runner.

- Robust loader for HLE questions (JSON array OR JSONL)
- Clear error messages showing exactly which line is invalid
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, List


def _guess_default_questions_file() -> Path:
    """
    Try to find a reasonable default questions file so
    `python run_hle_eval.py` works in CI without args.
    """
    candidates = [
        "data/hle_questions.jsonl",
        "data/hle_questions.json",
        "hle_questions.jsonl",
        "hle_questions.json",
        "questions.jsonl",
        "questions.json",
    ]
    for name in candidates:
        p = Path(name)
        if p.is_file():
            return p

    raise FileNotFoundError(
        "Could not find any HLE questions file. "
        "Tried: " + ", ".join(candidates)
    )


def load_hle_questions(path: str | Path) -> List[Dict[str, Any]]:
    """
    Load HLE questions from a JSON or JSONL file.

    Supports:
    - A single JSON array: [ {...}, {...}, ... ]
    - JSONL: one JSON object per non-empty line

    Skips blank lines and lines starting with '#' or '//'.
    Raises a detailed error on malformed JSON.
    """
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"HLE questions file not found: {p}")

    text = p.read_text(encoding="utf-8").strip()
    if not text:
        raise ValueError(f"{p} is empty")

    # Case 1: whole file is a JSON array
    if text[0] == "[":
        try:
            arr = json.loads(text)
        except json.JSONDecodeError as e:
            raise ValueError(
                f"Invalid JSON array in {p}: {e.msg} "
                f"(line {e.lineno}, col {e.colno}, pos {e.pos})"
            ) from e

        if not isinstance(arr, list):
            raise ValueError(
                f"Expected list in {p}, got {type(arr).__name__}"
            )
        for idx, obj in enumerate(arr, start=1):
            if not isinstance(obj, dict):
                raise ValueError(
                    f"Element {idx} in {p} is not an object: "
                    f"{type(obj).__name__}"
                )
        return arr  # type: ignore[return-value]

    # Case 2: treat as JSONL
    questions: List[Dict[str, Any]] = []
    for lineno, raw in enumerate(text.splitlines(), start=1):
        line = raw.strip()
        if not line or line.startswith("#") or line.startswith("//"):
            continue

        try:
            obj = json.loads(line)
        except json.JSONDecodeError as e:
            raise ValueError(
                f"Invalid JSON in {p} at line {lineno}: {e.msg} "
                f"(col {e.colno}, pos {e.pos})\n"
                f"Offending line:\n{raw}"
            ) from e

        if not isinstance(obj, dict):
            raise ValueError(
                f"Expected JSON object on line {lineno} of {p}, "
                f"got {type(obj).__name__}"
            )

        questions.append(obj)

    if not questions:
        raise ValueError(f"No questions loaded from {p}")

    return questions


def dummy_eval(questions: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Temporary placeholder evaluation.

    We just prove loading works; real Vireon-HLE metrics can be wired in later.
    """
    return {
        "num_questions": len(questions),
        "accuracy": 0.0,
        "notes": "Dummy eval – questions loaded successfully.",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Run Vireon HLE evaluation.")
    parser.add_argument(
        "--questions",
        "-q",
        type=str,
        default=None,
        help=(
            "Path to HLE questions file (JSON or JSONL). "
            "If omitted, a default path is auto-detected."
        ),
    )
    args = parser.parse_args()

    if args.questions is None:
        q_path = _guess_default_questions_file()
    else:
        q_path = Path(args.questions)

    questions = load_hle_questions(q_path)
    metrics = dummy_eval(questions)

    print(json.dumps(metrics, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
