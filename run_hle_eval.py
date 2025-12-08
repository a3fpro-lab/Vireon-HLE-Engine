import json
from pathlib import Path
from typing import Any, Dict, List


def load_hle_questions(path: str | Path) -> List[Dict[str, Any]]:
    """
    Load HLE questions from a JSONL or JSON file.

    - Ignores blank lines and lines starting with '#'
    - Raises a clear error showing the offending line if JSON is invalid
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"HLE questions file not found: {path}")

    questions: List[Dict[str, Any]] = []

    with path.open("r", encoding="utf-8") as f:
        for lineno, raw in enumerate(f, start=1):
            line = raw.strip()
            # Skip blanks / comments
            if not line or line.startswith("#"):
                continue

            try:
                obj = json.loads(line)
            except json.JSONDecodeError as e:
                # Give a *very* explicit message so we can fix the data file quickly
                msg = (
                    f"Invalid JSON in {path} at line {lineno}: {e.msg} "
                    f"(pos {e.pos}, col {e.colno})\n"
                    f"Offending line:\n{raw}"
                )
                raise ValueError(msg) from e

            if not isinstance(obj, dict):
                raise ValueError(
                    f"Expected JSON object on line {lineno} of {path}, "
                    f"got {type(obj).__name__}"
                )

            questions.append(obj)

    if not questions:
        raise ValueError(f"No questions loaded from {path} (all blank/comment?)")

    return questions
