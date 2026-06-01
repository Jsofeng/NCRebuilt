from __future__ import annotations

import hashlib 
from pathlib import Path
from datetime import datetime, timezone

from cli.diff import diff_against_snapshot
from cli.repo import nc_path, read_json
from cli.staging import clear_stage
from storage.commit_graph import CommitGraph
from storage.object_store import ObjectStore
from storage.vector_index import VectorIndex


"""
nc commit --no-ai

NeuralCommit Does..

- Read staged files.
- Find the latest commit.
- Generate a diff.
- Generate a commit message.
- Create a commit ID.
- Save commit metadata to SQLite.
- Save file snapshot rows to SQLite.
- Clear the staging area.

"""

"""
automatically creates a commit message given the params (feat,fix,docs,test,chore)
if no_ai is True then at the end of the commit msg it will include (offline) 
"""

def conventional_message(staged, diff_text, no_ai=False) -> str:
    paths = [item["path"] for item in staged]
    joined = " ".join(paths).lower()

    prefix = "chore" #default 

    if any(paths.endswith((".md", ".rst")) for path in paths): #If the changed file is markdown or reStructuredText, call it docs.
        prefix = "docs"

    if any(word in joined for word in ["test", "spec"]):
        prefix = "test"

    if any(line.startswith("+def ") or line.startswith("+class ") for line in diff_text.splitlines()):
        prefix = "feat"

    if any(word in diff_text.lower() for word in ["fix", "bug", "error", "exception"]):
        prefix = "fix"

    subject = ", ".join(paths[:2])

    if len(paths) > 2:
        subject += f" and {len(paths) - 2} more"

    suffix = "offline" if no_ai else "ai" #nc commit --no-ai = offline 

    return f"{prefix}: update {subject} ({suffix})"





"""
snapshot_to_files functionality

latest snapshot:
{
    "README.md": "old_readme_blob",
    "app.py": "old_app_blob"
}


staged changes:
[
    {
        "path": "app.py",
        "blob_sha": "new_app_blob",
        "status": "modified",
        "summary": "modified app.py: +2/-1 lines"
    }
]

new commit snapshot:
[
    {
        "path": "README.md",
        "blob_sha": "old_readme_blob",
        "status": "unchanged",
        "summary": "unchanged"
    },
    {
        "path": "app.py",
        "blob_sha": "new_app_blob",
        "status": "modified",
        "summary": "modified app.py: +2/-1 lines"
    }
]
"""


def snapshot_to_files(snapshot: dict[str, str], staged: list[dict[str,str]]) -> list[dict[str,str]]:
    merged = {
        path: {
            "path": path,
            "blob_sha": blob,
            "status": "unchanged",
            "summary": "unchanged",
        }
        for path, blob in snapshot.items()
    }

    for item in staged: #If a staged file changed, replace the old entry.
        merged[item["path"]] = item

    return list(merged.values())
        
    

    