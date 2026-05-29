import os
from pathlib import Path
from typing import Optional #Used for a parameter that may be either a string or missing:

import typer #Typer turns Python functions into CLI commands.


from cli.repo import nc_path, write_json
from storage.commit_graph import CommitGraph
from storage.vector_index import VectorIndex
from storage.object_store import ObjectStore

def main():
    app = typer.Typer(help="NeuralCommit: AI-native version control.") # When a user runs python main.py --help that msg will show up

    @app.command()
    def init(name: Optional[str] = typer.Option(None, help="Repository name")): #nc init --name <project_name>
        repo = Path.cwd()
        root = nc_path(repo)

        for child in ["objects", "staging", "vectors"]: #auto creates these 3 directories
            (root / child).mkdir(parents=True, exist_ok=True)

        config = {
            "repo_name": name or repo.name,
            "remote_url": "",
            "author": os.getenv("USER") or os.getenv("USERNAME") or "unknown",
            "ai": {
                "model": "claude-sonnet-4-20250514",
                "steps": [
                    "diff_analyzer",
                    "bug_scanner",
                    "refactor_suggester",
                    "pr_summary",
                    "commit_scorer",
                ],
                "severity_threshold": "HIGH",
            },
        }
        write_json(root / "config.json", config)
        write_json(root / "staging" / "index.json", []) #empty staging area
        CommitGraph(root / "commits.db")
        VectorIndex(root / "vector_index.db")
        typer.echo(f"Initialized NeuralCommit repository in {root}")

    @app.command()
    def add(files: list[str]):
        pass


    
    #TBC...

