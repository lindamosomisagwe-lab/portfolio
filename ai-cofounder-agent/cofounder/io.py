"""Founder I/O: real interactive prompts, or a scripted queue for demo runs."""
from __future__ import annotations

import json
from pathlib import Path


class FounderIO:
    """Interactive by default (real input()). Pass a script path to replay
    a fixed sequence of founder answers non-interactively, echoing each
    answer to stdout so the transcript reads like a live session."""

    def __init__(self, script_path: str | None = None):
        self._queue: list[str] = []
        if script_path:
            with Path(script_path).open() as f:
                self._queue = json.load(f)

    def ask(self, prompt: str) -> str:
        print(f"\n>>> {prompt}")
        if self._queue:
            answer = self._queue.pop(0)
            print(f"[founder] {answer}")
            return answer
        return input("[founder] ")
