"""SQLite database operations for personal memory system."""

import aiosqlite
import json
import os
import sys
from datetime import datetime
from typing import List, Optional
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Import configuration
from config import get_db_path, get_entries_dir, is_test_mode

# Database file path (from config)
DB_PATH = get_db_path()
ENTRIES_DIR = get_entries_dir()


async def init_db():
    """Initialize database and entries directory."""
    # Create entries directory structure
    Path(ENTRIES_DIR).mkdir(parents=True, exist_ok=True)
    
    async with aiosqlite.connect(DB_PATH) as db:
        # Create main table
        await db.execute("""
            CREATE TABLE IF NOT EXISTS memories (
                id TEXT PRIMARY KEY,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                category TEXT NOT NULL,
                tags TEXT,
                title TEXT NOT NULL,
                content TEXT NOT NULL,
                project TEXT,
                importance INTEGER NOT NULL,
                archived INTEGER NOT NULL DEFAULT 0,
                source_type TEXT NOT NULL,
                source_timestamp TEXT NOT NULL,
                entry_path TEXT NOT NULL
            )
        """)
        
        # Create FTS5 virtual table for full-text search
        # Use simple FTS5 without content option for Phase 0
        await db.execute("""
            CREATE VIRTUAL TABLE IF NOT EXISTS memories_fts USING fts5(
                id UNINDEXED,
                title,
                content,
                category,
                project
            )
        """)
        
        # Create index for faster queries
        await db.execute("""
            CREATE INDEX IF NOT EXISTS idx_category ON memories(category)
        """)
        await db.execute("""
            CREATE INDEX IF NOT EXISTS idx_project ON memories(project)
        """)
        await db.execute("""
            CREATE INDEX IF NOT EXISTS idx_created_at ON memories(created_at)
        """)
        
        # Create projects table
        await db.execute("""
            CREATE TABLE IF NOT EXISTS projects (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL UNIQUE,
                description TEXT,
                baseline_doc TEXT,
                status TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)
        
        await db.execute("""
            CREATE INDEX IF NOT EXISTS idx_project_status ON projects(status)
        """)
        
        # Create memory_tags table for tag indexing
        await db.execute("""
            CREATE TABLE IF NOT EXISTS memory_tags (
                memory_id TEXT NOT NULL,
                tag TEXT NOT NULL,
                PRIMARY KEY (memory_id, tag),
                FOREIGN KEY (memory_id) REFERENCES memories(id) ON DELETE CASCADE
            )
        """)
        
        await db.execute("""
            CREATE INDEX IF NOT EXISTS idx_tag ON memory_tags(tag)
        """)
        
        await db.commit()
        
        # Migrate existing tags from JSON to memory_tags table
        await migrate_tags_to_table()


async def migrate_tags_to_table():
    """Migrate existing tags from memories.tags JSON to memory_tags table."""
    async with aiosqlite.connect(DB_PATH) as db:
        # Check if migration is needed
        cursor = await db.execute("SELECT COUNT(*) FROM memory_tags")
        tag_count = (await cursor.fetchone())[0]
        
        if tag_count > 0:
            # Tags already migrated
            return
        
        # Get all memories with tags
        cursor = await db.execute("SELECT id, tags FROM memories WHERE tags IS NOT NULL AND tags != '[]' AND tags != ''")
        rows = await cursor.fetchall()
        
        for row in rows:
            memory_id = row[0]
            tags_json = row[1]
            
            try:
                tags = json.loads(tags_json) if tags_json else []
                if tags:
                    # Insert tags into memory_tags table
                    for tag in tags:
                        if tag:  # Skip empty tags
                            try:
                                await db.execute(
                                    "INSERT OR IGNORE INTO memory_tags (memory_id, tag) VALUES (?, ?)",
                                    (memory_id, tag)
                                )
                            except Exception:
                                # Skip duplicate or invalid tags
                                pass
            except (json.JSONDecodeError, TypeError):
                # Skip invalid JSON
                continue
        
        await db.commit()


def _is_chinese_text(text: str) -> bool:
    """Check if text contains Chinese characters."""
    return any('\u4e00' <= char <= '\u9fff' for char in text)


async def search_memories(
    query: str,
    category: Optional[str] = None,
    project: Optional[str] = None,
    tags: Optional[List[str]] = None,
    limit: int = 5
) -> List[dict]:
    """Search memories using FTS5 full-text search with fallback to LIKE for Chinese."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        
        # Build conditions and parameters
        conditions = []
        params = []
        
        # Determine search method: FTS5 for English/mixed, LIKE for Chinese
        use_fts = False
        if query and query.strip():
            query_clean = query.strip()
            # Use FTS5 for English or mixed queries, LIKE for pure Chinese
            # FTS5 works better for English, LIKE works better for Chinese
            if _is_chinese_text(query_clean):
                # Chinese text: use LIKE (more reliable for Chinese)
                # For multi-word Chinese queries, search for each word
                if ' ' in query_clean:
                    # Multi-word: search for any word (OR logic)
                    words = query_clean.split()
                    word_conditions = []
                    for word in words:
                        word_pattern = f"%{word}%"
                        word_conditions.append("(m.title LIKE ? OR m.content LIKE ?)")
                        params.extend([word_pattern, word_pattern])
                    conditions.append(f"({' OR '.join(word_conditions)})")
                else:
                    # Single word
                    query_pattern = f"%{query_clean}%"
                    conditions.append("(m.title LIKE ? OR m.content LIKE ?)")
                    params.extend([query_pattern, query_pattern])
            else:
                # English or mixed: use FTS5
                # For multi-word queries, use AND to connect
                if ' ' in query_clean:
                    words = query_clean.split()
                    fts_query = " AND ".join(words)
                else:
                    fts_query = query_clean
                
                conditions.append("memories_fts MATCH ?")
                params.append(fts_query)
                use_fts = True
        
        # Add filters
        if category:
            conditions.append("m.category = ?")
            params.append(category)
        
        if project:
            conditions.append("m.project = ?")
            params.append(project)
        
        conditions.append("m.archived = 0")
        
        # Handle tags filter (AND logic - all tags must match)
        tag_joins = ""
        tag_conditions = ""
        if tags and len(tags) > 0:
            # Join memory_tags table for each tag
            tag_joins = " ".join([
                f"INNER JOIN memory_tags mt{i} ON m.id = mt{i}.memory_id"
                for i in range(len(tags))
            ])
            tag_conditions = " AND ".join([
                f"mt{i}.tag = ?"
                for i in range(len(tags))
            ])
            params.extend(tags)
        
        where_clause = " AND ".join(conditions)
        if tag_conditions:
            where_clause = f"{where_clause} AND {tag_conditions}"
        
        # Build SQL query
        if use_fts:
            # Search using FTS5 with JOIN to main table
            sql = f"""
                SELECT DISTINCT m.* FROM memories m
                JOIN memories_fts ON m.id = memories_fts.id
                {tag_joins}
                WHERE {where_clause}
                ORDER BY m.importance DESC, m.created_at DESC
                LIMIT ?
            """
        else:
            # Search main table directly (LIKE or empty query)
            sql = f"""
                SELECT DISTINCT m.* FROM memories m
                {tag_joins}
                WHERE {where_clause}
                ORDER BY m.importance DESC, m.created_at DESC
                LIMIT ?
            """
        
        params.append(limit)
        
        cursor = await db.execute(sql, params)
        rows = await cursor.fetchall()
        
        # Load full content from JSON files
        results = []
        for row in rows:
            entry_path = row["entry_path"]
            if os.path.exists(entry_path):
                with open(entry_path, "r", encoding="utf-8") as f:
                    entry_data = json.load(f)
                    results.append(entry_data)
        
        return results


async def get_memory(memory_id: str) -> Optional[dict]:
    """Get a single memory by ID."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT entry_path FROM memories WHERE id = ?",
            (memory_id,)
        )
        row = await cursor.fetchone()
        
        if row and os.path.exists(row["entry_path"]):
            with open(row["entry_path"], "r", encoding="utf-8") as f:
                return json.load(f)
        
        return None


async def add_memory(
    memory_id: str,
    category: str,
    title: str,
    content: str,
    project: Optional[str] = None,
    importance: int = 3,
    source_type: str = "claude_ai",
    tags: List[str] = None
) -> dict:
    """Add a new memory entry."""
    if tags is None:
        tags = []
    
    now = datetime.now().isoformat()
    
    # Create entry data
    entry_data = {
        "id": memory_id,
        "created_at": now,
        "updated_at": now,
        "category": category,
        "tags": tags,
        "title": title,
        "content": content,
        "project": project,
        "importance": importance,
        "archived": False,
        "source": {
            "type": source_type,
            "timestamp": now
        }
    }
    
    # Save to JSON file
    year_month = datetime.now().strftime("%Y/%m")
    entry_dir = os.path.join(ENTRIES_DIR, year_month)
    Path(entry_dir).mkdir(parents=True, exist_ok=True)
    
    entry_path = os.path.join(entry_dir, f"{memory_id}.json")
    with open(entry_path, "w", encoding="utf-8") as f:
        json.dump(entry_data, f, ensure_ascii=False, indent=2)
    
    # Insert into database
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            INSERT INTO memories (
                id, created_at, updated_at, category, tags, title, content,
                project, importance, archived, source_type, source_timestamp, entry_path
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            memory_id, now, now, category, json.dumps(tags), title, content,
            project, importance, 0, source_type, now, entry_path
        ))
        
        # Insert into FTS5
        await db.execute("""
            INSERT INTO memories_fts (id, title, content, category, project)
            VALUES (?, ?, ?, ?, ?)
        """, (memory_id, title, content, category, project))
        
        # Insert tags into memory_tags table
        if tags:
            for tag in tags:
                if tag:  # Skip empty tags
                    await db.execute(
                        "INSERT OR IGNORE INTO memory_tags (memory_id, tag) VALUES (?, ?)",
                        (memory_id, tag)
                    )
        
        await db.commit()
    
    return entry_data


async def list_tags(project: Optional[str] = None) -> List[dict]:
    """List all tags with their usage counts.
    
    Args:
        project: Optional project filter
    
    Returns:
        List of dicts with 'name' and 'count' keys
    """
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        
        if project:
            # Filter by project
            sql = """
                SELECT mt.tag as name, COUNT(DISTINCT mt.memory_id) as count
                FROM memory_tags mt
                INNER JOIN memories m ON mt.memory_id = m.id
                WHERE m.project = ? AND m.archived = 0
                GROUP BY mt.tag
                ORDER BY count DESC, mt.tag ASC
            """
            cursor = await db.execute(sql, (project,))
        else:
            # All tags
            sql = """
                SELECT mt.tag as name, COUNT(DISTINCT mt.memory_id) as count
                FROM memory_tags mt
                INNER JOIN memories m ON mt.memory_id = m.id
                WHERE m.archived = 0
                GROUP BY mt.tag
                ORDER BY count DESC, mt.tag ASC
            """
            cursor = await db.execute(sql)
        
        rows = await cursor.fetchall()
        
        return [{"name": row["name"], "count": row["count"]} for row in rows]
