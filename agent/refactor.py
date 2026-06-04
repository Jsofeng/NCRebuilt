from __future__ import annotations
from agent.client import ClaudeClient

SCHEMA = {
    "suggestions": [
        {
            "file": "string",
            "problem": "string",
            "before": "string",
            "after": "string",
            "benefit": "string",
        }
    ]
}

SYSTEM = "You are a senior pragmatic refracting coach at Anthropic. Suggest only concrete improvements visible in the diff"


def suggest(diff_text: str, client: ClaudeClient | None = None) -> dict:
    fallback = {"suggestion": []} #incase it fails we don't want to make up a random refactor
    user = f"Find code smells, DRY issues, and performance anti-patterns in this diff:\n\n{diff_text[:12000]}" #prompt given to claude with a limit of 12000 characters to not overload tokens
    return (client or ClaudeClient()).complete_json(SYSTEM, user, SCHEMA, fallback)