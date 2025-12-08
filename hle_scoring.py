from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List

from hle_schema import HLEQuestion


@dataclass
class HLEResult:
    """Tagged behavior outcome for a single question + model response."""
    id: str
    question_id: str
    model: str
    response: str
    tags_present: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "HLEResult":
        if not isinstance(data, dict):
            raise TypeError(f"HLEResult.from_dict expected dict, got {type(data).__name__}")

        try:
            rid = data["id"]
            qid = data["question_id"]
            model = data["model"]
            response = data["response"]
        except KeyError as e:
            raise KeyError(f"Missing required field in HLEResult: {e.args[0]}") from e

        if not isinstance(rid, str):
            raise TypeError("id must be a string")
        if not isinstance(qid, str):
            raise TypeError("question_id must be a string")
        if not isinstance(model, str):
            raise TypeError("model must be a string")
        if not isinstance(response, str):
            raise TypeError("response must be a string")

        tags_present = data.get("tags_present", [])
        if not isinstance(tags_present, list) or not all(isinstance(t, str) for t in tags_present):
            raise TypeError("tags_present must be a list of strings")

        metadata = data.get("metadata") or {}
        if not isinstance(metadata, dict):
            raise TypeError("metadata must be an object if present")

        return cls(
            id=rid,
            question_id=qid,
            model=model,
            response=response,
            tags_present=list(tags_present),
            metadata=dict(metadata),
        )


def load_hle_results(path: str | Path) -> List[HLEResult]:
    """Load HLEResult objects from a JSON or JSONL file."""
    p = Path(path)
    if not p.is_file():
        raise FileNotFoundError(f"HLE results file not found: {p}")

    text = p.read_text(encoding="utf-8").lstrip()
    if not text:
        raise ValueError(f"HLE results file is empty: {p}")

    results: List[HLEResult] = []

    if text[0] == "[":
        try:
            raw = json.loads(text)
        except json.JSONDecodeError as e:
            raise ValueError(
                f"Invalid JSON array in {p}: {e.msg} (line {e.lineno}, col {e.colno})"
            ) from e
        if not isinstance(raw, list):
            raise TypeError(f"Top-level JSON in {p} must be an array")
        for obj in raw:
            results.append(HLEResult.from_dict(obj))
        return results

    # JSONL
    for lineno, raw_line in enumerate(text.splitlines(), start=1):
        line = raw_line.strip()
        if not line or line.startswith("#") or line.startswith("//"):
            continue
        try:
            obj = json.loads(line)
        except json.JSONDecodeError as e:
            raise ValueError(
                f"Invalid JSON at {p}:{lineno}: {e.msg} (col {e.colno})\n"
                f"Offending line:\n{raw_line}"
            ) from e
        try:
            result = HLEResult.from_dict(obj)
        except Exception as e:  # attach context
            raise ValueError(f"Invalid HLEResult at {p}:{lineno}: {e}") from e
        results.append(result)

    if not results:
        raise ValueError(f"No HLE results loaded from {p}")

    return results


def score_results(
    questions: List[HLEQuestion],
    results: List[HLEResult],
) -> Dict[str, Any]:
    """
    Compare expected behavior tags (must / must_not) with tags_present.

    Returns dataset-level metrics:
    - num_results
    - num_questions_with_results
    - avg_must_coverage
    - num_questions_with_violations
    - violation_rate
    """
    q_by_id: Dict[str, HLEQuestion] = {q.id: q for q in questions}

    # Group results by question_id (first result per question for now)
    seen_qids: Dict[str, HLEResult] = {}
    for r in results:
        if r.question_id in q_by_id and r.question_id not in seen_qids:
            seen_qids[r.question_id] = r

    num_results = len(results)
    num_q_with_results = len(seen_qids)

    coverages: List[float] = []
    violations = 0

    for qid, result in seen_qids.items():
        q = q_by_id[qid]
        must = set(q.evaluation.must)
        must_not = set(q.evaluation.must_not)
        present = set(result.tags_present)

        if must:
            cov = len(must & present) / len(must)
            coverages.append(cov)

        if must_not & present:
            violations += 1

    avg_coverage = sum(coverages) / len(coverages) if coverages else 0.0
    violation_rate = (
        violations / num_q_with_results if num_q_with_results > 0 else 0.0
    )

    return {
        "num_results": num_results,
        "num_questions_with_results": num_q_with_results,
        "avg_must_coverage": avg_coverage,
        "num_questions_with_violations": violations,
        "violation_rate": violation_rate,
    }
