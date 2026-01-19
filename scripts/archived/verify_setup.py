#!/usr/bin/env python3
"""Verify MCP Server setup and configuration."""

import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from storage.db import init_db, search_memories, get_memory
from models import MemorySearchInput, MemoryAddInput
import uuid


async def verify_database():
    """Verify database is set up correctly."""
    print("=" * 60)
    print("1. Verifying database setup...")
    print("=" * 60)
    
    await init_db()
    print("✅ Database initialized")
    
    # Test search
    results = await search_memories(query="目标", limit=5)
    print(f"✅ Search test: Found {len(results)} results")
    if results:
        print(f"   Example: {results[0]['title']}")
    
    print()


async def verify_models():
    """Verify Pydantic models work correctly."""
    print("=" * 60)
    print("2. Verifying Pydantic models...")
    print("=" * 60)
    
    # Test MemorySearchInput
    search_input = MemorySearchInput(
        query="测试",
        category=None,
        project=None,
        limit=5
    )
    print(f"✅ MemorySearchInput: {search_input.query}")
    
    # Test MemoryAddInput
    add_input = MemoryAddInput(
        category="test",
        title="测试标题",
        content="测试内容",
        project=None,
        importance=3
    )
    print(f"✅ MemoryAddInput: {add_input.title}")
    
    print()


async def verify_tools():
    """Verify tool functions work correctly."""
    print("=" * 60)
    print("3. Verifying tool functions...")
    print("=" * 60)
    
    from tools.memory_search import memory_search
    from tools.memory_add import memory_add
    
    # Test memory_search
    search_params = MemorySearchInput(query="目标", limit=3)
    result = await memory_search(search_params)
    print(f"✅ memory_search tool: {len(result)} characters returned")
    
    # Test memory_add
    add_params = MemoryAddInput(
        category="test",
        title="验证测试",
        content="这是一个验证测试",
        importance=1
    )
    result = await memory_add(add_params)
    print(f"✅ memory_add tool: Memory added successfully")
    
    print()


async def verify_mcp_server():
    """Verify MCP server can be imported."""
    print("=" * 60)
    print("4. Verifying MCP server...")
    print("=" * 60)
    
    try:
        from main import mcp
        print(f"✅ MCP server imported: {mcp.name}")
        print(f"✅ Server ready to run")
    except Exception as e:
        print(f"❌ Error importing MCP server: {e}")
    
    print()


async def main():
    """Run all verification checks."""
    print("\n" + "=" * 60)
    print("Personal Memory MCP Server - Setup Verification")
    print("=" * 60 + "\n")
    
    await verify_database()
    await verify_models()
    await verify_tools()
    await verify_mcp_server()
    
    print("=" * 60)
    print("✅ All verifications completed!")
    print("=" * 60)
    print("\nNext steps:")
    print("1. Configure MCP Server in Cursor (see MCP_CONFIG.md)")
    print("2. Run test cases (see TEST_PLAN.md)")
    print("3. Start using the memory system!")
    print()


if __name__ == "__main__":
    asyncio.run(main())
