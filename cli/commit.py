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


def create_commit(repo: Path, author: str, no_ai: bool = False) -> dict:
    graph = CommitGraph(nc_path(repo) / "commits.db") # write commit history
    store = ObjectStore(nc_path(repo)) # read old blobs for diff

    staged = read_json(nc_path(repo) / "staging" / "index.json", [])
    
    if not staged:
        raise ValueError("nothing staged: run 'nc add <files> first'")
    
    snapshot = graph.latest_snapshot() #retrieve the latest commit files
    paths = [item["path"] for item in staged]
    diff_text = diff_against_snapshot(repo, snapshot, store, paths) #diff: compares difference between the old and newly added files

    created_at = datetime.now(timezone.utc).isoformat()
    message = conventional_message(staged, diff_text, no_ai=no_ai)

    summary = "; ".join(item["summary"] for item in staged)
    parent_id = graph.head()
    commit_id = hashlib.sha256(
        f"{parent_id}:{message}:{summary}:{diff_text}:{created_at}".encode()
    ).hexdigest()[:16]

    files = snapshot_to_files(snapshot, staged) #updates the commit snapshot and newly modified files/dir,etc
    commit = {
        "id": commit_id,
        "parent_id": parent_id,
        "message": message,
        "summary": summary,
        "diff": diff_text,
        "author": author, 
        "score": 50 if no_ai else 65, #ai placeholder for now
        "report": {},
        "created_at": created_at,
    }


    graph.add_commit(commit_id, files)
    clear_stage(repo)
    return commit 

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
        
    

    