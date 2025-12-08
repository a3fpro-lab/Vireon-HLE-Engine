from pathlib import Path
from hle_data import load_hle_questions


def test_load_example_questions():
    path = Path("data/hle_questions.example.jsonl")
    questions = load_hle_questions(path)
    assert len(questions) >= 3

    ids = {q.id for q in questions}
    assert "hle_truthload_001" in ids
    assert "hle_selfharm_001" in ids
    assert "hle_truth_001" in ids
