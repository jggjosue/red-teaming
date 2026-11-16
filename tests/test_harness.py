"""Offline checks of the harness itself (no API calls)."""

import pytest

from pbw import sandbox
from pbw.experiment import _parse_verdict, plant_one, review_one
from pbw.providers import Model
from pbw.tasks import TASKS


@pytest.mark.parametrize("task", TASKS, ids=lambda t: t.name)
def test_reference_is_consistent(task):
    label = sandbox.classify(task, task.reference)
    assert label["passes_visible"] and label["passes_hidden"]


@pytest.mark.parametrize("task", TASKS, ids=lambda t: t.name)
def test_seed_bug_is_plausible_but_wrong(task):
    """The hidden tests must catch a bug that the visible tests miss."""
    label = sandbox.classify(task, task.seed_bug)
    assert label["passes_visible"], "seed bug should pass the visible tests"
    assert not label["passes_hidden"], "hidden tests should catch the seed bug"


def test_timeout_and_crash_are_handled():
    assert sandbox.run("def f():\n    while True: pass\n", "f", [[]], timeout=1).error == "timeout"
    assert not sandbox.run("def f(:\n", "f", [[]]).ok


def test_parse_verdict():
    v = _parse_verdict('Sure. {"verdict": "incorrect", "confidence": 0.9, "explanation": "x", "failing_input": [[1]]}')
    assert v["verdict"] == "incorrect" and v["failing_input"] == [[1]]
    assert _parse_verdict("no json here")["verdict"] == "unparsed"


def test_mock_pipeline_rejects_unchanged_code():
    row = plant_one(Model("mock:x"), TASKS[0], attempts=2)
    assert not row["valid"] and {a["status"] for a in row["attempts"]} == {"unchanged"}


def test_counterexample_verification():
    t = next(t for t in TASKS if t.name == "max_subarray")

    class Fake:
        spec = "fake"

        def complete(self, *_a, **_k):
            return '{"verdict": "incorrect", "confidence": 0.9, "explanation": "", "failing_input": [[-3, -1]]}'

    item = {"task": t.name, "variant": "human_bug", "is_buggy": True, "code": t.seed_bug}
    assert review_one(Fake(), item, "code_only")["counterexample_verified"]
    item_clean = {**item, "variant": "clean", "is_buggy": False, "code": t.reference}
    assert not review_one(Fake(), item_clean, "code_only")["counterexample_verified"]
