from __future__ import annotations
from agent.client import ClaudeClient

"""
What files changed?
What was the intent?
How complex is it?
"""

#Informs claude the expected output shape
SCHEMA = {
    "files_changed": [{"path": "string", "reason": "string"}],
    "likely_intent": "string",
    "complexity_score": "integer 1-10",
}

SYSTEM = "You are a senior staff engineer at Anthropic, analyzing version-control diffs. Be concise, specific, and evident-based"

def analyze(diff_text, client: ClaudeClient | None = None) -> dict:
    fallback = { #backup response if claude fails
        "files_changed": [{"path": "unknown", "reason": "changed in stage diff"}] if diff_text else [],
        "likely_intent": "Update repository files based on staged changes",
        "complexity_score": min(10, max(1, diff_text.count("\n") // 40 + 1)), # counts # of lines and // by 40 then adds 1 and min(10,) complexity cannot go over 10 and max(1,) complexity cannot go below 1
    }

    user = f"Analyze this git-style diff and infer developer intent:\n\n{diff_text[:12000]}" #Builds prompt for Claude. Only first 12,000 chars.
    return (client or ClaudeClient()).complete_json(SYSTEM, user, SCHEMA, fallback) #calls client.py's complete_json 
