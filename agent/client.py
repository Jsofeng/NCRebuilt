from __future__ import annotations

import json
import os
import time
from typing import Any

MODEL = "claude-sonnet-4-20250514"

class ClaudeClient:
    
    def __init__(self, model: str = MODEL):
        self.model = model

    """
    Send a prompt to Claude and expect structured clean JSON back.
    param:
        - prompt
        - user prompt containing its diff
        - expects JSON shape
        - Offline-safe output if Claude cannot run.
    """
    def complete_json(self, prompt: str, user: str, schema: dict[str, Any], fallback: dict[str, Any]) -> dict[str, Any]: #AI USED FOR DETECTION OF SECURITY BUGS
        
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            return fallback
        try:
            import anthropic #Anthropic SDK
        except ImportError:
            return fallback

        client = anthropic.Anthropic(api_key=api_key)
        last_error: Exception | None = None
        for attempt in range(5):
            try:
                #RULES SET TO THE AI TO GET EXPECTED OUTPUT
                message = client.messages.create(
                    model=self.model,
                    max_tokens=2000,
                    system=prompt,
                    messages=[
                        {
                            "role": "user",
                            "content": (
                                f"{user}\n\nReturn only JSON matching this schema:\n"
                                f"{json.dumps(schema, indent=2)}"
                            ),
                        }
                    ],
                )
                """
                Return only JSON matching this schema:

                {
                "files_changed": [
                    {
                    "path": "string",
                    "reason": "string"
                    }
                ],
                "likely_intent": "string",
                "complexity_score": "integer 1-10"
                }

                CLAUDE'S RESPONSE:
                {
                "files_changed": [
                    {
                    "path": "auth.py",
                    "reason": "Added login check"
                    }
                ],
                "likely_intent": "Add authentication",
                "complexity_score": 4
                }
                
                CLAUDE can return TextBlock,ToolUseBlock,ImageBlock but we only want the text ones so 
                Extract all text blocks from Claude response and merge them into a single JSON string.
                """
                text = "".join(block.text for block in message.content if getattr(block, "type", "") == "text") #Does this block have type == "text"? if so only grab the text portion 
                return json.loads(text) #Convert text into a Python dictionary.
            
            except Exception as exc:  
                last_error = exc
                time.sleep(min(2**attempt, 16))
        enriched = dict(fallback)
        enriched["error"] = str(last_error)
        return enriched #If all retries fail, return fallback plus error message.
    
