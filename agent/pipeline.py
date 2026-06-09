from __future__ import annotations

from agent import bug_scanner, diff_analyzer, pr_summary, refactor, scorer
from agent.client import ClaudeClient

def run_pipeline(diff_text: str, no_ai: bool = False) -> dict:
    client = ClaudeClient()
    step1 = diff_analyzer.analyze(diff_text, client) #Understand developer intent
    step2 = bug_scanner.scan(diff_text, client, force_local=no_ai) #Find vulnerabilities
    step3 = refactor.suggest(diff_text, client) #Suggest cleaner code
    step4 = pr_summary.generate(step1, step2, step3, client) #Write PR summary
    reports = {
        "diff_analyzer": step1,
        "bug_scanner": step2,
        "refactor_suggester": step3,
        "pr_summary": step4,
    }
    step5 = scorer.score(diff_text, reports, client) #Grade commit quality
    reports["commit_score"] = step5
    return reports
    