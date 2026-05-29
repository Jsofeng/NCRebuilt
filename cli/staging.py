"""
Finds the repo root.
Reads app.py.
Stores it in the object store.
Compares it against the latest committed version.
Creates a staged entry in .neuralcommit/staging/index.json.

"""
from __future__ import annotations
from pathlib import Path
from storage.object_store import ObjectStore
from cli.repo import nc_path, read_json, write_json


def summarize_change(path: str, status: str, diff_text: str) -> str: #status (added, modified, deleted)
    added = sum(1 for line in diff_text.splitlines() if line.startswith("+") and not line.startswith("+++")) #splitlines turns diff_text into a list therefore sum([1,1,1]) = 3
    removed = sum(1 for line in diff_text.splitlines() if line.startswith("-") and not line.startswith("---"))
    return f"{status} {path}: +{added}/-{removed} lines"