from __future__ import annotations

import json
from pathlib import Path
from typing import List

from hle_schema import HLEQuestion


def _load_json_array(path: Path) -> List[HLEQuestion]:
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        raise ValueError(
            f"Invalid JSON array in {path}: {e.msg} (line {e.lineno}, col {e.colno})"
        ) from e
    if not isinstance(raw, list):
        raise TypeError(f"Top-level JSON in {path} must be an array")
    return [HLEQuestion.from_dict(obj) for obj in raw]


def _load_jsonl(path: Path) -> List[HLEQuestion]:
    questions: List[HLEQuestion] = []
    for lineno, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        line = raw.strip()
        if not line or line.startswith("#") or line.startswith("//"):
            continue
        try:
            obj = json.loads(line)
        except json.JSONDecodeError as e:
            raise ValueError(
                f"Invalid JSON at {path}:{lineno}: {e.msg} (col {e.colno})\n"
                f"Offending line:\n{raw}"
            ) from e
        try:
            question = HLEQuestion.from_dict(obj)
        except Exception as e:  # intentional, we want context
            raise ValueError(f"Invalid HLEQuestion at {path}:{lineno}: {e}") from e
        questions.append(question)
    if not questions:
        raise ValueError(f"No HLE questions loaded from {path}")
    return questions


def load_hle_questions(path: str | Path) -> List[HLEQuestion]:
    """
    Load HLE questions from a JSON or JSONL file.

    - If the file starts with '[' → parse as JSON array.
    - Else, treat as JSONL (one object per line).
    """
    p = Path(path)
    if not p.is_file():
        raise FileNotFoundError(f"HLE questions file not found: {p}")

    text = p.read_text(encoding="utf-8").lstrip()
    if not text:
        raise ValueError(f"HLE questions file is empty: {p}")

    if text[0] == "[":
        return _load_json_array(p)
    return _load_jsonl(p)
