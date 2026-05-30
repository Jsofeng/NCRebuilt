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
from cli.diff import diff_against_snapshot


def summarize_change(path: str, status: str, diff_text: str) -> str: #status (added, modified, deleted)
    added = sum(1 for line in diff_text.splitlines() if line.startswith("+") and not line.startswith("+++")) #splitlines turns diff_text into a list therefore sum([1,1,1]) = 3
    removed = sum(1 for line in diff_text.splitlines() if line.startswith("-") and not line.startswith("---"))
    return f"{status} {path}: +{added}/-{removed} lines"

"""
#files (the files that the user wants to stage) 
#snapshot (latest committed files)

stage_files functionality: Takes files → checks them → stores their content → computes diff → saves them into a staging index → returns staged files

line 41: staged = [
    {"path": "a.txt", "blob_sha": "123"},
    {"path": "b.txt", "blob_sha": "456"}
]

line 58: 
by_path = {
    "a.txt": {"path": "a.txt", "blob_sha": "123"},
    "b.txt": {"path": "b.txt", "blob_sha": "456"}
}

"""
def stage_files(repo: Path, files: tuple[str, ...], snapshot: dict[str, str], store: ObjectStore) -> list[dict[str,str]]: 
    staged = read_json(nc_path(repo) / "staging" / "index.json", []) #returns a list of all staged files
    by_path = {item["path"]: item for item in staged} #turns the list into a dict if the same files are staged the most recent one replaces the old one

    for raw in files:
        path = (repo / raw).resolve() #Build the absolute path.

        if not path.exists() or not path.is_file():
            raise FileNotFoundError(f"cannot stage missing file: {raw}")

        rel = path.relative_to(repo).as_posix() # A commit should store the relative path -> "as_posix" Converts the path separators to POSIX format (forward slashes /

        if rel.startswith(".neuralcommit/"):
            continue

        blob = store.put_file(path)
        status = "modified" if rel in snapshot else "added" #If the file path exists in the latest commit snapshot, it is modified.
        diff_text = diff_against_snapshot(repo, snapshot, store, [rel])

        by_path[rel] = {
            "path": rel,
            "blob_sha": blob,
            "status": status,
            "summary": summarize_change(rel, status, diff_text),
        }

        result = list(by_path.values())
        write_json(nc_path(repo) / "staging" / "index.json", result)
        return result
    
    
def clear_stage(repo: Path) -> None: #clears the staging area after committed
    write_json(nc_path(repo) / "staging" / "index.json", []) 