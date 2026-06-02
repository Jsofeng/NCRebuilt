from __future__ import annotations

from pathlib import Path
from cli.repo import nc_path
from storage.commit_graph import CommitGraph

def push(repo: Path, no_ai: bool = False) -> dict:
    graph = CommitGraph(nc_path(repo) / "commits.db")

    head = graph.head()

    if not head:
        raise ValueError("nothing to push")
    
    commit = graph.get_commit(head)

    assert commit is not None

    #tbc - agentic pipeline

    
    
