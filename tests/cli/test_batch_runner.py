import csv
import sys

from runaway import batch


def test_batch_runner_creates_summary_and_history(tmp_path) -> None:
    old_argv = sys.argv
    sys.argv = [
        "runaway-batch",
        "--output-dir",
        str(tmp_path),
        "--agents-list",
        "10",
        "--steps",
        "2",
        "--preset",
        "small",
        "--seeds",
        "5",
    ]
    try:
        batch.main()
    finally:
        sys.argv = old_argv

    summary = tmp_path / "summary.csv"
    history = tmp_path / "agents-10_seed-5_history.json"
    assert summary.is_file()
    assert history.is_file()

    with summary.open("r", encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    assert len(rows) == 1
    assert rows[0]["scenario"] == "agents-10"
    assert rows[0]["seed"] == "5"
