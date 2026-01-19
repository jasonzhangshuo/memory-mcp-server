#!/usr/bin/env python3
"""Test 2026-baseline project initialization."""

import asyncio
import json
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from storage.db import init_db
from storage.projects import get_project_by_name, get_project_baseline, get_project_memories
from tools.memory_get_project_context import memory_get_project_context
from models import MemoryGetProjectContextInput


async def test_project_exists():
    """Test if project exists."""
    print("\n[测试] 项目存在性")
    print("-" * 70)
    
    project = await get_project_by_name("2026-baseline")
    if project:
        print(f"✅ 通过: 项目存在")
        print(f"   项目ID: {project['id']}")
        print(f"   名称: {project['name']}")
        print(f"   状态: {project.get('status', 'N/A')}")
        return True
    else:
        print("❌ 失败: 项目不存在")
        return False


async def test_baseline_doc():
    """Test baseline document loading."""
    print("\n[测试] 基准文档加载")
    print("-" * 70)
    
    baseline = await get_project_baseline("2026-baseline")
    if baseline:
        print(f"✅ 通过: 基准文档加载成功")
        print(f"   文档长度: {len(baseline)} 字符")
        if "50岁退休" in baseline:
            print("   ✓ 包含核心目标")
        return True
    else:
        print("❌ 失败: 基准文档未找到")
        return False


async def test_memory_association():
    """Test memory association."""
    print("\n[测试] 记忆关联")
    print("-" * 70)
    
    memories = await get_project_memories("2026-baseline", limit=10)
    if memories:
        print(f"✅ 通过: 找到 {len(memories)} 条关联记忆")
        seed_titles = [
            "基本身份信息",
            "核心目标：50岁退休",
            "行为模式：研究替代到达",
            "三个锚点",
            "止损规则"
        ]
        found_seeds = [m.get('title') for m in memories if m.get('title') in seed_titles]
        print(f"   种子数据: {len(found_seeds)}/{len(seed_titles)}")
        for title in found_seeds:
            print(f"     ✓ {title}")
        return len(found_seeds) >= 5
    else:
        print("❌ 失败: 未找到关联记忆")
        return False


async def test_project_context():
    """Test project context loading."""
    print("\n[测试] 项目上下文加载")
    print("-" * 70)
    
    params = MemoryGetProjectContextInput(
        project="2026-baseline",
        include_baseline=True,
        recent_limit=5
    )
    result = await memory_get_project_context(params)
    data = json.loads(result)
    
    if data.get('status') == 'success':
        print(f"✅ 通过: 项目上下文加载成功")
        print(f"   项目: {data['project']['name']}")
        print(f"   基准文档: {'存在' if data.get('baseline') else '不存在'}")
        print(f"   记忆数: {data.get('memory_count', 0)}")
        return True
    else:
        print(f"❌ 失败: {data.get('message')}")
        return False


async def run_all_tests():
    """Run all baseline initialization tests."""
    print("=" * 70)
    print("2026-baseline 项目初始化测试")
    print("=" * 70)
    
    await init_db()
    
    results = []
    results.append(await test_project_exists())
    results.append(await test_baseline_doc())
    results.append(await test_memory_association())
    results.append(await test_project_context())
    
    print("\n" + "=" * 70)
    print("测试结果汇总")
    print("=" * 70)
    passed = sum(results)
    total = len(results)
    print(f"通过: {passed}/{total} ({passed*100//total if total > 0 else 0}%)")
    
    if passed == total:
        print("\n🎉 所有项目初始化测试通过！")
    else:
        print(f"\n⚠️  {total - passed} 个测试失败")


if __name__ == "__main__":
    asyncio.run(run_all_tests())
