"""Simple test script for MCP tools."""

import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from storage.db import init_db, search_memories, add_memory
from models import MemorySearchInput, MemoryAddInput


async def test_search():
    """Test memory_search tool."""
    print("=" * 50)
    print("Test 1: Search memories")
    print("=" * 50)
    
    await init_db()
    
    # Test search for "目标"
    results = await search_memories(query="目标", limit=5)
    print(f"Found {len(results)} results for '目标':")
    for r in results:
        print(f"  - {r['title']}: {r['content'][:50]}...")
    
    print("\n")


async def test_add():
    """Test memory_add tool."""
    print("=" * 50)
    print("Test 2: Add memory")
    print("=" * 50)
    
    import uuid
    memory_id = str(uuid.uuid4())
    
    entry = await add_memory(
        memory_id=memory_id,
        category="test",
        title="测试记忆",
        content="这是一个测试记忆条目",
        importance=3,
        source_type="manual"
    )
    
    print(f"Added memory: {entry['id']}")
    print(f"  Title: {entry['title']}")
    print(f"  Content: {entry['content']}")
    print("\n")
    
    # Search for it
    results = await search_memories(query="测试", limit=5)
    print(f"Found {len(results)} results for '测试':")
    for r in results:
        print(f"  - {r['title']}: {r['content']}")


async def main():
    """Run all tests."""
    await test_search()
    await test_add()
    print("=" * 50)
    print("All tests completed!")
    print("=" * 50)


if __name__ == "__main__":
    asyncio.run(main())
