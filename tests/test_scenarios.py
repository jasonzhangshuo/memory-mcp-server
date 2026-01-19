"""Scenario tests.

真实使用场景测试。
"""

import asyncio
import json
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from storage.db import init_db
from tools.memory_add import memory_add
from tools.memory_search import memory_search
from tools.memory_suggest_category import memory_suggest_category
from tools.memory_check_conflicts import memory_check_conflicts
from models import (
    MemoryAddInput,
    MemorySearchInput,
    MemorySuggestCategoryInput,
    MemoryCheckConflictsInput
)


async def test_daily_usage_scenario():
    """测试日常使用场景"""
    print("测试：日常使用场景...")
    
    # 模拟一天的使用
    scenarios = [
        {
            "desc": "添加个人洞察",
            "params": MemoryAddInput(
                category="insight",
                title="今天的觉察",
                content="我发现自己在使用AI工具时又陷入了研究替代到达的模式",
                tags=["觉察", "模式"]
            )
        },
        {
            "desc": "添加知识库条目",
            "params": MemoryAddInput(
                category="knowledge",
                title="八步骤学习笔记",
                content="## 摘要\n八步骤是修学方法论\n## 要点\n- 闻思法义\n- 理解内涵\n## 来源\n《修学要领》",
                project="knowledge-base/佛法",
                tags=["八步骤", "修行方法"]
            )
        },
        {
            "desc": "使用智能判定（auto）",
            "params": MemoryAddInput(
                category="auto",
                title="我决定每天冥想",
                content="我决定从今天开始，每天冥想10分钟"
            )
        },
    ]
    
    for scenario in scenarios:
        result_str = await memory_add(scenario["params"])
        result = json.loads(result_str)
        assert result["status"] == "success", f"{scenario['desc']} 失败"
        print(f"  ✓ {scenario['desc']}")
    
    # 搜索验证
    search_params = MemorySearchInput(query="觉察", limit=5)
    search_result_str = await memory_search(search_params)
    search_result = json.loads(search_result_str)
    assert search_result["count"] > 0, "搜索失败"
    print("  ✓ 搜索验证成功")
    
    return True


async def test_knowledge_base_accumulation():
    """测试知识库积累场景"""
    print("测试：知识库积累场景...")
    
    # 添加50条知识库条目
    for i in range(10):  # 测试时减少到10条
        add_params = MemoryAddInput(
            category="knowledge",
            title=f"知识条目 {i+1}",
            content=f"这是第 {i+1} 条知识库条目，用于测试知识库积累",
            project="knowledge-base",
            tags=[f"主题{i%5}", "知识库"]
        )
        result_str = await memory_add(add_params)
        result = json.loads(result_str)
        assert result["status"] == "success", f"添加第 {i+1} 条失败"
    
    print(f"  ✓ 成功添加 10 条知识库条目")
    
    # 验证检索
    search_params = MemorySearchInput(
        query="",
        category="knowledge",
        project="knowledge-base",
        limit=20
    )
    search_result_str = await memory_search(search_params)
    search_result = json.loads(search_result_str)
    assert search_result["count"] >= 10, "检索数量不足"
    print(f"  ✓ 检索验证成功，找到 {search_result['count']} 条")
    
    return True


async def test_conflict_handling():
    """测试冲突处理流程"""
    print("测试：冲突处理流程...")
    
    # 添加第一条
    add1 = MemoryAddInput(
        category="decision",
        title="决定每天运动",
        content="我决定每天运动30分钟"
    )
    result1_str = await memory_add(add1)
    result1 = json.loads(result1_str)
    id1 = result1["id"]
    
    # 添加可能冲突的第二条
    add2 = MemoryAddInput(
        category="decision",
        title="决定每天运动1小时",
        content="我决定每天运动1小时"
    )
    result2_str = await memory_add(add2)
    result2 = json.loads(result2_str)
    id2 = result2["id"]
    
    # 检测冲突
    check_params = MemoryCheckConflictsInput(
        new_entry_id=id2,
        check_type=["contradict"]
    )
    conflict_result_str = await memory_check_conflicts(check_params)
    conflict_result = json.loads(conflict_result_str)
    
    assert conflict_result["status"] == "success", "冲突检测失败"
    print(f"  ✓ 冲突检测完成，发现 {conflict_result.get('count', 0)} 个冲突")
    
    return True


async def test_smart_classification_scenarios():
    """测试智能判定场景"""
    print("测试：智能判定场景...")
    
    test_cases = [
        {
            "title": "我发现一个规律",
            "content": "我发现自己在使用工具时总是陷入研究循环",
            "expected_confidence": 0.8
        },
        {
            "title": "这篇文章很好",
            "content": "这篇文章讲八步骤很清晰，来源：https://example.com",
            "expected_confidence": 0.8
        },
    ]
    
    for case in test_cases:
        params = MemorySuggestCategoryInput(
            title=case["title"],
            content=case["content"]
        )
        result_str = await memory_suggest_category(params)
        result = json.loads(result_str)
        
        assert result["status"] == "success", "智能判定失败"
        suggestion = result.get("suggestion", {})
        confidence = suggestion.get("confidence", 0)
        assert confidence >= case["expected_confidence"], f"置信度不足：{confidence}"
        print(f"  ✓ '{case['title']}' 判定成功（置信度 {confidence}）")
    
    return True


async def run_all_tests():
    """运行所有场景测试"""
    print("=" * 60)
    print("场景测试")
    print("=" * 60)
    
    await init_db()
    
    tests = [
        ("日常使用场景", test_daily_usage_scenario),
        ("知识库积累", test_knowledge_base_accumulation),
        ("冲突处理流程", test_conflict_handling),
        ("智能判定场景", test_smart_classification_scenarios),
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        try:
            print(f"\n[{test_name}]")
            success = await test_func()
            if success:
                passed += 1
            else:
                failed += 1
        except Exception as e:
            failed += 1
            print(f"  ✗ {test_name} 失败: {str(e)}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "=" * 60)
    print(f"测试结果：通过 {passed}/{len(tests)}，失败 {failed}/{len(tests)}")
    print("=" * 60)
    
    return failed == 0


if __name__ == "__main__":
    success = asyncio.run(run_all_tests())
    sys.exit(0 if success else 1)
