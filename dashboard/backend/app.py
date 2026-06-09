from __future__ import annotations
import json
import os
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import HTMLResponse

from cli.repo import nc_path
from storage.commit_graph import CommitGraph
from storage.vector_index import VectorIndex #haven't created vector_index yet -> used for /search


"""
SQLite commit data
        ↓
FastAPI backend
        ↓
JSON API
        ↓
browser dashboard
"""

app = FastAPI(title="NeuralCommit Dashboard")

def repo_root() -> Path: #This function figures out which NeuralCommit repo the dashboard should read.
    configured = os.getenv("NEURALCOMMIT_REPO") 
    return Path(configured).resolve() if configured else Path.cwd().resolve() #resolve gives the abspath

def graph() -> CommitGraph: #creates a CommitGraph pointing to the active repo database.
    return CommitGraph(nc_path(repo_root) / "commits.db")


@app.get("/", response_class=HTMLResponse) #When browser requests /, run the next function and return HTML.

def index():
    html = Path(__file__).parents[1] / "frontend" / "index.html" #parents[1] goes up 2 levels from cwd so -> neuralcommit/dashboard/frontend/index.html
    return HTMLResponse(html.read_text(encoding="utf-8")) #Read the HTML file as text and return it as an HTML response.

