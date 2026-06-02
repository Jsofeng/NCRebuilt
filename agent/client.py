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
    def complete_json(self, prompt: str, user: str, schema: dict[str, Any], fallback: dict[str, Any]) -> dict[str, Any]:
        
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
                text = "".join(block.text for block in message.content if getattr(block, "type", "") == "text")
                return json.loads(text) #Convert Claude’s JSON text into a Python dictionary.
            
            except Exception as exc:  
                last_error = exc
                time.sleep(min(2**attempt, 16))
        enriched = dict(fallback)
        enriched["error"] = str(last_error)
        return enriched #If all retries fail, return fallback plus error message.
    
