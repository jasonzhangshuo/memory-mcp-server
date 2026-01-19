#!/usr/bin/env python3
"""Performance testing script for memory search."""

import asyncio
import time
import sys
import uuid
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from storage.db import init_db, search_memories, add_memory


async def measure_search_time(query: str, category: str = None, project: str = None, limit: int = 5) -> tuple:
    """Measure search execution time."""
    start_time = time.time()
    results = await search_memories(query=query, category=category, project=project, limit=limit)
    elapsed_time = (time.time() - start_time) * 1000  # Convert to milliseconds
    return elapsed_time, len(results)


async def test_different_query_lengths():
    """Test performance with different query lengths."""
    print("\n[性能测试] 不同查询长度")
    print("-" * 70)
    
    queries = [
        ("目标", "1字查询"),
        ("退休", "1字查询"),
        ("50岁退休", "3字查询"),
        ("核心目标：50岁退休", "7字查询"),
        ("为50岁退休做好身体与精神的双重准备", "15字查询"),
    ]
    
    results = []
    for query, desc in queries:
        elapsed, count = await measure_search_time(query)
        results.append((desc, elapsed, count))
        status = "✅" if elapsed < 500 else "⚠️"
        print(f"{status} {desc}: {elapsed:.2f}ms (找到 {count} 条)")
    
    return results


async def test_with_filters():
    """Test performance with category and project filters."""
    print("\n[性能测试] 带过滤的查询")
    print("-" * 70)
    
    tests = [
        ("目标", "goal", None, "类别过滤"),
        ("", "goal", None, "仅类别过滤"),
        ("测试", None, "测试项目", "项目过滤"),
        ("", None, "测试项目", "仅项目过滤"),
    ]
    
    results = []
    for query, category, project, desc in tests:
        elapsed, count = await measure_search_time(query, category, project)
        results.append((desc, elapsed, count))
        status = "✅" if elapsed < 500 else "⚠️"
        print(f"{status} {desc}: {elapsed:.2f}ms (找到 {count} 条)")
    
    return results


async def test_with_different_data_sizes():
    """Test performance with different data sizes."""
    print("\n[性能测试] 不同数据量")
    print("-" * 70)
    
    # Get current data count
    current_results = await search_memories("", limit=1000)
    current_count = len(current_results)
    print(f"当前数据量: {current_count} 条")
    
    # Test with current data
    elapsed, count = await measure_search_time("目标", limit=10)
    status = "✅" if elapsed < 500 else "⚠️"
    print(f"{status} 当前数据量搜索: {elapsed:.2f}ms (找到 {count} 条)")
    
    # Add more test data to simulate larger dataset
    print("\n添加测试数据以模拟更大数据集...")
    for i in range(50):
        await add_memory(
            memory_id=str(uuid.uuid4()),
            category="test",
            title=f"测试记忆 {i}",
            content=f"这是第 {i} 条测试记忆，用于性能测试。包含一些关键词如目标、计划、执行等。",
            importance=2,
            source_type="manual"
        )
    
    # Test again
    elapsed, count = await measure_search_time("目标", limit=10)
    status = "✅" if elapsed < 500 else "⚠️"
    print(f"{status} 增加数据后搜索: {elapsed:.2f}ms (找到 {count} 条)")
    
    return elapsed < 500


async def test_sorting_performance():
    """Test sorting performance."""
    print("\n[性能测试] 排序性能")
    print("-" * 70)
    
    # Test with different limits
    limits = [5, 10, 20, 50]
    results = []
    for limit in limits:
        elapsed, count = await measure_search_time("", limit=limit)
        results.append((limit, elapsed, count))
        status = "✅" if elapsed < 500 else "⚠️"
        print(f"{status} limit={limit}: {elapsed:.2f}ms (返回 {count} 条)")
    
    return results


async def test_empty_query_performance():
    """Test empty query performance."""
    print("\n[性能测试] 空查询性能")
    print("-" * 70)
    
    elapsed, count = await measure_search_time("", limit=10)
    status = "✅" if elapsed < 500 else "⚠️"
    print(f"{status} 空查询: {elapsed:.2f}ms (返回 {count} 条)")
    
    return elapsed < 500


async def run_performance_tests():
    """Run all performance tests."""
    print("=" * 70)
    print("性能测试 - 目标: 检索延迟 <500ms")
    print("=" * 70)
    
    await init_db()
    
    # Run all tests
    test_results = []
    
    query_length_results = await test_different_query_lengths()
    test_results.extend([r[1] < 500 for r in query_length_results])
    
    filter_results = await test_with_filters()
    test_results.extend([r[1] < 500 for r in filter_results])
    
    data_size_ok = await test_with_different_data_sizes()
    test_results.append(data_size_ok)
    
    sorting_results = await test_sorting_performance()
    test_results.extend([r[1] < 500 for r in sorting_results])
    
    empty_query_ok = await test_empty_query_performance()
    test_results.append(empty_query_ok)
    
    # Summary
    print("\n" + "=" * 70)
    print("性能测试结果汇总")
    print("=" * 70)
    passed = sum(test_results)
    total = len(test_results)
    print(f"通过 (<500ms): {passed}/{total} ({passed*100//total if total > 0 else 0}%)")
    
    if passed == total:
        print("\n🎉 所有性能测试通过！检索延迟均 <500ms")
    else:
        print(f"\n⚠️  {total - passed} 个测试超过 500ms，需要优化")
    
    # Calculate average
    all_times = [r[1] for r in query_length_results] + [r[1] for r in filter_results] + [r[1] for r in sorting_results]
    if all_times:
        avg_time = sum(all_times) / len(all_times)
        max_time = max(all_times)
        min_time = min(all_times)
        print(f"\n平均延迟: {avg_time:.2f}ms")
        print(f"最大延迟: {max_time:.2f}ms")
        print(f"最小延迟: {min_time:.2f}ms")


if __name__ == "__main__":
    asyncio.run(run_performance_tests())
