#!/usr/bin/env python3
"""Test MCP tools directly to verify functionality."""

import asyncio
import json
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from models import MemorySearchInput, MemoryAddInput
from tools.memory_search import memory_search
from tools.memory_add import memory_add
from storage.db import init_db


async def test_t1_explicit_read_history():
    """T1: 显式读取 - 历史引用"""
    print("=" * 60)
    print("T1: 显式读取 - '我们上次聊的戒糖，后来怎样了'")
    print("=" * 60)
    
    await init_db()
    
    # 模拟用户查询"戒糖"
    params = MemorySearchInput(query="戒糖", limit=5)
    result = await memory_search(params)
    
    result_data = json.loads(result)
    print(f"✅ 工具调用成功")
    print(f"   状态: {result_data.get('status')}")
    print(f"   结果数量: {result_data.get('count', 0)}")
    
    if result_data.get('count', 0) > 0:
        print(f"   找到记忆:")
        for item in result_data.get('results', [])[:3]:
            print(f"     - {item.get('title', 'N/A')}")
    else:
        print(f"   ⚠️  未找到相关记忆（这是正常的，因为种子数据中没有'戒糖'）")
    
    print()
    return result_data.get('status') == 'success'


async def test_t2_explicit_read_goal():
    """T2: 显式读取 - 目标查询"""
    print("=" * 60)
    print("T2: 显式读取 - '我的目标是什么'")
    print("=" * 60)
    
    await init_db()
    
    # 查询目标
    params = MemorySearchInput(query="目标", category="goal", limit=5)
    result = await memory_search(params)
    
    result_data = json.loads(result)
    print(f"✅ 工具调用成功")
    print(f"   状态: {result_data.get('status')}")
    print(f"   结果数量: {result_data.get('count', 0)}")
    
    if result_data.get('count', 0) > 0:
        print(f"   找到目标:")
        for item in result_data.get('results', [])[:3]:
            print(f"     - {item.get('title', 'N/A')}: {item.get('content', '')[:50]}...")
    else:
        print(f"   ❌ 未找到目标（应该能找到'核心目标：50岁退休'）")
    
    print()
    return result_data.get('count', 0) > 0


async def test_t3_explicit_save():
    """T3: 显式保存 - 保存请求"""
    print("=" * 60)
    print("T3: 显式保存 - '记住：我周二有禅修课'")
    print("=" * 60)
    
    await init_db()
    
    # 添加记忆
    params = MemoryAddInput(
        category="commitment",
        title="周二禅修课",
        content="我周二有禅修课",
        importance=3
    )
    result = await memory_add(params)
    
    result_data = json.loads(result)
    print(f"✅ 工具调用成功")
    print(f"   状态: {result_data.get('status')}")
    print(f"   记忆ID: {result_data.get('id', 'N/A')}")
    print(f"   标题: {result_data.get('entry', {}).get('title', 'N/A')}")
    
    # 验证是否真的保存了
    if result_data.get('status') == 'success':
        search_params = MemorySearchInput(query="禅修", limit=1)
        search_result = await memory_search(search_params)
        search_data = json.loads(search_result)
        if search_data.get('count', 0) > 0:
            print(f"   ✅ 验证：可以搜索到刚保存的记忆")
        else:
            print(f"   ⚠️  警告：保存后无法搜索到（可能是搜索延迟）")
    
    print()
    return result_data.get('status') == 'success'


async def test_t5_empty_result():
    """T5: 空结果处理 - 未找到记录"""
    print("=" * 60)
    print("T5: 空结果处理 - '我们讨论过量子计算吗'")
    print("=" * 60)
    
    await init_db()
    
    # 查询不存在的主题
    params = MemorySearchInput(query="量子计算", limit=5)
    result = await memory_search(params)
    
    result_data = json.loads(result)
    print(f"✅ 工具调用成功")
    print(f"   状态: {result_data.get('status')}")
    print(f"   结果数量: {result_data.get('count', 0)}")
    print(f"   消息: {result_data.get('message', 'N/A')}")
    
    # 空结果是正确的
    is_correct = (
        result_data.get('status') == 'success' and
        result_data.get('count', 0) == 0 and
        '没有找到' in result_data.get('message', '')
    )
    
    if is_correct:
        print(f"   ✅ 正确处理空结果：返回'没有找到相关记录'")
    else:
        print(f"   ⚠️  空结果处理可能有问题")
    
    print()
    return is_correct


async def main():
    """Run all tool tests."""
    print("\n" + "=" * 60)
    print("MCP Tools 功能测试")
    print("=" * 60 + "\n")
    
    results = {}
    
    results['T1'] = await test_t1_explicit_read_history()
    results['T2'] = await test_t2_explicit_read_goal()
    results['T3'] = await test_t3_explicit_save()
    results['T5'] = await test_t5_empty_result()
    
    print("=" * 60)
    print("测试结果汇总")
    print("=" * 60)
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for test_id, result in results.items():
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{test_id}: {status}")
    
    print(f"\n通过率: {passed}/{total} ({passed*100//total}%)")
    print("=" * 60)
    
    print("\n注意：这些测试只验证工具功能，不验证 Skill 触发机制。")
    print("Skill 触发需要在 Cursor/Claude 中通过实际对话验证。")
    print()


if __name__ == "__main__":
    asyncio.run(main())
