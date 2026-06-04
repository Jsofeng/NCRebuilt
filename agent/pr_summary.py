from __future__ import annotations
from agent.client import ClaudeClient

#How would we explain this commit as a pull request?
"""
{
    "title": "Refactor authentication module",

    "what_changed": [
        "Extracted validation helper",
        "Removed duplicate login logic"
    ],

    "why_changed":
        "Improve maintainability and reduce duplication",

    "risks": [
        "Potential authentication regressions"
    ],

    "suggested_reviewers": [
        "backend-team"
    ]
}

"""
SCHEMA = {
    "title": "string",
    "what_changed": ["string"],
    "why_changed": "string",
    "risks": ["string"],
    "suggested_reviewers": ["string"]
}

SYSTEM = "You're a senior engineer at Anthropic and a professional at writing pull requests. Descriptions from engineering analysis"

def generate(diff_report: dict, bug_report: dict, refactor_report: dict, client: ClaudeClient | None = None) -> dict:
    fallback = {
        "title": "Update repository files",
        "what_changed": [
            item.get("reason", "Changed file") for item in diff_report.get("files_changed", []) #tries to get "reason" from diff_analyzer.SCHEMA.files_changed if it doesn't exist return "Changed file as the reason"
        ],
        "why_changed": diff_report.get("likely_intent", "Intent inferred from commit diff"), #tries to get likely_intent from diff_analyzer.SCHEMA.likely_intent if it doesn't exist then return "Intent inferred from commit diff as the reason"
        "risks": [
            finding.get("title", "Potential issue") for finding in bug_report.get("findings", []) #tries to get title from bug_analyzer.SCHEMA.findings, if it doesn't exist then return "Potential issue" 
        ],
        "suggested_reviewers": ["repo-owner"],
    }

    #Prompt for claude
    user = (
        "Synthesize these reports into a PR description.\n"
        f"Diff analyzer: {diff_report}\n"
        f"Bug scanner: {bug_report}\n"
        f"Refactor: {refactor_report}"
    )

    #user is the output format
    #schema is what we input into claude
    return (client or ClaudeClient()).complete_json(SYSTEM, user, SCHEMA, fallback)
