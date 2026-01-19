"""Project management operations for personal memory system."""

import aiosqlite
import json
import os
from datetime import datetime
from typing import List, Optional
from pathlib import Path

from storage.db import DB_PATH

PROJECTS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "projects")


async def create_project(
    project_id: str,
    name: str,
    description: str,
    baseline_doc: Optional[str] = None,
    status: str = "active"
) -> dict:
    """Create a new project."""
    Path(PROJECTS_DIR).mkdir(parents=True, exist_ok=True)
    
    now = datetime.now().isoformat()
    
    project_data = {
        "id": project_id,
        "name": name,
        "description": description,
        "baseline_doc": baseline_doc,
        "status": status,
        "created_at": now,
        "updated_at": now
    }
    
    # Save project JSON file
    project_file = os.path.join(PROJECTS_DIR, f"{project_id}.json")
    with open(project_file, "w", encoding="utf-8") as f:
        json.dump(project_data, f, ensure_ascii=False, indent=2)
    
    # Save baseline doc if provided
    if baseline_doc:
        baseline_file = os.path.join(PROJECTS_DIR, f"{project_id}_baseline.md")
        with open(baseline_file, "w", encoding="utf-8") as f:
            f.write(baseline_doc)
        project_data["baseline_path"] = baseline_file
    
    # Insert into database
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            INSERT INTO projects (id, name, description, baseline_doc, status, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            project_id, name, description, baseline_doc, status, now, now
        ))
        await db.commit()
    
    return project_data


async def get_project(project_id: str) -> Optional[dict]:
    """Get project by ID."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT * FROM projects WHERE id = ?",
            (project_id,)
        )
        row = await cursor.fetchone()
        
        if row:
            return dict(row)
        return None


async def get_project_by_name(name: str) -> Optional[dict]:
    """Get project by name."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT * FROM projects WHERE name = ?",
            (name,)
        )
        row = await cursor.fetchone()
        
        if row:
            return dict(row)
        return None


async def list_projects(status: Optional[str] = None) -> List[dict]:
    """List all projects, optionally filtered by status."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        
        if status:
            cursor = await db.execute(
                "SELECT * FROM projects WHERE status = ? ORDER BY created_at DESC",
                (status,)
            )
        else:
            cursor = await db.execute(
                "SELECT * FROM projects ORDER BY created_at DESC"
            )
        
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]


async def get_project_memories(
    project_name: str,
    limit: int = 5
) -> List[dict]:
    """Get recent memories for a project."""
    from storage.db import search_memories
    
    # First, try to find project by name
    project = await get_project_by_name(project_name)
    if not project:
        return []
    
    # Search memories for this project
    results = await search_memories(
        query="",
        project=project_name,
        limit=limit
    )
    
    return results


async def get_project_baseline(project_name: str) -> Optional[str]:
    """Get project baseline document."""
    project = await get_project_by_name(project_name)
    if not project or not project.get("baseline_doc"):
        return None
    
    baseline_path = os.path.join(PROJECTS_DIR, f"{project['id']}_baseline.md")
    if os.path.exists(baseline_path):
        with open(baseline_path, "r", encoding="utf-8") as f:
            return f.read()
    
    return project.get("baseline_doc")
