from __future__ import annotations
import re

from agent.client import ClaudeClient

#Informs claude the expected output shape
SCHEMA = {
    "findings": [
        {
            "file": "string",
            "line": "integer",
            "title": "string",
            "details": "string",
            "severity": "LOW|MEDIUM|HIGH|CRITICAL",
        }
    ]
}

SYSTEM = "You are a senior security-focused code reviewer at Anthropic..." #This tells Claude its role.

"""
example input:

diff_text = '
+++ b/main.py
@@ -1,2 +1,3 @@
+password = "123"
'

"""

def heuristic_scan(diff_text: str) -> list[dict]: #This is offline bug detection. NO AI USED
    findings: list[dict] = []
    current_file = "unknown"
    new_line = 0

    for line in diff_text.splitlines():
        if line.startswith("+++ b/"):
            """
            +++ b/main.py
            +password = "123"

            +++ b/auth.py
            +eval(user_input)
            """
            current_file = line[6:] #grabs the current file name
        elif line.startswith("@@"):
            match = re.search(r"\+(\d+)", line) #using regex look for any strs that contain '+' followed by one or more digits
            #line = "@@ -10,4 +20,7 @@" regex finds +20 
            new_line = int(match.group(1)) - 1 if match else new_line #match.group(1) gets "20" only (subtracts 1 bc the elif statement at the bottom takes care of adding)
        elif line.startswith("+") and not line.startswith("+++"):
            body = line[1:].lower() #only inspect newly added code & Remove the leading + and lowercase the code.
            
            if "eval(" in body or "exec(" in body: #security risk
                findings.append(
                    {
                        "file": current_file,
                        "line": new_line,
                        "title": "Dynamic code execution",
                        "details": "New code executes a string as code, which can become remote code execution if input is attacker-controlled.",
                        "severity": "CRITICAL",
                    }
                )
            
            if "password" in body and ("=" in body or ":" in body) and "hash" not in body: #prevents "password=123 & password: "123"
                findings.append(
                    {
                        "file": current_file,
                        "line": new_line,
                        "title": "Possible secret handling issue",
                        "details": "A password-like value appears in changed code. Confirm it is not hard-coded or logged.",
                        "severity": "HIGH",
                    }
                )
        elif not line.startswith("-"):
            new_line+=1 
        
    return findings


"""
FUNCTIONALITY: Scans a git diff for bugs/vulnerabilities using AI, but falls back to a fast local scanner if needed.

skips claude and returns local findings (nc push --no-ai)

force_local: skips Claude and returns local findings.

"""
def scan(diff_text: str, client: ClaudeClient | None = None, force_local: bool = False) -> dict:
    
    fallback = {"findings": heuristic_scan(diff_text)} #Reason for implementation: works as a backup scanner, AI can fail, be slow, or cost money
    if force_local: #If user explicitly says: --no-ai skips and js returns fallback
        return fallback
    
    user = f"scan this git-style diff for bugs and vulnerabilities:\n\n{diff_text[:12000]}"
    result = (client or ClaudeClient()).complete_json(SYSTEM, user, SCHEMA, fallback) #gets AI's response instead of heuristic
    if not result.get("findings"): #if findings doesn't exist after getting back complete_json then set it to heuristic_scans
        result["findings"] = fallback["findings"]
    return result