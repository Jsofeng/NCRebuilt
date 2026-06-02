import os
from pathlib import Path
from typing import Optional #Used for a parameter that may be either a string or missing:

import typer #Typer turns Python functions into CLI commands.


from cli.repo import ( nc_path, write_json, read_json, find_repo, load_config )
from storage.commit_graph import CommitGraph
from storage.vector_index import VectorIndex
from storage.object_store import ObjectStore
from cli.staging import stage_files
from cli.diff import annotate_diff, diff_against_snapshot
from cli.commit import create_commit
from cli.push import push as run_push
"""
NeuralCommit Workflow

working file -> object store -> staging/index.json
staging/index.json -> commits.db -> permanent history
commits.db -> terminal output

"""

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

    """
    User types nc add
            ↓
        find repo
            ↓
    load commit history
            ↓
    load object storage
            ↓
        stage files
            ↓
     print summaries
        
    """

    @app.command()
    def add(files: list[str]):
        repo = find_repo() #finds root repo e.g (if this was where .neuralcommit was found project/.neuralcommit -> returns project/)
        graph = CommitGraph(nc_path(repo) / "commits.db") 
        store = ObjectStore(nc_path(repo))
        staged = stage_files(repo, files, graph.latest_snapshot, store)

        for item in staged:
            typer.echo(item["summary"]) #prints out all new changes added/modified/removed

    
        """
            nc diff
                ↓
            find_repo()
                ↓
        load commit graph
                ↓
        load object store
                ↓
        read staged files
                ↓
        extract paths
                ↓
    diff_against_snapshot()
                ↓
      load old version
                ↓
      load current version
                ↓
      generate git-style diff
                ↓
        annotate_diff()
            ↓
        scan + and - lines
            ↓
        add AI comments
            ↓
        typer.echo()
            ↓
        print result


        Take staged file list
                ↓
        For each staged file:
        compare committed version
                vs
        current working version

        """

    @app.command()
    def diff():
        repo = find_repo()
        graph = CommitGraph(nc_path(repo) / "commits.db")
        store = ObjectStore(nc_path(repo))
        staged = read_json(nc_path(repo) / "staging" / "index.json", [])
        paths = [item["path"] for item in staged] #extracts only paths from the CURRENT list of paths from STAGED and other stuff from staging

        typer.echo(
            annotate_diff(
                diff_against_snapshot(repo, graph.latest_snapshot, store, paths) #ts function compares current staged with previous committed files with the same file
            )
        )

    @app.command()
    def commit(no_ai: bool = typer.Option(False, "--no-ai", help="Skip AI assist for this command.")):
        repo = find_repo()
        config = load_config(repo)
        result = create_commit(repo, config.get("author", "unknown"), no_ai=no_ai)
         
        typer.echo(f"[{result['id']}] {result['message']}")
        typer.echo(result["summary"])

    @app.command()
    def log(limit: int = 20):
        repo = find_repo()
        graph = CommitGraph(nc_path(repo) / "commits.db")

        for item in graph.list_commits():
            typer.echo(f"{item['id']} score={item['score']} {item['created_at']}")
            typer.echo(f"  {item['message']}")
            typer.echo(f"  {item['summary']}")

    @app.command()
    def push(no_ai: bool = typer.Option(False, "--no-ai", help="Skip external AI calls")):
        repo = find_repo()
        result = run_push(repo, no_ai=no_ai)
        typer.echo(f"Pushed {result['commit_id']} with AI score {result['score']}")
