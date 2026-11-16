"""Run candidate code against inputs in a separate Python process.

Model-generated code is untrusted. Each candidate runs in a fresh `python -I`
subprocess with a timeout, in a temporary working directory. This is a basic
isolation layer, not a security sandbox: run the experiment in a container or
VM if you change the task bank or attacker prompts.
"""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from dataclasses import dataclass

_RUNNER = r"""
import json, sys
src, func, inputs = json.load(sys.stdin)
ns = {}
exec(compile(src, "<candidate>", "exec"), ns)
fn = ns[func]
out = []
for args in inputs:
    try:
        r = fn(*json.loads(json.dumps(args)))
        out.append({"ok": True, "value": json.loads(json.dumps(r))})
    except Exception as e:
        out.append({"ok": False, "error": type(e).__name__})
json.dump(out, sys.stdout)
"""


@dataclass
class RunResult:
    ok: bool  # process completed and produced results
    outputs: list | None
    error: str | None = None


def run(src: str, func: str, inputs: list[list], timeout: float = 10.0) -> RunResult:
    payload = json.dumps([src, func, inputs])
    with tempfile.TemporaryDirectory() as tmp:
        try:
            p = subprocess.run(
                [sys.executable, "-I", "-c", _RUNNER],
                input=payload,
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=tmp,
            )
        except subprocess.TimeoutExpired:
            return RunResult(False, None, "timeout")
    if p.returncode != 0:
        last = (p.stderr.strip().splitlines() or ["error"])[-1]
        return RunResult(False, None, last[:200])
    return RunResult(True, json.loads(p.stdout))


def compare(task, src: str, inputs: list[list]) -> tuple[bool, list[int]]:
    """Return (all_match, indices_that_differ) vs. the reference implementation."""
    ref = run(task.reference, task.func, inputs)
    got = run(src, task.func, inputs)
    if not ref.ok:
        raise RuntimeError(f"reference failed for {task.name}: {ref.error}")
    if not got.ok:
        return False, list(range(len(inputs)))
    diff = [i for i, (a, b) in enumerate(zip(ref.outputs, got.outputs)) if a != b]
    return not diff, diff


def classify(task, src: str, hidden_n: int = 300) -> dict:
    """Ground-truth label for a candidate: does it pass visible tests? hidden tests?"""
    vis_ok, _ = compare(task, src, task.visible)
    hidden = task.hidden_inputs(hidden_n)
    hid_ok, diff = compare(task, src, hidden)
    return {
        "passes_visible": vis_ok,
        "passes_hidden": hid_ok,
        "hidden_failures": len(diff),
        "hidden_total": len(hidden),
        "first_failing_input": hidden[diff[0]] if diff else None,
    }
