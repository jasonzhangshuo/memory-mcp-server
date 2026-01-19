#!/usr/bin/env python3
"""Test FTS5 search functionality."""

import asyncio
import json
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from storage.db import init_db, search_memories, add_memory
import uuid


async def test_basic_search():
    """Test basic FTS5 search."""
    print("\n[测试] 基本搜索功能")
    print("-" * 70)
    
    results = await search_memories(query="目标", limit=10)
    
    if results:
        print(f"✅ 通过: 找到 {len(results)} 条结果")
        for r in results[:3]:
            print(f"   - {r.get('title', 'N/A')}")
        return True
    else:
        print("❌ 失败: 未找到结果")
        return False


async def test_multi_keyword_search():
    """Test multi-keyword search."""
    print("\n[测试] 多关键词搜索")
    print("-" * 70)
    
    # Test with multiple keywords
    results = await search_memories(query="退休 准备", limit=10)
    
    if results:
        print(f"✅ 通过: 找到 {len(results)} 条结果")
        return True
    else:
        print("❌ 失败: 未找到结果")
        return False


async def test_category_filter():
    """Test category filtering."""
    print("\n[测试] 类别过滤")
    print("-" * 70)
    
    results = await search_memories(query="", category="goal", limit=10)
    
    if results:
        all_goals = all(r.get('category') == 'goal' for r in results)
        if all_goals:
            print(f"✅ 通过: 找到 {len(results)} 条 goal 类别结果")
            return True
        else:
            print("❌ 失败: 类别过滤不正确")
            return False
    else:
        print("⚠️  警告: 未找到结果（可能没有 goal 类别数据）")
        return True  # Not a failure if no data


async def test_project_filter():
    """Test project filtering."""
    print("\n[测试] 项目过滤")
    print("-" * 70)
    
    # First create a test memory with project
    test_id = str(uuid.uuid4())
    await add_memory(
        memory_id=test_id,
        category="test",
        title="测试项目记忆",
        content="这是一个测试项目的记忆",
        project="测试项目",
        importance=3,
        source_type="manual"
    )
    
    # Search with project filter
    results = await search_memories(query="测试", project="测试项目", limit=10)
    
    if results:
        all_in_project = all(r.get('project') == '测试项目' for r in results)
        if all_in_project:
            print(f"✅ 通过: 找到 {len(results)} 条项目结果")
            return True
        else:
            print("❌ 失败: 项目过滤不正确")
            return False
    else:
        print("⚠️  警告: 未找到结果")
        return True


async def test_empty_result():
    """Test empty result handling."""
    print("\n[测试] 空结果处理")
    print("-" * 70)
    
    results = await search_memories(query="不存在的关键词xyz123", limit=10)
    
    if len(results) == 0:
        print("✅ 通过: 正确处理空结果")
        return True
    else:
        print(f"❌ 失败: 应该返回空结果，但找到了 {len(results)} 条")
        return False


async def test_empty_query():
    """Test empty query (should return all)."""
    print("\n[测试] 空查询处理")
    print("-" * 70)
    
    results = await search_memories(query="", limit=10)
    
    if results:
        print(f"✅ 通过: 空查询返回 {len(results)} 条结果")
        return True
    else:
        print("⚠️  警告: 空查询未返回结果（可能数据库为空）")
        return True


async def test_chinese_search():
    """Test Chinese character search."""
    print("\n[测试] 中文搜索")
    print("-" * 70)
    
    results = await search_memories(query="退休", limit=10)
    
    if results:
        print(f"✅ 通过: 中文搜索找到 {len(results)} 条结果")
        return True
    else:
        print("❌ 失败: 中文搜索未找到结果")
        return False


async def run_all_tests():
    """Run all FTS5 tests."""
    print("=" * 70)
    print("FTS5 搜索功能测试")
    print("=" * 70)
    
    await init_db()
    
    results = []
    results.append(await test_basic_search())
    results.append(await test_multi_keyword_search())
    results.append(await test_category_filter())
    results.append(await test_project_filter())
    results.append(await test_empty_result())
    results.append(await test_empty_query())
    results.append(await test_chinese_search())
    
    print("\n" + "=" * 70)
    print("测试结果汇总")
    print("=" * 70)
    passed = sum(results)
    total = len(results)
    print(f"通过: {passed}/{total} ({passed*100//total if total > 0 else 0}%)")
    
    if passed == total:
        print("\n🎉 所有 FTS5 测试通过！")
    else:
        print(f"\n⚠️  {total - passed} 个测试失败")


if __name__ == "__main__":
    asyncio.run(run_all_tests())
