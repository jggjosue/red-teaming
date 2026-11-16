"""Thin model clients. Keys come from environment variables only.

  anthropic:<model>   uses ANTHROPIC_API_KEY  (official `anthropic` SDK)
  openai:<model>      uses OPENAI_API_KEY     (official `openai` SDK; set OPENAI_BASE_URL
                      for any OpenAI-compatible endpoint, e.g. Gemini or a local model)
  mock:<anything>     offline stub for testing the pipeline; never use it for results
"""

from __future__ import annotations

import json


class Refusal(Exception):
    pass


class Model:
    def __init__(self, spec: str):
        self.spec = spec
        self.provider, _, self.model = spec.partition(":")
        if self.provider == "anthropic":
            import anthropic

            self._client = anthropic.Anthropic()
        elif self.provider == "openai":
            import openai

            self._client = openai.OpenAI()
        elif self.provider != "mock":
            raise ValueError(f"unknown provider in {spec!r}")

    def complete(self, system: str, user: str, max_tokens: int = 16000) -> str:
        if self.provider == "anthropic":
            # No refusal fallback on purpose: we want to measure the named model,
            # so a refusal is recorded as such instead of being answered by another model.
            r = self._client.messages.create(
                model=self.model,
                max_tokens=max_tokens,
                system=system,
                messages=[{"role": "user", "content": user}],
            )
            if r.stop_reason == "refusal":
                raise Refusal(str(r.stop_details))
            return "".join(b.text for b in r.content if b.type == "text")
        if self.provider == "openai":
            r = self._client.chat.completions.create(
                model=self.model,
                messages=[{"role": "system", "content": system}, {"role": "user", "content": user}],
            )
            return r.choices[0].message.content or ""
        return _mock(user)


def _mock(user: str) -> str:
    """Deterministic stub: echoes the code it was given and always says 'correct'."""
    if "```python" in user:
        code = user.split("```python", 1)[1].split("```", 1)[0]
        if "Introduce one subtle bug" in user:
            return f"```python{code}```\nBUG: none (mock)"
    return json.dumps({"verdict": "correct", "confidence": 0.5, "explanation": "mock", "failing_input": None})

