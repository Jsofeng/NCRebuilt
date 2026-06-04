from __future__ import annotations
from agent.client import ClaudeClient


SCHEMA = {
    "score": "integer 0-100",
    "breakdown": {
        "code_quality": "integer 0-25",
        "commit_hygiene": "integer 0-25",
        "test_coverage_delta": "integer 0-25",
        "documentation_updates": "integer 0-25",
    },
    "rationale": "string",
}

SYSTEM = "You score commits fairly for production readiness. Penalize critical bugs and missing tests."

def score(diff_text: str, reports: dict, client: ClaudeClient | None = None) -> dict:
    findings = (
        reports.get("bug_scanner", {}).get("findings", []) #since "reports" is plural and can mean bug_scanner/refactor_repot/diff_analyzer we grab the "bug_scanner" one and retrieve its list[dict] of "findings"
    )

    penalty = sum(
        {
            "LOW": 5,
            "MEDIUM": 12,
            "HIGH": 25,
            "CRITICAL": 40,

        }.get(item["severity"], 8) #{LOW: 5, MEDIUM: 12, HIGH: 25, CRITICAL:40}.get(item["severity"]) 
        for item in findings
    )
    """
    82 is the default commit score if diff contains "test" e.g test_login.py then +8 score (0 is the lowest 100 is the max)
    """
    fallback_score = max(0, min(100, 82 - penalty + (8 if "test" in diff_text.lower() else 0))) 
    fallback = {
        "score": fallback_score, 
        "breakdown": {   
            "code_quality": min(25, fallback_score // 4), # there are 4 categories that is being marked so divide that by 4 to get it's mark
            "commit_hygiene": 20,
            "test_coverage_delta": 18 if "test" in diff_text.lower() else 8,
            "documentation_updates": 18 if ".md" in diff_text.lower() else 8,
        },
        "rationale": "Offline heuristic score based on findings, tests, and documentation changes.",

    }

    user = f"Score this commit using the provided reports.\nReports: {reports}\nDiff:\n{diff_text[:12000]}"
    result = (client or ClaudeClient()).complete_json(SYSTEM, user, SCHEMA, fallback)
    result["score"] = int(max(0, min(100, result.get("score", fallback_score)))) #AI might return something over 100 or below 0 so this is a safety check
    return result