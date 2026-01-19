#!/usr/bin/env python3
"""Phase 1 工具测试脚本"""

import asyncio
import json
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from storage.db import init_db, add_memory
from models import (
    MemoryGetInput,
    MemoryUpdateInput,
    MemoryCompressConversationInput,
    MemoryGetProjectContextInput,
    MemoryListProjectsInput,
    MemoryStatsInput,
)
from tools.memory_get import memory_get
from tools.memory_update import memory_update
from tools.memory_compress_conversation import memory_compress_conversation
from tools.memory_get_project_context import memory_get_project_context
from tools.memory_list_projects import memory_list_projects
from tools.memory_stats import memory_stats
from storage.projects import create_project
import uuid


async def test_memory_get():
    """测试 memory_get"""
    print("\n[测试] memory_get")
    print("-" * 70)
    
    # 先创建一个记忆
    test_id = str(uuid.uuid4())
    await add_memory(
        memory_id=test_id,
        category="test",
        title="测试记忆",
        content="这是一个测试记忆",
        importance=3,
        source_type="manual"
    )
    
    # 测试获取
    params = MemoryGetInput(id=test_id)
    result = await memory_get(params)
    data = json.loads(result)
    
    if data.get('status') == 'success' and data.get('entry'):
        print(f"✅ 通过: 成功获取记忆 {test_id}")
        print(f"   标题: {data['entry'].get('title')}")
        return True
    else:
        print(f"❌ 失败: {data.get('message')}")
        return False


async def test_memory_update():
    """测试 memory_update"""
    print("\n[测试] memory_update")
    print("-" * 70)
    
    # 先创建一个记忆
    test_id = str(uuid.uuid4())
    await add_memory(
        memory_id=test_id,
        category="test",
        title="原始标题",
        content="原始内容",
        importance=3,
        source_type="manual"
    )
    
    # 测试更新
    params = MemoryUpdateInput(
        id=test_id,
        title="更新后的标题",
        content="更新后的内容"
    )
    result = await memory_update(params)
    data = json.loads(result)
    
    if data.get('status') == 'success':
        print(f"✅ 通过: 成功更新记忆 {test_id}")
        print(f"   新标题: {data['entry'].get('title')}")
        return True
    else:
        print(f"❌ 失败: {data.get('message')}")
        return False


async def test_memory_compress_conversation():
    """测试 memory_compress_conversation"""
    print("\n[测试] memory_compress_conversation")
    print("-" * 70)
    
    params = MemoryCompressConversationInput(
        summary="这是一次测试对话的摘要",
        key_decisions=["决定1", "决定2"],
        key_insights=["洞察1"],
        action_items=["行动项1"]
    )
    result = await memory_compress_conversation(params)
    data = json.loads(result)
    
    if data.get('status') == 'success':
        print(f"✅ 通过: 成功压缩保存对话")
        print(f"   记忆ID: {data.get('id')}")
        return True
    else:
        print(f"❌ 失败: {data.get('message')}")
        return False


async def test_memory_get_project_context():
    """测试 memory_get_project_context"""
    print("\n[测试] memory_get_project_context")
    print("-" * 70)
    
    # 先创建一个项目
    project_id = str(uuid.uuid4())
    await create_project(
        project_id=project_id,
        name="测试项目",
        description="这是一个测试项目",
        baseline_doc="# 测试项目基准文档\n\n这是项目的基准文档。",
        status="active"
    )
    
    # 添加一些项目记忆
    await add_memory(
        memory_id=str(uuid.uuid4()),
        category="test",
        title="项目记忆1",
        content="这是项目的第一个记忆",
        project="测试项目",
        importance=3,
        source_type="manual"
    )
    
    # 测试获取项目上下文
    params = MemoryGetProjectContextInput(
        project="测试项目",
        include_baseline=True,
        recent_limit=5
    )
    result = await memory_get_project_context(params)
    data = json.loads(result)
    
    if data.get('status') == 'success':
        print(f"✅ 通过: 成功获取项目上下文")
        print(f"   项目: {data['project']['name']}")
        print(f"   记忆数: {data.get('memory_count', 0)}")
        return True
    else:
        print(f"❌ 失败: {data.get('message')}")
        return False


async def test_memory_list_projects():
    """测试 memory_list_projects"""
    print("\n[测试] memory_list_projects")
    print("-" * 70)
    
    params = MemoryListProjectsInput(status=None)
    result = await memory_list_projects(params)
    data = json.loads(result)
    
    if data.get('status') == 'success':
        print(f"✅ 通过: 成功列出项目")
        print(f"   项目数: {data.get('count', 0)}")
        return True
    else:
        print(f"❌ 失败: {data.get('message')}")
        return False


async def test_memory_stats():
    """测试 memory_stats"""
    print("\n[测试] memory_stats")
    print("-" * 70)
    
    params = MemoryStatsInput(project=None)
    result = await memory_stats(params)
    data = json.loads(result)
    
    if data.get('status') == 'success':
        stats = data.get('stats', {})
        print(f"✅ 通过: 成功获取统计信息")
        print(f"   总记忆数: {stats.get('total', 0)}")
        print(f"   分类统计: {len(stats.get('by_category', {}))} 个类别")
        return True
    else:
        print(f"❌ 失败: {data.get('message')}")
        return False


async def run_all_tests():
    """运行所有测试"""
    print("=" * 70)
    print("Phase 1 工具测试")
    print("=" * 70)
    
    await init_db()
    
    results = []
    results.append(await test_memory_get())
    results.append(await test_memory_update())
    results.append(await test_memory_compress_conversation())
    results.append(await test_memory_get_project_context())
    results.append(await test_memory_list_projects())
    results.append(await test_memory_stats())
    
    print("\n" + "=" * 70)
    print("测试结果汇总")
    print("=" * 70)
    passed = sum(results)
    total = len(results)
    print(f"通过: {passed}/{total} ({passed*100//total if total > 0 else 0}%)")
    
    if passed == total:
        print("\n🎉 所有测试通过！")
    else:
        print(f"\n⚠️  {total - passed} 个测试失败")


if __name__ == "__main__":
    asyncio.run(run_all_tests())
