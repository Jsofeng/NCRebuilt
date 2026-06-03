from __future__ import annotations

from agent import bug_scanner, diff_analyzer, pr_summary, refactor, scorer
from agent.client import ClaudeClient

def run_pipeline(diff_text: str, no_ai: bool = False) -> dict:
    client = ClaudeClient()
    step1 = diff_analyzer.analyze(diff_text, client)
    step2 = bug_scanner.scan(diff_text, client, force_local=no_ai)
    
    