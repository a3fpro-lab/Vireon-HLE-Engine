from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Literal


UserFragility = Literal["low", "medium", "high"]


@dataclass
class EvaluationSpec:
    """Behavioral expectations for a single HLE question."""
    must: List[str] = field(default_factory=list)
    must_not: List[str] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: Dict[str, Any] | None) -> "EvaluationSpec":
        if data is None:
            return cls()

        if not isinstance(data, dict):
            raise TypeError(f"evaluation must be an object, got {type(data).__name__}")

        must = data.get("must", [])
        must_not = data.get("must_not", [])

        if not isinstance(must, list) or not all(isinstance(x, str) for x in must):
            raise TypeError("evaluation.must must be a list of strings")

        if not isinstance(must_not, list) or not all(isinstance(x, str) for x in must_not):
            raise TypeError("evaluation.must_not must be a list of strings")

        return cls(must=list(must), must_not=list(must_not))


@dataclass
class HLEQuestion:
    """Single HLE question with truth/load annotations."""
    id: str
    category: str
    prompt: str
    user_fragility: UserFragility = "medium"
    evaluation: EvaluationSpec = field(default_factory=EvaluationSpec)
    metadata: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "HLEQuestion":
        if not isinstance(data, dict):
            raise TypeError(f"HLEQuestion.from_dict expected dict, got {type(data).__name__}")

        try:
            qid = data["id"]
            category = data["category"]
            prompt = data["prompt"]
        except KeyError as e:
            raise KeyError(f"Missing required field in HLEQuestion: {e.args[0]}") from e

        if not isinstance(qid, str):
            raise TypeError("id must be a string")
        if not isinstance(category, str):
            raise TypeError("category must be a string")
        if not isinstance(prompt, str):
            raise TypeError("prompt must be a string")

        user_fragility = data.get("user_fragility", "medium")
        if user_fragility not in ("low", "medium", "high"):
            raise ValueError(
                f"user_fragility must be 'low', 'medium', or 'high', not {user_fragility!r}"
            )

        eval_spec = EvaluationSpec.from_dict(data.get("evaluation"))
        metadata = data.get("metadata") or {}
        if not isinstance(metadata, dict):
            raise TypeError("metadata must be an object if present")

        return cls(
            id=qid,
            category=category,
            prompt=prompt,
            user_fragility=user_fragility,  # type: ignore[arg-type]
            evaluation=eval_spec,
            metadata=dict(metadata),
        )
