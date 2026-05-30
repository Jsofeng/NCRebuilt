from __future__ import annotations

import difflib #Python built-in library for comparing text.

from pathlib import Path
from storage.object_store import ObjectStore


def text_or_placeholder(data: bytes) -> str:
    try:
        return data.decode("utf-8") #objectstore gives us bytes so we try to decode it into letters using decode utf-8 but if it's a binary file like an image it might fail
    except UnicodeDecodeError:
        return "<binary file>\n"

def unified_diff(path: str, before: str, after: str) -> str:
    """
    example of generation
    "--- a/test.txt\n"
    "+++ b/test.txt\n"
    "@@ -1,3 +1,3 @@\n"
    " hello\n"
    "-world\n"
    "+python\n"
    " bye\n"    
    """
    
    return "".join(
        difflib.unified_diff(
            before.splitlines(True), #True keeps the \n
            after.splitlines(True),
            fromfile=f"a/{path}",
            tofile=f"b/{path}",
        )
    )

"""
snapshot: prev committed file mapping:
paths: Files to compare:
"""
def diff_against_snapshot(repo: Path, snapshot: dict[str,str], store: ObjectStore, paths: list[str]) -> str: 
    chunks: list[str] = [] #same as chunks = [] but this line is a typehint used for readability to signify what chunks is supposed to store

    for rel in sorted(paths):
        path = repo / rel
        before = text_or_placeholder(store.get_bytes(snapshot[rel])) if rel else "" # loads old content from object store & turns the bytes file into text 
        after = text_or_placeholder(path.read_bytes()) if path.exists() else ""

        if before != after:
            chunks.append(unified_diff(rel, before, after))
        
    return "\n".join(chunk for chunk in chunks if chunk) #if chunk ignores all empty strings

"""
annotate_diff example output

--- a/app.py
+++ b/app.py
@@ -1 +1 @@
-print("hello")
# AI: removed behavior or data; check callers and migration impact.
+print("hello world")
# AI: added behavior or data; review tests and side effects.
"""


def annotate_diff(diff_text: str) -> str: #TBC -> Wait for Claude api & LLM reasoning
    annotations: list[str] = []
    for line in diff_text.splitlines():
        annotations.append(line)

        if line.startswith("+") and not line.startswith("+++"):
            annotations.append("# AI: added behavior or data; review tests and side effects.")
        elif line.startswith("-") and not line.startswith("---"):
            annotations.append("# AI: removed behavior or data; check callers and migration impact.")

    return "\n".join(annotations)

