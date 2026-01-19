"""Debug FTS5 table."""

import asyncio
import aiosqlite

async def debug():
    async with aiosqlite.connect("memory.db") as db:
        db.row_factory = aiosqlite.Row
        
        print("=== Memories table ===")
        cursor = await db.execute("SELECT id, title FROM memories LIMIT 5")
        rows = await cursor.fetchall()
        for row in rows:
            print(f"{row['id']}: {row['title']}")
        
        print("\n=== FTS5 table ===")
        cursor = await db.execute("SELECT id, title FROM memories_fts LIMIT 5")
        rows = await cursor.fetchall()
        for row in rows:
            print(f"{row['id']}: {row['title']}")
        
        print("\n=== FTS5 search test ===")
        cursor = await db.execute("SELECT id, title FROM memories_fts WHERE memories_fts MATCH '目标'")
        rows = await cursor.fetchall()
        for row in rows:
            print(f"Found: {row['id']}: {row['title']}")

asyncio.run(debug())
