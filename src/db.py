"""Datenbank — SQLite-basierte Workflow-Template-Verwaltung."""

import sqlite3
import json
import os
from datetime import datetime, timezone
from pathlib import Path

_DB_PATH = os.getenv("WORKFLOW_DB_PATH", str(Path(__file__).resolve().parent.parent / "workflows.db"))


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(_DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("""
        CREATE TABLE IF NOT EXISTS workflows (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            description TEXT NOT NULL,
            category TEXT NOT NULL,
            steps TEXT NOT NULL,
            required_tools TEXT,
            input_schema TEXT,
            output_schema TEXT,
            author TEXT,
            tags TEXT,
            uses INTEGER DEFAULT 0,
            avg_rating REAL DEFAULT 0,
            total_ratings INTEGER DEFAULT 0,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS workflow_ratings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            workflow_name TEXT NOT NULL,
            rating INTEGER NOT NULL CHECK(rating BETWEEN 1 AND 5),
            review TEXT,
            created_at TEXT NOT NULL
        )
    """)
    conn.commit()
    return conn


def create_workflow(
    name: str, description: str, category: str, steps: list[dict],
    required_tools: list[str] = None, input_schema: dict = None,
    output_schema: dict = None, author: str = None, tags: list[str] = None,
) -> dict:
    conn = _connect()
    now = datetime.now(timezone.utc).isoformat()
    conn.execute(
        """INSERT INTO workflows (name, description, category, steps,
           required_tools, input_schema, output_schema, author, tags,
           created_at, updated_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
           ON CONFLICT(name) DO UPDATE SET
               description=excluded.description, steps=excluded.steps,
               required_tools=excluded.required_tools, updated_at=excluded.updated_at""",
        (name, description, category, json.dumps(steps),
         json.dumps(required_tools) if required_tools else None,
         json.dumps(input_schema) if input_schema else None,
         json.dumps(output_schema) if output_schema else None,
         author, json.dumps(tags) if tags else None, now, now),
    )
    conn.commit()
    conn.close()
    return {"name": name, "created": True}


def get_workflow(name: str) -> dict | None:
    conn = _connect()
    conn.execute("UPDATE workflows SET uses = uses + 1 WHERE name=?", (name,))
    conn.commit()
    row = conn.execute("SELECT * FROM workflows WHERE name=?", (name,)).fetchone()
    conn.close()
    if not row:
        return None
    d = dict(row)
    for field in ["steps", "required_tools", "input_schema", "output_schema", "tags"]:
        d[field] = json.loads(d[field]) if d[field] else None
    return d


def search_workflows(query: str = None, category: str = None, limit: int = 20) -> list:
    conn = _connect()
    sql = "SELECT * FROM workflows WHERE 1=1"
    params = []
    if query:
        sql += " AND (name LIKE ? OR description LIKE ? OR tags LIKE ?)"
        params.extend([f"%{query}%"] * 3)
    if category:
        sql += " AND category=?"
        params.append(category)
    sql += " ORDER BY uses DESC LIMIT ?"
    params.append(limit)
    rows = conn.execute(sql, params).fetchall()
    conn.close()
    results = []
    for r in rows:
        d = dict(r)
        for field in ["steps", "required_tools", "tags"]:
            d[field] = json.loads(d[field]) if d[field] else None
        results.append(d)
    return results


def rate_workflow(name: str, rating: int, review: str = None) -> dict:
    conn = _connect()
    now = datetime.now(timezone.utc).isoformat()
    conn.execute(
        "INSERT INTO workflow_ratings (workflow_name, rating, review, created_at) VALUES (?, ?, ?, ?)",
        (name, rating, review, now),
    )
    avg = conn.execute(
        "SELECT AVG(rating) as a, COUNT(*) as c FROM workflow_ratings WHERE workflow_name=?", (name,)
    ).fetchone()
    conn.execute(
        "UPDATE workflows SET avg_rating=?, total_ratings=? WHERE name=?",
        (round(avg["a"], 2), avg["c"], name),
    )
    conn.commit()
    conn.close()
    return {"workflow": name, "rating": rating, "new_avg": round(avg["a"], 2)}


def list_categories() -> list:
    conn = _connect()
    rows = conn.execute(
        "SELECT category, COUNT(*) as count FROM workflows GROUP BY category ORDER BY count DESC"
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_popular(limit: int = 10) -> list:
    conn = _connect()
    rows = conn.execute(
        "SELECT name, category, description, uses, avg_rating FROM workflows ORDER BY uses DESC LIMIT ?",
        (limit,),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]
