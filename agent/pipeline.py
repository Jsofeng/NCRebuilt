from __future__ import annotations

from agent import bug_scanner 
from agent.client import ClaudeClient


def run_pipeline(diff_text: str, no_ai: bool = False) -> dict:
    client = ClaudeClient()
    