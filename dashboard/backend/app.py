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


@app.get("/api/commits")
def commits():
    rows = graph().list_commits(100)
    # **row Take all key-value pairs from this dictionary and copy them here
    return [
        {
            **row, 
            "reports": json.loads(row.get("report_json") or "{}"),
        }
        for row in rows
    ]


@app.get("api/health")
def health():
    rows = list(reversed(graph().list_commits(100))) #list_commits returns newest commits but we want oldest -> newest
    points = [
        {
            "id": row["id"],
            "score": row["score"],
            "created_at": row["created_at"]
        }
        for row in rows
    ]
    average = round(sum(point["score"] for point in points) / len(points), 1) if points else 0 #If there are commits, calculate average score. 
    return {"average": average, "points": points}


@app.get("api/security-alerts")
def security_alerts():
    alerts = []
    for row in graph().list_commits(100):
        report = json.loads(row.get("report_json") or "{}") #Parse AI report JSON.
        for finding in report.get("bug_scanner", {}).get("findings", []): #Safely get bug_scanner[findings]
            if finding.get("severity") in {"HIGH", "CRITICAL"}:
                alerts.append({"commit_id": row["id"], **finding}) #append the commit_id and the entire finding dict for that commit_id
    
    return alerts


