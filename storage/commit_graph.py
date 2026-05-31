from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any

"""
Which file used this blob?
Which commit did it belong to?
Who made the commit?
What was the commit message?
What was the previous commit?
"""

#parent_id -> points to the previous commit.



SCHEMA = """
CREATE TABLE IF NOT EXISTS commits (
  id TEXT PRIMARY KEY,
  parent_id TEXT,
  message TEXT NOT NULL,
  summary TEXT NOT NULL,
  diff TEXT NOT NULL,
  author TEXT NOT NULL,
  score INTEGER NOT NULL DEFAULT 0,
  report_json TEXT NOT NULL DEFAULT '{}',
  created_at TEXT NOT NULL    
);

CREATE TABLE IF NOT EXISTS commit_files (
  commit_id TEXT NOT NULL,
  path TEXT NOT NULL,
  blob_sha TEXT NOT NULL,
  status TEXT NOT NULL,
  summary TEXT NOT NULL,
  PRIMARY KEY (commit_id, path)
);
"""


class CommitGraph:
    def __init__(self, db_path: Path):
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        with self.connect() as conn:
            conn.executescript(SCHEMA) # "executescript" lets SQLite run multiple SQL statements at once.

    def connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row #allows rows to behave like dicts (e.g row["id"] row["message"])
        return conn
    
    def head(self) -> str | None:
        with self.connect() as conn:
            row = conn.execute(
            "SELECT id FROM commits ORDER BY created_at DESC LIMIT 1"
        ).fetchone()
            
        return row["id"] if row else None
    
    def get_commit(self, commit_id: str) -> dict[str, Any] | None: #sqlite3 "?" is a placeholder for data -> reducing the risk of sql injection
        with self.connect() as conn:
            row = conn.execute("SELECT * FROM commits WHERE id = ?", (commit_id,)).fetchone()
        if not row:
            return None
        return dict(row) #returns an array of commits with the same commit_id
    
    def latest_snapshot(self) -> dict[str, str]: #return dict bc a commit can have multiple files
        head = self.head() #calls head function to find the latest commit
        if not head:
            return {}
        
        with self.connect() as conn:
            rows = conn.execute(
                "SELECT path, blob_sha FROM commit_files WHERE commit_id = ?",
                (head,)
        ).fetchall() #retrieve all files from the latest commit

        return {row["path"]: row["blob_sha"] for row in rows}
    

    def add_commit(self, commit: dict[str, Any], files: list[dict[str,str]]) -> None: #This inserts: One row into commits, Many rows into commit_files
        with self.connect() as conn:
            conn.execute(
                """
                INSERT INTO commits
                (id, parent_id, message, summary, diff, author, score, report_json, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    commit["id"],
                    commit.get("parent_id"),
                    commit["message"],
                    commit["summary"],
                    commit["diff"],
                    commit["author"],
                    commit.get("score", 0),
                    json.dumps(commit.get("report", {}), sort_keys=True),
                    commit["created_at"],
                ),
            )

            conn.executemany(
                """
                INSERT INTO commit_files (commit_id, path, blob_sha, status, summary)
                VALUES (?, ?, ?, ?, ?)
                """,
                [
                    (
                        commit["id"],
                        item["path"],
                        item["blob_sha"],
                        item["status"],
                        item["summary"],
                    )
                    for item in files
                ],
            )

    def list_commits(self, limit: int = 50) -> list[dict[str, Any]]:
        with self.connect() as conn:
            rows = conn.execute("SELECT * FROM commits ORDER BY created_at DESC LIMIT ?", (limit,)).fetchall() #returns a list of all commits up to set LIMIT from newest
            return [dict(row) for row in rows]
        
    def update_report(self, commit_id: str, report: dict[str, Any], score: int) -> None:
        with self.connect() as conn:
            conn.execute(
            "UPDATE commits SET report_json = ?, score = ? WHERE id = ?",
            (json.dumps(report, sort_keys=True), score, commit_id),
        )
            
    