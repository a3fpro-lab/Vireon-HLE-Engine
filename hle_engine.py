from __future__ import annotations

from collections import Counter
from typing import Any, Dict, List

from hle_schema import HLEQuestion


def run_dataset_eval(questions: List[HLEQuestion]) -> Dict[str, Any]:
    """
    Compute dataset-level stats for a set of HLE questions.

    This does NOT require model outputs yet. It gives:
    - basic counts
    - category distribution
    - fragility distribution
    - tag statistics
    """
    num_questions = len(questions)
    categories = Counter(q.category for q in questions)
    fragility = Counter(q.user_fragility for q in questions)

    total_must = sum(len(q.evaluation.must) for q in questions)
    total_must_not = sum(len(q.evaluation.must_not) for q in questions)

    return {
        "num_questions": num_questions,
        "categories": dict(categories),
        "fragility_distribution": dict(fragility),
        "total_must_tags": total_must,
        "total_must_not_tags": total_must_not,
    }
