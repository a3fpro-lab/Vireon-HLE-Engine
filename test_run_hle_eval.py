import run_hle_eval


def test_hle_stub_metrics_shape():
    metrics = run_hle_eval.run_hle_eval()

    # basic structure
    assert isinstance(metrics, dict)
    for key in ["engine", "version", "num_questions", "accuracy", "status", "notes"]:
        assert key in metrics

    # sanity checks
    assert metrics["engine"] == "Vireon-HLE"
    assert metrics["status"] == "ok"
    assert isinstance(metrics["num_questions"], int)
    assert isinstance(metrics["accuracy"], (int, float))
